#!/bin/bash
set -e

echo "Starting setup for reader-companion..."

# Check and install espeak-ng if not installed
if ! command -v espeak-ng &> /dev/null || ! command -v tesseract &> /dev/null
then
    echo "Dependencies could not be found, attempting to install via Homebrew..."
    if command -v brew &> /dev/null
    then
        brew install espeak-ng tesseract tesseract-lang
    else
        echo "Homebrew is not installed. Please install espeak-ng and tesseract manually."
        exit 1
    fi
fi

# Check and install ffmpeg if not installed
if ! command -v ffmpeg &> /dev/null
then
    echo "ffmpeg could not be found, attempting to install via Homebrew..."
    if command -v brew &> /dev/null
    then
        brew install ffmpeg
    else
        echo "Homebrew is not installed. Please install ffmpeg manually."
        exit 1
    fi
fi

# Set up Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install fastapi "uvicorn[standard]" pymupdf kokoro-onnx soundfile numpy python-multipart reportlab httpx

# Create models directory
mkdir -p models

# Download Kokoro-82M model assets
if [ ! -f "models/kokoro-v0_19.onnx" ]; then
    echo "Downloading kokoro-v0_19.onnx..."
    curl -L -o models/kokoro-v0_19.onnx "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
fi

if [ ! -f "models/voices.bin" ]; then
    echo "Downloading voices.bin..."
    curl -L -o models/voices.bin "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.bin"
fi

# Create static directory
mkdir -p static

echo "Setup complete!"
echo "Starting the FastAPI server..."
echo "The application will be available at http://127.0.0.1:8000"
echo "Setup complete!"
uvicorn main:app --host 127.0.0.1 --port 8000
