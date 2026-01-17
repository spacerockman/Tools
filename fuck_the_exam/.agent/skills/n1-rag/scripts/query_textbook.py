#!/usr/bin/env python3
"""
Query the RAG system for textbook content about a specific topic.
Usage: python query_textbook.py <topic> [top_k]
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

from services.rag_service import rag

def main():
    if len(sys.argv) < 2:
        print("Usage: python query_textbook.py <topic> [top_k]")
        sys.exit(1)
    
    topic = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    print(f"Querying RAG for: {topic}")
    print("=" * 60)
    
    result = rag.query(topic, top_k=top_k)
    
    if result:
        print(result)
    else:
        print("No results found or RAG index not initialized.")

if __name__ == "__main__":
    main()
