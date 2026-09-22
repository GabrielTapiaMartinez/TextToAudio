import asyncio
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Frame, PageTemplate, FrameBreak, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
import fitz
import os

from parser import parse_pdf
from tts_engine import generate_audio, get_model

def create_test_pdf() -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # 2-column layout
    frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-6, doc.height, id='col1')
    frame2 = Frame(doc.leftMargin+doc.width/2+6, doc.bottomMargin, doc.width/2-6, doc.height, id='col2')
    
    doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[frame1, frame2])])
    
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    
    # Text for testing
    story = [
        Paragraph("This is the first paragraph. It is located in the left column. The parser should read this first.", style),
        Spacer(1, 12),
        Paragraph("This is the second paragraph, also in the left column. We are testing the reading order.", style),
        FrameBreak(),
        Paragraph("This is the third paragraph, which appears in the right column. It should be read after the left column paragraphs.", style),
        Spacer(1, 12),
        Paragraph("Este es un párrafo de prueba en español. Debe ser leído usando el modelo de voz en español.", style),
        Spacer(1, 12),
        Paragraph("A paragraph split with a hy-\nphen. The parser should fix it into 'hyphen'.", style)
    ]
    
    doc.build(story)
    return buffer.getvalue()

def test_pipeline():
    print("1. Creating test PDF...")
    pdf_bytes = create_test_pdf()
    
    print("2. Parsing PDF...")
    paragraphs = parse_pdf(pdf_bytes)
    
    for p in paragraphs:
        print(f"[{p['id']}] Page {p['page']}: {p['text']}")
        
    assert "left column" in paragraphs[0]['text']
    assert "second paragraph" in paragraphs[1]['text']
    assert "right column" in paragraphs[2]['text']
    assert "español" in paragraphs[3]['text']
    assert "hyphen" in paragraphs[4]['text']
    print("Reading order & parsing looks good!")
    
    print("3. Testing TTS Engine (English)...")
    get_model() # Preload model
    
    wav_en = generate_audio(paragraphs[0]['text'], voice="af", lang="en-us")
    assert len(wav_en) > 1000
    print(f"Generated {len(wav_en)} bytes of WAV audio for English.")
    
    print("All automated tests passed successfully!")

if __name__ == "__main__":
    test_pipeline()
