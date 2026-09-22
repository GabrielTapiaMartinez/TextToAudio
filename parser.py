import fitz
import re
import os
import statistics
from typing import List, Dict

if not os.environ.get("TESSDATA_PREFIX"):
    if os.path.exists("/opt/homebrew/share/tessdata"):
        os.environ["TESSDATA_PREFIX"] = "/opt/homebrew/share/tessdata"
    elif os.path.exists("/usr/local/share/tessdata"):
        os.environ["TESSDATA_PREFIX"] = "/usr/local/share/tessdata"

def split_sentences(text: str) -> List[str]:
    # Regex to split on ., !, or ? followed by space, taking care of quotes
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'“])', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 1]

def parse_raw_text(text: str) -> List[Dict]:
    paragraphs = []
    paragraph_id = 0
    
    # Split raw text by double newline to form paragraphs
    raw_paragraphs = text.split('\n\n')
    
    for raw_p in raw_paragraphs:
        clean_text = raw_p.strip()
        # Compress spaces and newlines
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if len(clean_text) > 5:
            sentences = split_sentences(clean_text)
            if not sentences:
                continue
                
            paragraphs.append({
                "id": paragraph_id,
                "text": clean_text,
                "sentences": sentences,
                "page": 1  # Dummy page for raw text
            })
            paragraph_id += 1
            
    return paragraphs

def parse_pdf(pdf_bytes: bytes) -> List[Dict]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    paragraphs = []
    paragraph_id = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Determine if we need OCR
        blocks_raw = page.get_text("blocks")
        text_blocks_raw = [b for b in blocks_raw if b[6] == 0]
        
        if not text_blocks_raw:
            try:
                # Need to specify PSM for 2-columns? flags=0 uses default. Let's just use it.
                textpage = page.get_textpage_ocr(flags=0, dpi=300, full=True)
            except Exception as e:
                print(f"OCR failed for page {page_num+1}: {e}")
                textpage = page.get_textpage()
        else:
            textpage = page.get_textpage()
            
        dict_data = page.get_text("dict", textpage=textpage)
        blocks = [b for b in dict_data["blocks"] if b["type"] == 0]
        
        # Sort blocks into columns. Round x0 to 200 to separate columns (a spread is ~1200 wide)
        # Using 200 pixels is safer for column sorting
        def block_sort_key(b):
            x0 = b["bbox"][0]
            y0 = b["bbox"][1]
            col = round(x0 / 200.0) * 200.0
            return (col, y0)
            
        blocks.sort(key=block_sort_key)
        
        for b in blocks:
            # Gather spans
            spans = []
            for line in b["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        spans.append({
                            "text": text,
                            "size": span["size"],
                            "y0": span["bbox"][1]
                        })
            
            if not spans:
                continue
                
            # Filter superscripts/artifacts
            sizes = [s["size"] for s in spans]
            median_size = statistics.median(sizes)
            
            # Reconstruct text
            clean_text = ""
            for span in spans:
                # Ignore very small text or likely artifacts/superscripts (size < 70% of median)
                if span["size"] < median_size * 0.75:
                    continue
                    
                # Ignore random OCR glitches like | or _
                if span["text"] in ["|", "_", "-", "—"]:
                    continue
                    
                clean_text += span["text"] + " "
                
            clean_text = clean_text.strip()
            
            # Header/Footer stripping (heuristic based on bbox)
            y0, y1 = b["bbox"][1], b["bbox"][3]
            if len(clean_text) < 30 and (y0 < 60 or y1 > page.rect.height - 60):
                continue
                
            # De-hyphenate and compress spaces
            clean_text = re.sub(r'-\s+', '', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            if len(clean_text) > 5:
                sentences = split_sentences(clean_text)
                if not sentences:
                    continue
                    
                paragraphs.append({
                    "id": paragraph_id,
                    "text": clean_text,
                    "sentences": sentences,
                    "page": page_num + 1
                })
                paragraph_id += 1
                
    return paragraphs
