# Audio Merger API

A simple FastAPI application that merges multiple audio files from URLs into a single audio file.

## Features

- Merge multiple audio files from URLs
- API Key authentication
- Supports various audio formats (automatically converted to MP3)
- Efficient temporary file handling
- CORS support

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables by creating a `.env` file:

```bash
API_KEY=your-secret-api-key
```

3. Run the server:

```bash
uvicorn main:app --reload
```

## API Usage

### Merge Audio Files

**Endpoint:** `POST /merge-audio/`

**Headers:**

- `X-API-Key`: Your API key

**Request Body:**

```json
{
    "urls": [
        "https://example.com/audio1.mp3",
        "https://example.com/audio2.mp3"
    ]
}
```

**Response:**

- Content-Type: `audio/mpeg`
- The merged audio file will be returned as a downloadable MP3 file

## Error Handling

The API includes comprehensive error handling for:

- Invalid URLs
- Failed downloads
- Invalid API keys
- Processing errors

## Dependencies

- FastAPI
- uvicorn
- python-multipart
- pydantic
- python-dotenv
- requests
- pydub

## Notes

- Make sure to replace the default API key with a secure one in production
- The API automatically cleans up temporary files after processing
- Large files may take longer to process
