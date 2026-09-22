import fitz
import sys

def inspect_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    # Just look at page 10 where the OCR found text earlier
    page = doc[10]
    
    textpage = page.get_textpage_ocr(flags=0, dpi=300, full=True)
    blocks = page.get_text("blocks", textpage=textpage)
    
    text_blocks = [b for b in blocks if b[6] == 0]
    print(f"--- Raw Blocks on Page 10 ---")
    for b in text_blocks:
        print(repr(b[4]))
        print("-" * 20)

if __name__ == "__main__":
    inspect_pdf("test_media/Meyers - The Happiness Hypothesis Scan.pdf")
