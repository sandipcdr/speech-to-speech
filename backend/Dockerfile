FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# ffmpeg for audio processing
# espeak-ng for Piper TTS fallback or dependency
# curl for downloading models if needed
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak-ng \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Command to run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
