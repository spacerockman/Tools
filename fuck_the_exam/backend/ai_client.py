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

def generate_questions_from_topic(topic: str, num_questions: int = 5, max_retries: int = 3) -> List[Dict]:
    """
    Generates N1-level Japanese questions using SiliconFlow (DeepSeek) API.
    Includes retry logic for timeout errors.
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
    4. IMPORTANT: The "knowledge_point" field MUST be exactly "{topic}" for ALL questions. Do NOT add any prefix, suffix, or variation.

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
        "model": "deepseek-ai/DeepSeek-V3.2",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please generate {num_questions} questions about {topic}."}
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
    }
    
    # Retry logic with longer timeouts (API is very slow)
    for attempt in range(max_retries):
        try:
            timeout = 180 + (attempt * 60)  # 180s, 240s, 300s (3-5 minutes)
            print(f"[Attempt {attempt + 1}/{max_retries}] Sending request to SiliconFlow API (Topic: {topic}, Timeout: {timeout}s)...")
            
            response = requests.post(API_URL, headers=headers, json=data, timeout=timeout)
            response.raise_for_status()
            
            result_json = response.json()
            print("Received response from AI.")
            
            if 'choices' not in result_json:
                print(f"Unexpected response format: {result_json}")
                return []
                
            content = result_json['choices'][0]['message']['content']
            
            # Clean up code blocks if present
            content = content.strip()
            if content.startswith("```"):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
                content = content.strip()
            
            questions = json.loads(content)
            
            # Handle wrapped response
            if isinstance(questions, dict) and "questions" in questions:
                questions = questions["questions"]
                
            # Add hash for each question
            for q in questions:
                unique_string = f"{q['content']}-{json.dumps(q['options'], sort_keys=True)}"
                q['hash'] = hashlib.sha256(unique_string.encode()).hexdigest()
            
            print(f"Successfully generated {len(questions)} questions.")
            return questions
            
        except requests.exceptions.Timeout:
            print(f"[Attempt {attempt + 1}] Timeout after {timeout}s. {'Retrying...' if attempt < max_retries - 1 else 'Giving up.'}")
            if attempt == max_retries - 1:
                return []
        except requests.exceptions.RequestException as e:
            print(f"[Attempt {attempt + 1}] Request error: {e}")
            if attempt == max_retries - 1:
                return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response Content: {response.text[:500]}")
            return []
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []
    
    return []

if __name__ == "__main__":
    # Test run
    print("Testing SiliconFlow API...")
    result = generate_questions_from_topic("N1 Grammar: ～ざるを得ない", num_questions=1)
    print(json.dumps(result, indent=2, ensure_ascii=False))