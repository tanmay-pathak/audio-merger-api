import os
import tempfile
import uuid
import logging
from typing import List
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl
import httpx
from pydub import AudioSegment
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager

# Configure logging with less verbose format
logging.basicConfig(
    level=logging.INFO, 
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Create temp directory for output files
TEMP_DIR = tempfile.mkdtemp()
logger.info(f"Created temp dir: {TEMP_DIR}")

# Load environment variables
load_dotenv()

# Initialize HTTP client
http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Cleanup on shutdown
    await http_client.aclose()
    try:
        import shutil
        shutil.rmtree(TEMP_DIR)
        logger.info(f"Cleaned up temp dir: {TEMP_DIR}")
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")

app = FastAPI(title="Audio Merger API", lifespan=lifespan)

# Configure CORS with specific origins if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable must be set")
api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

class AudioURLs(BaseModel):
    urls: List[HttpUrl]

async def download_audio(url: str) -> str | None:
    """Download audio file from URL and save to temporary file."""
    try:
        logger.info(f"Downloading: {url}")
        headers = {"User-Agent": "AudioMergerAPI/1.0", "Accept": "audio/*,*/*"}
        
        async with http_client.stream('GET', str(url), headers=headers) as response:
            if not any(
                audio_type in response.headers.get("content-type", "").lower()
                for audio_type in ["audio/", "application/octet-stream"]
            ):
                logger.warning(f"Invalid content type: {response.headers.get('content-type')}")
                return None
            
            response.raise_for_status()
            
            # Stream to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            async for chunk in response.aiter_bytes(chunk_size=8192):
                temp_file.write(chunk)
            temp_file.close()
            
            if os.path.getsize(temp_file.name) == 0:
                os.unlink(temp_file.name)
                return None
                
            return temp_file.name
            
    except httpx.HTTPError as e:
        logger.warning(f"HTTP error for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.warning(f"Error for {url}: {str(e)}")
        return None

@app.post("/merge-audio/")
async def merge_audio(audio_urls: AudioURLs, api_key: str = Depends(get_api_key)):
    """Merge multiple audio files into one."""
    logger.info(f"Processing {len(audio_urls.urls)} files")

    if not audio_urls.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    temp_files = []
    output_file = None
    
    try:
        # Download all audio files concurrently
        download_tasks = [download_audio(url) for url in audio_urls.urls]
        temp_files = [f for f in await asyncio.gather(*download_tasks) if f]
        
        if not temp_files:
            raise HTTPException(
                status_code=400,
                detail="No files could be downloaded successfully"
            )
        
        # Process audio files in chunks
        combined = AudioSegment.empty()
        successful_merges = 0
        
        for temp_file in temp_files:
            try:
                # Load and process each audio file
                audio = AudioSegment.from_file(temp_file)
                if len(audio) == 0:
                    continue
                    
                combined += audio
                successful_merges += 1
                
                # Clear memory after processing each file
                del audio
                
            except Exception as e:
                logger.warning(f"Processing error: {str(e)}")
                continue

        if successful_merges == 0:
            raise HTTPException(
                status_code=400,
                detail="No audio files could be processed"
            )

        # Export merged file
        output_filename = f"merged_{uuid.uuid4()}.mp3"
        output_file = os.path.join(TEMP_DIR, output_filename)
        combined.export(output_file, format="mp3")
        
        # Clear memory
        del combined

        # Stream the response
        def iterfile():
            with open(output_file, 'rb') as f:
                while chunk := f.read(8192):
                    yield chunk
            # Cleanup after streaming
            os.unlink(output_file)

        return StreamingResponse(
            iterfile(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=merged.mp3",
                "X-Total-Files": str(len(audio_urls.urls)),
                "X-Successful-Merges": str(successful_merges)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Merge error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during merge")

    finally:
        # Cleanup temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")
