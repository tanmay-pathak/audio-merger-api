FROM python:3.11-slim-bullseye as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bullseye

# Install only ffmpeg without extra dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Start the application with reduced worker count and limited memory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--limit-concurrency", "50"]
