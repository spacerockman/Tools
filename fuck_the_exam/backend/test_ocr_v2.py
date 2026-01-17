import os
import pytesseract
from PIL import Image
import fitz
import io

TESS_CMD = "/opt/homebrew/bin/tesseract"
TESSDATA_DIR = "/Users/xujintao/Documents/workspace/Tools/fuck_the_exam/backend/knowledge_base/tessdata"
PDF_PATH = "/Users/xujintao/Documents/workspace/Tools/fuck_the_exam/backend/knowledge_base/teaching_material/N1语法__新日语能力考试考前对策.pdf"

pytesseract.pytesseract.tesseract_cmd = TESS_CMD
os.environ["TESSDATA_PREFIX"] = os.path.dirname(TESSDATA_DIR)

config_str = f'--tessdata-dir "{TESSDATA_DIR}"'
print(f"Available langs: {pytesseract.get_languages(config=config_str)}")

try:
    doc = fitz.open(PDF_PATH)
    page = doc[50] # page 51 - more likely to have text
    print(f"Page rect: {page.rect}")
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    print(f"Pixmap size: {pix.width}x{pix.height}, bytes: {len(pix.tobytes())}")
    
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    config = f'--tessdata-dir "{TESSDATA_DIR}"'
    text = pytesseract.image_to_string(img, lang="jpn", config=config)
    
    print(f"OCR result length: {len(text)}")
    print("--- FIRST 200 CHARS ---")
    print(text[:200])
    print("------------------------")
    doc.close()
except Exception as e:
    print(f"Error: {e}")
