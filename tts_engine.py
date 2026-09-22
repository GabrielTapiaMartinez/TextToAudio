import os
import io
import time
import hashlib
import asyncio
import soundfile as sf
import onnxruntime as rt
from kokoro_onnx import Kokoro
from typing import Tuple, Dict

# Global reference to avoid reloading
_model = None

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache", "audio")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_key(text: str, voice: str, lang: str) -> str:
    normalized = f"{voice.strip()}_{lang.strip()}_{text.strip()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def get_cached_audio_path(text: str, voice: str, lang: str) -> str:
    key = get_cache_key(text, voice, lang)
    return os.path.join(CACHE_DIR, f"{key}.wav")

def get_cache_stats() -> Dict:
    total_size = 0
    count = 0
    if os.path.exists(CACHE_DIR):
        for entry in os.scandir(CACHE_DIR):
            if entry.is_file() and entry.name.endswith(".wav"):
                count += 1
                total_size += entry.stat().st_size
    return {
        "file_count": count,
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }

def cleanup_cache(max_age_seconds: int = 86400, max_size_mb: int = 250) -> int:
    """
    Cleans up cached audio files older than max_age_seconds or when total size exceeds max_size_mb.
    Returns the number of files deleted.
    """
    if not os.path.exists(CACHE_DIR):
        return 0

    now = time.time()
    deleted_count = 0
    files = []

    for entry in os.scandir(CACHE_DIR):
        if entry.is_file() and entry.name.endswith(".wav"):
            stat = entry.stat()
            files.append({
                "path": entry.path,
                "mtime": stat.st_mtime,
                "size": stat.st_size
            })

    # 1. Prune expired files
    surviving_files = []
    total_size = 0
    for f in files:
        if now - f["mtime"] > max_age_seconds:
            try:
                os.remove(f["path"])
                deleted_count += 1
            except OSError:
                pass
        else:
            surviving_files.append(f)
            total_size += f["size"]

    # 2. Prune oldest files if total size exceeds max_size_mb
    max_bytes = max_size_mb * 1024 * 1024
    if total_size > max_bytes:
        # Sort surviving files by mtime ascending (oldest first)
        surviving_files.sort(key=lambda x: x["mtime"])
        for f in surviving_files:
            if total_size <= max_bytes:
                break
            try:
                os.remove(f["path"])
                deleted_count += 1
                total_size -= f["size"]
            except OSError:
                pass

    return deleted_count

def get_model() -> Kokoro:
    global _model
    if _model is None:
        model_path = os.path.join("models", "kokoro-v0_19.onnx")
        voices_path = os.path.join("models", "voices.bin")
        if not os.path.exists(model_path) or not os.path.exists(voices_path):
            raise Exception("Kokoro model files not found in models/ directory. Run setup to download them.")
        
        # Configure ONNX Runtime session for optimal Apple Silicon / CPU throughput
        opts = rt.SessionOptions()
        opts.intra_op_num_threads = 4  # Sweet spot on Apple Silicon: avoids thread contention
        opts.inter_op_num_threads = 1
        opts.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        session = rt.InferenceSession(model_path, sess_options=opts, providers=["CPUExecutionProvider"])
        _model = Kokoro.from_session(session, voices_path)
    return _model

def warmup() -> None:
    """Preloads the model and runs a lightweight warmup synthesis to eliminate cold start latency."""
    try:
        model = get_model()
        # Fast dummy inference
        model.create("warmup", voice="af", speed=1.0, lang="en-us")
        cleanup_cache()
    except Exception as e:
        print(f"TTS Warmup failed: {e}")

def generate_audio(text: str, voice: str = "af", lang: str = "en-us", return_cached_flag: bool = False):
    """
    Generates WAV audio bytes for the given text.
    If return_cached_flag is True, returns (wav_bytes, was_cached).
    Otherwise returns wav_bytes directly.
    """
    text_clean = text.strip()
    if not text_clean:
        return (b"", False) if return_cached_flag else b""

    cache_path = get_cached_audio_path(text_clean, voice, lang)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                data = f.read()
                return (data, True) if return_cached_flag else data
        except OSError:
            pass

    # Cache miss: Synthesize audio
    model = get_model()
    try:
        samples, sample_rate = model.create(text_clean, voice=voice, speed=1.0, lang=lang)
    except Exception as e:
        print(f"TTS Error with voice={voice}, lang={lang}: {e}")
        # Fallback to standard af voice
        samples, sample_rate = model.create(text_clean, voice="af", speed=1.0, lang="en-us")

    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate, format="WAV")
    wav_bytes = buffer.getvalue()

    # Save to disk cache atomically
    tmp_path = cache_path + f".tmp.{os.getpid()}"
    try:
        with open(tmp_path, "wb") as f:
            f.write(wav_bytes)
        os.replace(tmp_path, cache_path)
    except OSError:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    return (wav_bytes, False) if return_cached_flag else wav_bytes

async def async_generate_audio(text: str, voice: str = "af", lang: str = "en-us") -> Tuple[bytes, bool]:
    """
    Non-blocking async wrapper that offloads CPU-bound neural network inference
    to an asynchronous worker thread pool so FastAPI's event loop never freezes.
    Always returns (wav_bytes, was_cached).
    """
    return await asyncio.to_thread(generate_audio, text, voice, lang, True)
