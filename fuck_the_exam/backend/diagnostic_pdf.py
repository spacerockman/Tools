import fitz
import sys

path = "/Users/xujintao/Documents/workspace/Tools/fuck_the_exam/backend/knowledge_base/teaching_material/N1语法__新日语能力考试考前对策.pdf"
try:
    doc = fitz.open(path)
    print(f"Pages: {len(doc)}")
    for i in range(min(5, len(doc))):
        page = doc[i]
        text = page.get_text().strip()
        print(f"Page {i+1} text (first 100 chars): {text[:100]}")
        objs = page.get_images()
        print(f"Page {i+1} images: {len(objs)}")
    doc.close()
except Exception as e:
    print(f"Error: {e}")
