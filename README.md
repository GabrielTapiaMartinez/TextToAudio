# Reader Companion

**Reader Companion** is a local, privacy-first web application designed for reading along with PDF documents and text. It cleans up multi-column layouts, runs OCR on scanned pages when necessary, and generates natural-sounding speech on-the-fly using the local **Kokoro-82M** Text-to-Speech (TTS) model—completely offline with zero cloud API dependencies.

---

## Features

- **Smart PDF Extraction & Layout Analysis**
  - **Multi-column sorting**: Reconstructs reading order across multi-column layouts (e.g., academic papers, research articles, book spreads).
  - **Header & footer removal**: Strips running page headers and footers automatically.
  - **Artifact & footnote filtering**: Filters out superscripts, stray OCR artifacts, and small text based on font size distribution.
  - **De-hyphenation**: Repairs words broken across line wraps.
- **Automatic OCR Fallback**
  - Scans image-only or rasterized PDF pages using **Tesseract OCR** via PyMuPDF if no digital text layer is detected.
- **Direct Text Input**
  - Switch to "Paste Text" mode to paste and listen to arbitrary articles, essays, or notes.
- **Local Neural Text-to-Speech (Kokoro-82M)**
  - Runs locally via `kokoro-onnx` with optimized 4-thread CPU execution.
  - **Server-Side Disk Audio Cache**: Content-addressed cache (`.cache/audio/`) with SHA-256 hashing and automatic TTL/LRU eviction (24h / 250 MB cap). Replaying sentences is instantaneous (**< 1ms**, 0% CPU).
  - **Predictive First-Sentence Pre-Generation**: Automatically pre-synthesizes the first sentence on document/text submission so playback begins with zero wait.
  - **Non-blocking Asynchronous Execution**: Offloaded to worker threads via `asyncio.to_thread`—FastAPI's event loop never freezes.
  - Multiple English voices included (`af`, `am_adam`, `af_bella`, `am_michael`).
- **Interactive Distraction-Free UI**
  - **Sentence-Level Clicking & Highlighting**: Paragraphs are broken into interactive sentence spans. Click any sentence to jump playback directly there.
  - **Transparent Live Communication**: Pulsing animated glow on sentences undergoing synthesis, active reading glow with smooth auto-scrolling, and real-time status & progress pills in the player bar.
  - **Continuous playback & auto-advance**: Automatically advances through sentences and moves to the next paragraph.
  - **Intelligent preloading & instant abort**: Preloads upcoming sentences and immediately aborts stale requests via `AbortController` when jumping.
  - **Keyboard Shortcuts**: `Space` (Play/Pause), `ArrowRight` (Next Sentence), `ArrowLeft` (Previous Sentence/Restart).
  - **Playback controls**: Play/Pause, Stop, Previous/Next navigation, and adjustable playback speeds (`0.75x`, `1.0x`, `1.25x`, `1.5x`).
  - **Modern dark mode**: Clean typography and a floating glassmorphic player bar.

---

## Architecture & Tech Stack

| Layer | Component | Description |
|---|---|---|
| **Frontend** | Vanilla HTML5 / CSS3 / ES6 | Interactive sentence spans, AbortController preloading, keyboard shortcuts, and glassmorphic player |
| **Backend** | FastAPI / Uvicorn | Async Python API with lifespan warmup, non-blocking threadpool, and background pre-generation |
| **Caching Layer** | SHA-256 Disk & Memory Cache | Content-addressed `.cache/audio/` with automatic TTL/LRU eviction |
| **Document Processing** | PyMuPDF (`fitz`) & Tesseract OCR | PDF block extraction, column ordering, de-hyphenation, and OCR fallback |
| **TTS Engine** | `kokoro-onnx` + `soundfile` | 4-thread optimized ONNX runtime speech synthesis returning 24kHz WAV audio |

---

## Directory Structure

```text
TextToAudio/
├── main.py                  # FastAPI application routes (/api/upload, /api/text, /api/audio)
├── parser.py                # PDF layout parsing, OCR handling, text cleaning, sentence segmentation
├── tts_engine.py            # Kokoro TTS model loader and WAV audio synthesis
├── run.sh                   # All-in-one setup & launch script (Homebrew, venv, pip, models, uvicorn)
├── static/
│   └── index.html           # Single-page web application (reader UI, player bar, audio preloader)
├── models/
│   ├── kokoro-v0_19.onnx    # Kokoro-82M ONNX model weights
│   ├── voices.bin           # Binary voice vectors for Kokoro TTS
│   └── voices.json          # Voice metadata definitions
├── test_generation.py       # Automated test suite: generates synthetic 2-col PDF and verifies TTS
├── test_ocr.py              # Diagnostic script to test OCR extraction on a PDF
├── inspect_ocr.py           # Helper script to inspect raw OCR blocks on specific pages
├── test_media/              # Sample PDFs used for testing
└── README.md                # Project documentation
```

---

## Prerequisites

- **Operating System**: macOS (Apple Silicon or Intel) or Linux
- **Python**: Python 3.9+
- **System Packages**:
  - `espeak-ng` (required by Kokoro phonemizer)
  - `tesseract` & `tesseract-lang` (for OCR fallback)
  - `ffmpeg` (for audio processing)

On macOS with Homebrew, these can be installed with:
```bash
brew install espeak-ng tesseract tesseract-lang ffmpeg
```

---

## Quick Start

The included `run.sh` script automates system dependency checks, virtual environment setup, package installation, model downloads, and launches the server.

```bash
chmod +x run.sh
./run.sh
```

Once running, open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## Manual Installation & Setup

If you prefer to configure the environment step-by-step:

1. **Clone or navigate to the repository:**
   ```bash
   cd /path/to/TextToAudio
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install fastapi "uvicorn[standard]" pymupdf kokoro-onnx soundfile numpy python-multipart reportlab
   ```

4. **Download Kokoro-82M model files:**
   ```bash
   mkdir -p models
   curl -L -o models/kokoro-v0_19.onnx "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
   curl -L -o models/voices.bin "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.bin"
   ```

5. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

---

## API Reference

### 1. `POST /api/upload`
Uploads and parses a PDF document.

- **Request**: Multipart form data with `file` (PDF binary).
- **Response**: Array of parsed paragraphs:
  ```json
  [
    {
      "id": 0,
      "text": "Full cleaned paragraph text.",
      "sentences": ["Sentence 1.", "Sentence 2."],
      "page": 1
    }
  ]
  ```

### 2. `POST /api/text`
Parses raw plain text into paragraphs and sentences.

- **Request Body**:
  ```json
  { "text": "Raw pasted text..." }
  ```
- **Response**: Array of parsed `Paragraph` objects.

### 3. `GET /api/audio`
Generates and streams audio for a given paragraph or individual sentence.

- **Query Parameters**:
  - `id` (int, required): Paragraph ID.
  - `voice` (str, default: `"af"`): Voice identifier (e.g., `af`, `am_adam`, `af_bella`, `am_michael`).
  - `lang` (str, default: `"en-us"`): Language code.
  - `sentence_idx` (int, optional, default: `-1`): Zero-based sentence index within the paragraph. When `-1`, synthesizes the whole paragraph.
- **Response**: `audio/wav` audio stream.

---

## Testing & Diagnostics

### Run Pipeline Integration Test
Generates an in-memory two-column PDF with ReportLab, validates column sorting, tests hyphenation removal, and verifies Kokoro TTS audio generation:
```bash
./venv/bin/python test_generation.py
```

### Test OCR on a PDF
```bash
./venv/bin/python test_ocr.py "path/to/scanned_document.pdf"
```

### Inspect Raw OCR Output
```bash
./venv/bin/python inspect_ocr.py
```

---

## License & Acknowledgements

- **Kokoro-82M**: Model weights and architecture created by [hexgrad](https://huggingface.co/hexgrad/Kokoro-82M), ONNX runtime wrapper by [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx).
- **PyMuPDF**: PDF text extraction and OCR engine integration via [Artifex Software](https://pymupdf.readthedocs.io/).
