import os
import pytesseract
from PIL import Image
import fitz
import io

# Explicit paths
TESS_CMD = "/opt/homebrew/bin/tesseract"
TESSDATA_DIR = "/Users/xujintao/Documents/workspace/Tools/fuck_the_exam/backend/knowledge_base/tessdata"
PDF_PATH = "/Users/xujintao/Documents/workspace/Tools/fuck_the_exam/backend/knowledge_base/teaching_material/N1语法__新日语能力考试考前对策.pdf"

pytesseract.pytesseract.tesseract_cmd = TESS_CMD
os.environ["TESSDATA_PREFIX"] = os.path.dirname(TESSDATA_DIR)

print(f"TESSDATA_DIR: {TESSDATA_DIR}")
print(f"TESSDATA_PREFIX: {os.environ['TESSDATA_PREFIX']}")

try:
    doc = fitz.open(PDF_PATH)
    page = doc[10] # page 11
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    
    # Try with config
    config = f'--tessdata-dir "{TESSDATA_DIR}"'
    text = pytesseract.image_to_string(img, lang="jpn", config=config)
    
    print("--- OCR RESULT ---")
    print(text[:500])
    print("------------------")
    doc.close()
except Exception as e:
    print(f"Error: {e}")
