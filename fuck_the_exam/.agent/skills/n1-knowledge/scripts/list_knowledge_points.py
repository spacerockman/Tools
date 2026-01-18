import os
import sys

def list_knowledge_points():
    """
    Lists all available knowledge points in the backend/知识点 directory.
    """
    kb_path = os.path.join(os.getcwd(), "backend", "知识点")
    if not os.path.exists(kb_path):
        kb_path = os.path.join(os.getcwd(), "knowledge_base", "知识点") # Fallback
        
    if not os.path.exists(kb_path):
        print(f"Error: Knowledge base directory not found at {kb_path}")
        return

    print(f"Knowledge points in {kb_path}:")
    for filename in os.listdir(kb_path):
        if filename.endswith(".md"):
            print(f"- {filename}")
            # Optional: parse headers to find specific points
            with open(os.path.join(kb_path, filename), 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("## "):
                        print(f"  * {line.strip('## ').strip()}")

if __name__ == "__main__":
    list_knowledge_points()
