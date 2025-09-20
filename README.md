# Audio Merger API

A FastAPI application that efficiently merges multiple audio files from URLs into a single audio file, optimized for memory usage and performance.

## Features

- Asynchronous processing of audio files
- Memory-efficient streaming downloads and responses
- API Key authentication
- Supports various audio formats (automatically converted to MP3)
- Configurable MP3 compression (bitrate, quality, sample rate, channels)
- Efficient temporary file handling
- CORS support
- Concurrent downloads with sequential processing

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
uvicorn main:app --workers 1 --limit-concurrency 50
```

## System Requirements

- Minimum Memory: 512MB
- Recommended Memory: 1GB
- Maximum Memory: 2GB (for heavy workloads)

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
    ],
    "compression": {
        "bitrate_kbps": 96,
        "quality": 5,
        "sample_rate_hz": 22050,
        "channels": 1
    }
}
```

**Response:**

- Content-Type: `audio/mpeg`
- The merged audio file will be streamed as a downloadable MP3 file
- Headers include:
  - `X-Total-Files`: Total number of input files
  - `X-Successful-Merges`: Number of successfully merged files
  - `X-Output-Bitrate`: Bitrate applied to the merged output

### Compression Options

All compression fields are optional. If omitted, the API defaults to audiobook-friendly settings:

- Bitrate: `64 kbps`
- FFmpeg quality: `6`
- Sample rate: `22050 Hz`
- Channels: mono (`1`)

| Field | Type | Description |
| --- | --- | --- |
| `bitrate_kbps` | integer | Target bitrate for the output file in kbps (e.g. `96`). |
| `quality` | integer | FFmpeg VBR quality (`0` = best, `9` = smallest). |
| `sample_rate_hz` | integer | Resample the merged audio (e.g. `44100` for higher fidelity). |
| `channels` | integer | Force mono (`1`) or stereo (`2`) output. |

## Error Handling

The API includes comprehensive error handling for:

- Invalid URLs
- Failed downloads
- Invalid API keys
- Processing errors
- Empty or invalid audio files

## Dependencies

- FastAPI
- uvicorn[standard]
- pydantic[core]
- python-dotenv
- httpx
- pydub

## Performance Notes

- Uses streaming for both downloads and responses
- Processes files sequentially to optimize memory usage
- Downloads happen concurrently for better performance
- Automatically cleans up temporary files
- Memory usage is optimized for handling large files
- Uses chunked processing (8KB chunks)

## Production Deployment

For production deployment, consider setting appropriate memory limits:

### Docker

```bash
docker run -m "1g" --memory-swap "1g" your-image-name
```

### Kubernetes

```yaml
resources:
  limits:
    memory: "1Gi"
  requests:
    memory: "512Mi"
```

## Security Notes

- Replace the default API key with a secure one in production
- All temporary files are automatically cleaned up
- CORS can be configured for specific origins in production
