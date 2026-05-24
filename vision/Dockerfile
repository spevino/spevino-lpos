# Spevino LP-OS - Vision Pipeline
# YOLOv8 + OpenCV detection engine
FROM python:3.11-slim

WORKDIR /app

# Install system deps for OpenCV and video processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Default command - run as daemon listening for frame input
CMD ["python", "-m", "uvicorn", "pipeline:app", "--host", "0.0.0.0", "--port", "8001"]