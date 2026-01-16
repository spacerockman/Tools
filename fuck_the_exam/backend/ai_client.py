import os
import google.generativeai as genai
import json
import hashlib
from typing import List, Dict

# Retrieve API Key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

MODEL_NAME = "gemini-pro"  # Or gemini-1.5-flash if available and preferred

def generate_questions_from_topic(topic: str, num_questions: int = 5) -> List[Dict]:
    """
    Generates N1-level Japanese questions using Gemini API.
    """
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set.")
        return []

    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""
    You are a strict Japanese N1 Exam expert. 
    Generate {num_questions} multiple-choice questions testing the following topic: "{topic}".

    Constraint Checklist & Confidence Score:
    1. Strict N1 level? Yes.
    2. No duplicate questions? Yes.
    3. JSON output only? Yes.

    Output Format (strictly valid JSON list, no markdown):
    [
      {{
        "content": "JAPANESE_QUESTION_TEXT",
        "options": {{
            "A": "OPTION_A_TEXT",
            "B": "OPTION_B_TEXT",
            "C": "OPTION_C_TEXT",
            "D": "OPTION_D_TEXT"
        }},
        "correct_answer": "A",
        "explanation": "Detailed explanation in Chinese/Japanese (mostly Chinese for learners) focusing on why the answer is correct and why others are wrong.",
        "knowledge_point": "{topic}"
      }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # Clean up code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        questions = json.loads(text)
        
        # Add hash for each question
        for q in questions:
             # Create a unique hash based on content and options to detect duplicates
            unique_string = f"{q['content']}-{json.dumps(q['options'], sort_keys=True)}"
            q['hash'] = hashlib.sha256(unique_string.encode()).hexdigest()
            # Ensure options are serialized to string if your DB expects text, 
            # BUT our main logic might prefer keeping them as dict if Pydantic handles it. 
            # For now, let's keep them as dict and let the main.py/Pydantic handle the DB conversion.

        return questions

    except Exception as e:
        print(f"Error generating questions: {e}")
        return []

if __name__ == "__main__":
    # Test run
    result = generate_questions_from_topic("N1 Grammar: ～ざるを得ない")
    print(json.dumps(result, indent=2, ensure_ascii=False))