import requests
import sys

def trigger_ingestion():
    """
    Triggers the backend API to ingest questions from JSON files.
    The ingestion is actually part of the startup and study session logic,
    but we can trigger it via any endpoint that calls ingest_json_questions.
    We'll use /api/quiz/study which triggers ingestion.
    """
    url = "http://localhost:8000/api/quiz/study"
    
    try:
        print("Triging ingestion by calling study session endpoint...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        print("Successfully triggered ingestion! New questions should be in the DB.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    trigger_ingestion()
