from fastapi import FastAPI, File, UploadFile, Query, HTTPException, BackgroundTasks, Response
from fastapi.responses import Response as RawResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
import asyncio
import uuid
import os

from parser import parse_pdf, parse_raw_text
from tts_engine import async_generate_audio, warmup, get_cache_stats, cleanup_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Asynchronously warmup model weights and clear stale cache on startup
    asyncio.create_task(asyncio.to_thread(warmup))
    yield

app = FastAPI(title="Reader Companion", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for paragraphs and active document session
current_doc_id: str = ""
current_paragraphs: Dict[int, dict] = {}

class Paragraph(BaseModel):
    id: int
    text: str
    sentences: List[str]
    page: int

class TextPayload(BaseModel):
    text: str

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/api/status")
async def get_status():
    return {
        "status": "ready",
        "doc_id": current_doc_id,
        "cache": get_cache_stats(),
        "paragraphs_count": len(current_paragraphs)
    }

@app.post("/api/upload", response_model=List[Paragraph])
async def upload_pdf(response: Response, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    global current_paragraphs, current_doc_id
    try:
        content = await file.read()
        paragraphs = parse_pdf(content)
        
        # Generate new unique document ID to prevent cross-document cache collision
        current_doc_id = str(uuid.uuid4())[:8]
        response.headers["X-Doc-Id"] = current_doc_id
        
        # Replace active document paragraphs
        current_paragraphs = {p['id']: p for p in paragraphs}
        
        # Instantly pre-synthesize the first sentence of the new document in background
        if paragraphs and paragraphs[0].get("sentences"):
            first_sentence = paragraphs[0]["sentences"][0]
            background_tasks.add_task(async_generate_audio, first_sentence, "af", "en-us")
        
        return paragraphs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text", response_model=List[Paragraph])
async def upload_text(response: Response, payload: TextPayload, background_tasks: BackgroundTasks):
    global current_paragraphs, current_doc_id
    try:
        paragraphs = parse_raw_text(payload.text)
        
        # Generate new unique document ID to prevent cross-document cache collision
        current_doc_id = str(uuid.uuid4())[:8]
        response.headers["X-Doc-Id"] = current_doc_id
        
        # Replace active document paragraphs
        current_paragraphs = {p['id']: p for p in paragraphs}
        
        # Instantly pre-synthesize the first sentence of the new document in background
        if paragraphs and paragraphs[0].get("sentences"):
            first_sentence = paragraphs[0]["sentences"][0]
            background_tasks.add_task(async_generate_audio, first_sentence, "af", "en-us")
        
        return paragraphs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio")
async def get_audio(
    id: int = Query(...), 
    voice: str = Query("af"),
    lang: str = Query("en-us"),
    sentence_idx: int = Query(-1),
    doc_id: Optional[str] = Query(None)
):
    global current_paragraphs, current_doc_id
    
    # Reject stale requests from previous documents to prevent race conditions & wasted work
    if doc_id and current_doc_id and doc_id != current_doc_id:
        raise HTTPException(status_code=409, detail="Document version has changed")

    paragraph = current_paragraphs.get(id)
    if not paragraph:
        raise HTTPException(status_code=404, detail="Paragraph not found")
        
    # If sentence_idx is provided, play that sentence
    if sentence_idx >= 0 and "sentences" in paragraph and sentence_idx < len(paragraph["sentences"]):
        text_to_read = paragraph["sentences"][sentence_idx]
    else:
        text_to_read = paragraph["text"]
        
    try:
        wav_bytes, was_cached = await async_generate_audio(text_to_read, voice=voice, lang=lang)
        return RawResponse(
            content=wav_bytes,
            media_type="audio/wav",
            headers={
                "X-From-Cache": "true" if was_cached else "false",
                "X-Doc-Id": current_doc_id,
                # Crucial: Disable browser-level HTTP caching so different documents never replay old audio
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/preload")
async def preload_sentence(
    background_tasks: BackgroundTasks,
    id: int = Query(...),
    voice: str = Query("af"),
    lang: str = Query("en-us"),
    sentence_idx: int = Query(0),
    doc_id: Optional[str] = Query(None)
):
    global current_paragraphs, current_doc_id
    if doc_id and current_doc_id and doc_id != current_doc_id:
        return {"status": "ignored_stale_doc"}

    paragraph = current_paragraphs.get(id)
    if paragraph:
        if 0 <= sentence_idx < len(paragraph.get("sentences", [])):
            text = paragraph["sentences"][sentence_idx]
        else:
            text = paragraph["text"]
        background_tasks.add_task(async_generate_audio, text, voice, lang)
        return {"status": "queued"}
    return {"status": "not_found"}
