import os
import json
import fitz  # PyMuPDF
import faiss
import numpy as np
import hashlib
import pytesseract
from PIL import Image
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import torch

EMBED_MODEL_NAME = "BAAI/bge-m3"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "rag_cache")
TEXT_CACHE_DIR = os.path.join(CACHE_DIR, "text_cache")
MATERIAL_DIR = os.path.join(BASE_DIR, "knowledge_base", "teaching_material")
TESSDATA_DIR = os.path.join(BASE_DIR, "knowledge_base", "tessdata")

# Configure Tesseract
# TESSDATA_PREFIX should point to the directory CONTAINING the 'tessdata' folder
# However, TESSDATA_DIR is .../tessdata, so the prefix should be the parent.
os.environ["TESSDATA_PREFIX"] = os.path.dirname(TESSDATA_DIR)

class RAGService:
    def __init__(self):
        self.index = None
        self.chunks = []
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(TEXT_CACHE_DIR, exist_ok=True)
        self.index_path = os.path.join(CACHE_DIR, "vector.index")
        self.chunks_path = os.path.join(CACHE_DIR, "chunks.json")
        
        # Initialize Local Model
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Initializing RAG Service on device: {device}")
        try:
            self.model = SentenceTransformer(EMBED_MODEL_NAME, device=device)
        except Exception as e:
            print(f"Error loading model {EMBED_MODEL_NAME}: {e}")
            self.model = None

    def _ocr_page(self, doc_path: str, page_num: int) -> str:
        """
        Extends text from a page using OCR if necessary.
        """
        cache_key = hashlib.md5(f"{doc_path}_{page_num}".encode()).hexdigest()
        cache_path = os.path.join(TEXT_CACHE_DIR, f"{cache_key}.txt")
        
        # If cache exists and is NOT empty, return it
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()

        try:
            doc = fitz.open(doc_path)
            page = doc[page_num]
            text = page.get_text().strip()
            
            # If no text or text is likely too short, use OCR
            if len(text) < 50:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # High res for OCR
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                # Explicitly point to tessdata and use Japanese
                tess_config = f'--tessdata-dir "{TESSDATA_DIR}"'
                text = pytesseract.image_to_string(img, lang="jpn+eng", config=tess_config)
            
            doc.close()
            
            # Save to cache
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return text
        except Exception as e:
            print(f"OCR Error on {doc_path} p{page_num}: {e}")
            return ""

    def load_or_build(self, force: bool = False):
        if not self.model:
            print("Model not loaded, cannot build index.")
            return

        if not force and os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            print("Loading existing RAG index...")
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.chunks_path, 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
                return
            except Exception as e:
                print(f"Error loading index: {e}. Rebuilding...")

        print("Building new RAG index (with OCR)...")
        all_chunks = []
        
        if not os.path.exists(MATERIAL_DIR):
            print(f"Material directory not found: {MATERIAL_DIR}")
            return

        pdf_files = [f for f in os.listdir(MATERIAL_DIR) if f.endswith(".pdf")]
        for filename in pdf_files:
            path = os.path.join(MATERIAL_DIR, filename)
            doc = fitz.open(path)
            num_pages = len(doc)
            doc.close()
            
            print(f"  Processing {filename} ({num_pages} pages)...")
            
            # Use parallel OCR/Extraction
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(self._ocr_page, path, p): p for p in range(num_pages)}
                for future in as_completed(futures):
                    p = futures[future]
                    content = future.result()
                    if len(content) > 100:
                        all_chunks.append({
                            "source": filename,
                            "page": p + 1,
                            "content": content
                        })
            print(f"  Extracted {len(all_chunks)} chunks so far.")

        if not all_chunks:
            print("No text found.")
            return

        print(f"  Generating embeddings for {len(all_chunks)} chunks...")
        
        # Batch processing for embeddings
        texts = [chunk['content'] for chunk in all_chunks]
        
        try:
            # Encode all at once (SentenceTransformer handles batching internally usually, but we can call it directly)
            embeddings_np = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            return

        dimension = embeddings_np.shape[1]
        
        print(f"  Building FAISS index (dimension={dimension})...")
        self.index = faiss.IndexFlatIP(dimension) # Use Inner Product for normalized embeddings (Cosine Similarity)
        self.index.add(embeddings_np)
        self.chunks = all_chunks
        
        # Save
        faiss.write_index(self.index, self.index_path)
        with open(self.chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"RAG index built with {len(self.chunks)} chunks and saved.")

    def query(self, topic: str, top_k: int = 3) -> str:
        if not self.model:
            # Try to init again if failed (unlikely but safe)
            return ""
            
        if not self.index:
            self.load_or_build()
        if not self.index:
            return ""

        try:
            query_vector = self.model.encode([topic], convert_to_numpy=True, normalize_embeddings=True)
            distances, indices = self.index.search(query_vector, top_k)
            
            results = []
            for idx in indices[0]:
                if idx != -1 and idx < len(self.chunks):
                    chunk = self.chunks[idx]
                    results.append(f"Source: {chunk['source']} (Page {chunk['page']})\nContent: {chunk['content']}")
            
            return "\n\n---\n\n".join(results)
        except Exception as e:
            print(f"Query error: {e}")
            return ""

# Global instance
rag = RAGService()

if __name__ == "__main__":
    # Test
    rag.load_or_build()
    print("\nTest Query: こそすれ")
    print(rag.query("こそすれ"))
