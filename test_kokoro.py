import asyncio
from kokoro_onnx import Kokoro
import json
import soundfile as sf

async def main():
    try:
        kokoro = Kokoro("models/kokoro-v0_19.onnx", "models/voices.json")
        samples, sample_rate = kokoro.create("Hello world", voice="af_heart", speed=1.0, lang="en-us")
        print(f"Generated {len(samples)} samples at {sample_rate}Hz")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
