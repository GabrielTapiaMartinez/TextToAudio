# 🎧 Reader Companion

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![ONNX Runtime](https://img.shields.io/badge/ONNX_Runtime-1.30+-005CED?logo=onnx&logoColor=white)](https://onnxruntime.ai)
[![TTS Model](https://img.shields.io/badge/TTS-Kokoro--82M-8A2BE2)](https://huggingface.co/hexgrad/Kokoro-82M)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A high-performance, distraction-free PDF and text reader with on-device neural Text-to-Speech (TTS). It cleans complex multi-column documents, applies OCR when needed, and streams natural speech with sentence-level read-along playback—**100% offline and private**.

---

## ⚡ Highlights

- **🎙️ Local Neural TTS**: Powered by the 82M-parameter Kokoro diffusion-style model running locally on CPU via ONNX Runtime. Zero cloud APIs, telemetry, or recurring fees.
- **⚡ Sub-Millisecond Caching**: Content-addressed SHA-256 disk cache serves previously synthesized sentences in `< 1ms` with zero CPU load.
- **📄 Smart Document Cleaning**: Reconstructs reading order across multi-column layouts, removes running headers/footers, strips footnote artifacts, and de-hyphenates wrapped lines.
- **🔍 Automated OCR Fallback**: Integrated Tesseract OCR via PyMuPDF detects and extracts rasterized or scanned pages transparently.
- **🎯 Sentence-Level Read-Along**: Click any sentence to begin reading immediately. Features active sentence highlights, smooth auto-scrolling, and gapless background preloading.
- **🎨 Glassmorphic Dark UI**: Modern dark theme with floating player controls, live synthesis status indicators, and keyboard shortcuts.

---

## 🚀 Quick Start

Ensure you have [Homebrew](https://brew.sh) installed (macOS), then run:

```bash
git clone https://github.com/GabrielTapiaMartinez/TextToAudio.git
cd TextToAudio
chmod +x run.sh
./run.sh
```

`run.sh` automatically verifies system tools (`espeak-ng`, `tesseract`, `ffmpeg`), creates a Python virtual environment, installs dependencies, downloads the Kokoro model weights, and boots the server at:

👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| <kbd>Space</kbd> | Play / Pause |
| <kbd>→</kbd> | Jump to Next Sentence |
| <kbd>←</kbd> | Jump to Previous Sentence / Restart Sentence |

---

## 📂 Project Structure

```text
TextToAudio/
├── main.py              # FastAPI server, background workers, and session management
├── parser.py            # Multi-column layout reconstruction, cleaning, and OCR
├── tts_engine.py        # Kokoro ONNX loader, 4-thread CPU tuning, and disk cache
├── run.sh               # One-click installation and launch script
├── static/
│   └── index.html       # Single-page web app with interactive sentence spans
├── docs/                # Comprehensive technical documentation
│   ├── ARCHITECTURE.md  # Deep dive: layout parsing, thread scaling, cache design
│   ├── API.md           # Full REST API specification and payload examples
│   └── DEVELOPMENT.md   # Diagnostic scripts, manual setup, and test utilities
└── test_generation.py   # End-to-end integration and audio synthesis test suite
```

---

## 📚 Documentation

For in-depth technical details, architectural decisions, and API references:

- 📘 **[Architecture & Engineering Deep Dive](docs/ARCHITECTURE.md)**: Column clustering algorithms, ONNX thread optimization, and cache eviction policies.
- 📡 **[REST API Reference](docs/API.md)**: Complete endpoint schemas for `/api/upload`, `/api/text`, `/api/audio`, and `/api/status`.
- 🛠️ **[Development & Testing Guide](docs/DEVELOPMENT.md)**: Manual environment configuration, OCR diagnostic tools, and test suites.

---

## ⚖️ License & Acknowledgements

- **Kokoro-82M**: Model weights and architecture created by [hexgrad](https://huggingface.co/hexgrad/Kokoro-82M), ONNX runtime wrapper by [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx).
- **PyMuPDF**: Document layout and OCR engine integration via [Artifex Software](https://pymupdf.readthedocs.io/).
- Distributed under the [MIT License](LICENSE).
