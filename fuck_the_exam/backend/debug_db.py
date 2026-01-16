
import sys
import os

# Add /app to path (where backend package lives)
sys.path.append("/app")

from backend import database, models
from sqlalchemy import text

def debug_questions():
    db = database.SessionLocal()
    try:
        questions = db.query(models.Question).all()
        print(f"Found {len(questions)} questions.")
        for q in questions:
            print(f"--- Question ID: {q.id} ---")
            print(f"Content: {q.content[:50]}...")
            print(f"Correct Answer: '{q.correct_answer}' (Type: {type(q.correct_answer)})")
            print(f"Explanation: '{q.explanation}'")
            # print(f"Options: {q.options}") 
            print(f"Hash: {q.hash}")
            print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_questions()
