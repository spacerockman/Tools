import os
import sys

def search_knowledge(query):
    """
    Searches for a keyword in the knowledge_base/知识点 directory.
    """
    kb_path = os.path.join(os.getcwd(), "backend", "知识点")
    if not os.path.exists(kb_path):
        kb_path = os.path.join(os.getcwd(), "knowledge_base", "知识点") # Fallback
        
    results = []
    if not os.path.exists(kb_path):
        print(f"Error: Knowledge base directory not found at {kb_path}")
        return results

    for filename in os.listdir(kb_path):
        if filename.endswith(".md"):
            file_path = os.path.join(kb_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if query.lower() in content.lower():
                    results.append({
                        "file": filename,
                        "match": True
                    })
                    print(f"Found match in {filename}")

    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search_knowledge.py <query>")
        sys.exit(1)
        
    search_knowledge(sys.argv[1])
