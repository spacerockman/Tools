#!/usr/bin/env python3
"""
Rebuild the RAG index from PDF textbooks.
Usage: python rebuild_index.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

from services.rag_service import rag

def main():
    print("Rebuilding RAG index from textbooks...")
    print("This may take several minutes on first run.")
    print("=" * 60)
    
    rag.load_or_build(force=True)
    
    print("\nIndex rebuild complete!")
    print(f"Total chunks indexed: {len(rag.chunks)}")

if __name__ == "__main__":
    main()
