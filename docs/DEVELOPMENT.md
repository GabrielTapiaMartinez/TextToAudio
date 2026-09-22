# Development & Testing Guide

This guide covers testing utilities, diagnostic scripts, and manual setup for Reader Companion developers.

---

## Testing Tools

### 1. Integration Pipeline Test (`test_generation.py`)
Generates an in-memory two-column PDF using ReportLab, parses the layout, verifies column reading order, tests de-hyphenation, and validates Kokoro audio synthesis:
```bash
./venv/bin/python test_generation.py
```

### 2. OCR Diagnostics (`test_ocr.py`)
Inspects scanned PDFs without a digital text layer to verify Tesseract extraction:
```bash
./venv/bin/python test_ocr.py "path/to/document.pdf"
```

### 3. Raw Block Inspector (`inspect_ocr.py`)
Outputs raw OCR blocks and spatial coordinates for debugging complex document layouts:
```bash
./venv/bin/python inspect_ocr.py
```

---

## Environment Configuration

| Variable | Description | Default |
|---|---|---|
| `TESSDATA_PREFIX` | Directory containing Tesseract language data | `/opt/homebrew/share/tessdata` |
| `ONNX_PROVIDER` | Execution provider override for ONNX Runtime | `CPUExecutionProvider` |

---

## Manual Environment Setup

1. **System Dependencies** (macOS):
   ```bash
   brew install espeak-ng tesseract tesseract-lang ffmpeg
   ```

2. **Python Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt # or install via run.sh
   ```

3. **Download Kokoro Model Weights**:
   ```bash
   mkdir -p models
   curl -L -o models/kokoro-v0_19.onnx "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
   curl -L -o models/voices.bin "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.bin"
   ```
