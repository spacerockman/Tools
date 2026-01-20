import os
import shutil

BASE_DIR = os.path.join(os.path.dirname(__file__), "..") # backend/
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
N1_TARGET = os.path.join(KB_DIR, "n1")

def fix():
    # Check if 'n1' is a file
    if os.path.isfile(N1_TARGET):
        print("'n1' is a file, renaming context...")
        temp_file = os.path.join(KB_DIR, "语法.md")
        os.rename(N1_TARGET, temp_file)
        
        # Create dir
        os.makedirs(N1_TARGET, exist_ok=True)
        
        # Move back
        shutil.move(temp_file, os.path.join(N1_TARGET, "语法.md"))
        print("Fixed: Moved content to n1/语法.md")
    else:
        print("'n1' is not a file, checking if it is a dir...")
        if not os.path.exists(N1_TARGET):
            os.makedirs(N1_TARGET)
            print("Created n1 dir")
            
    # Check if we need to move from old 知识点
    OLD_DIR = os.path.join(BASE_DIR, "知识点")
    OLD_FILE = os.path.join(OLD_DIR, "语法.md")
    
    if os.path.exists(OLD_FILE):
        print("Moving from old 知识点...")
        os.makedirs(N1_TARGET, exist_ok=True)
        shutil.move(OLD_FILE, os.path.join(N1_TARGET, "语法.md"))
        print("Moved.")
        
    # Create databricks dir
    DB_DIR = os.path.join(KB_DIR, "databricks")
    os.makedirs(DB_DIR, exist_ok=True)
    print("Databricks dir ready.")

if __name__ == "__main__":
    fix()
