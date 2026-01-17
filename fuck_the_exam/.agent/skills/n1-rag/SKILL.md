---
name: n1-rag
description: Ability to query the RAG system for textbook-based verification of Japanese N1 grammar and vocabulary.
---
# N1 RAG (Textbook Verification) Skill

This skill allows the agent to leverage the local RAG system to verify knowledge points against authoritative N1 textbooks.

## Available Tools (via scripts)
- **`query_textbook.py <topic>`**: Queries the RAG index for relevant textbook content about a specific grammar point or vocabulary.
- **`rebuild_index.py`**: Forces a rebuild of the RAG index from the PDF textbooks (use when textbooks are updated).

## Critical Paths
- `backend/services/rag_service.py`: RAG service implementation with local embeddings.
- `backend/knowledge_base/teaching_material/`: Directory containing N1 PDF textbooks.
- `backend/rag_cache/`: Cached embeddings and FAISS index.

## Technical Details
- **Model**: BAAI/bge-m3 (local, runs on MPS/CPU)
- **OCR**: Tesseract with Japanese language data
- **Index**: FAISS with cosine similarity

## Usage
"Query the textbook for information about '～こそすれ' to verify the accuracy of the generated questions."
