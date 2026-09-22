import fitz
import sys
import os

if not os.environ.get("TESSDATA_PREFIX"):
    if os.path.exists("/opt/homebrew/share/tessdata"):
        os.environ["TESSDATA_PREFIX"] = "/opt/homebrew/share/tessdata"
    elif os.path.exists("/usr/local/share/tessdata"):
        os.environ["TESSDATA_PREFIX"] = "/usr/local/share/tessdata"

def test_ocr(pdf_path):
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        # Try normal text
        text = page.get_text()
        if not text.strip():
            print(f"Page {i+1} has no text, trying OCR...")
            try:
                # Need to use get_textpage_ocr
                # TESSDATA_PREFIX environment variable may be needed, but fitz will try default
                textpage = page.get_textpage_ocr(flags=0, dpi=300, full=True)
                blocks = page.get_text("blocks", textpage=textpage)
                print(f"OCR found {len(blocks)} blocks on page {i+1}.")
                for b in blocks:
                    print(b[4])
            except Exception as e:
                print(f"OCR failed: {e}")
        else:
            print(f"Page {i+1} already has text.")
            
if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_ocr(sys.argv[1])
    else:
        print("Please provide a PDF path.")
