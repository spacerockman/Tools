import os
import json
import hashlib
import requests
from typing import List, Dict

# SiliconFlow API Configuration
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
# Ideally this should be in an env var like SILICONFLOW_API_KEY
# Using the provided key for now as requested
API_KEY = "sk-dghfpxoqxxsahxgcljjlkoyjebiyulmwdegyrhmztqecyiwt"

MODEL_NAME = "deepseek-ai/DeepSeek-V3.2"

def generate_questions_from_topic(topic: str, num_questions: int = 5) -> List[Dict]:
    """
    Generates N1-level Japanese questions using SiliconFlow (DeepSeek) API.
    """
    if not API_KEY:
        print("Error: API_KEY is not set.")
        return []

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    system_prompt = f"""
    You are a strict Japanese N1 Exam expert. 
    Generate {num_questions} multiple-choice questions testing the following topic: "{topic}".

    Constraint Checklist:
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
        "memorization_tip": "A short, catchy tip or mnemonic to help remember this grammar/vocab point.",
        "knowledge_point": "{topic}"
      }}
    ]
    """

    data = {
        "model": "deepseek-ai/DeepSeek-V3", # Falling back to V3 as V3.2 might be a specific internal alias or just V3 in public API. User payload said V3.2 but standard is usually V3. Let's try what user gave first? Actually user log said V3.2, let's stick to what works or standard. 
        # Wait, the user provided `deepseek-ai/DeepSeek-V3.2` in the curl command. I will use exactly that.
        "model": "deepseek-ai/DeepSeek-V3.2",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please generate {num_questions} questions about {topic}."}
        ],
        "temperature": 0.7,
        "max_tokens": 4000, # Increased for JSON list
        "response_format": {"type": "json_object"} # DeepSeek supports json mode often, but let's be safe with prompt engineering too. 
        # Actually SiliconFlow/DeepSeek often respects 'json_object' if model supports it. 
        # Let's try without forcing response_format first to match the user's curl which didn't have it, but DID have prompt constraints.
    }
    
    # User's curl didn't use response_format, relying on prompt.
    if "json" in system_prompt.lower():
         # Good practice to hint json in prompt
         pass

    try:
        print(f"Sending request to SiliconFlow API (Topic: {topic})...")
        # Increased timeout to 120s as DeepSeek can be slow
        response = requests.post(API_URL, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        
        result_json = response.json()
        print("Received response from AI.")
        
        if 'choices' not in result_json:
             print(f"Unexpected response format: {result_json}")
             return []
             
        content = result_json['choices'][0]['message']['content']
        # print(f"Raw content: {content}") # Debug: Print raw content
        
        # Clean up code blocks if present (DeepSeek might wrap in ```json ... ```)
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"): # Sometimes just ```
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        questions = json.loads(content)
        
        # Handle case where AI wraps response in {"questions": [...]}
        if isinstance(questions, dict) and "questions" in questions:
            questions = questions["questions"]
            
        # Add hash for each question
        for q in questions:
             # Create a unique hash based on content and options to detect duplicates
            unique_string = f"{q['content']}-{json.dumps(q['options'], sort_keys=True)}"
            q['hash'] = hashlib.sha256(unique_string.encode()).hexdigest()

        return questions

    except Exception as e:
        print(f"Error generating questions: {e}")
        if 'response' in locals():
            print(f"Response Content: {response.text}")
        return []

if __name__ == "__main__":
    # Test run
    print("Testing SiliconFlow API...")
    result = generate_questions_from_topic("N1 Grammar: ～ざるを得ない", num_questions=1)
    print(json.dumps(result, indent=2, ensure_ascii=False))