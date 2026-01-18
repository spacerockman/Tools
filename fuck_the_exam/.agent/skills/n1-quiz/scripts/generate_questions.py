import requests
import sys
import json

def trigger_generation(topic, num_questions=5):
    """
    Triggers the backend API to generate questions for a specific topic.
    """
    url = "http://localhost:28888/api/quiz/generate"
    payload = {
        "topic": topic,
        "num_questions": num_questions
    }
    
    try:
        print(f"Requesting generation of {num_questions} questions for: {topic}...")
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        print("Successfully triggered generation!")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_questions.py <topic> [num_questions]")
        sys.exit(1)
        
    topic = sys.argv[1]
    num_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    result = trigger_generation(topic, num_questions)
    if result:
        print(f"Generated {len(result)} questions.")
