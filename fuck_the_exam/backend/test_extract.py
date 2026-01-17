import fitz

PDF_PATH = "/Users/xujintao/Documents/workspace/Tools/fuck_the_exam/backend/knowledge_base/teaching_material/N1语法__新日语能力考试考前对策.pdf"

try:
    doc = fitz.open(PDF_PATH)
    page = doc[50]
    img_list = page.get_images(full=True)
    print(f"Images on page 51: {len(img_list)}")
    
    if img_list:
        xref = img_list[0][0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        print(f"Extracted image size: {len(image_bytes)} bytes, extension: {base_image['ext']}")
        
        # Save if it seems valid
        with open("test_extract.png", "wb") as f:
            f.write(image_bytes)
    doc.close()
except Exception as e:
    print(f"Error: {e}")
