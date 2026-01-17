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

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct" # Light, fast, and fully compatible with the standard chat API

from concurrent.futures import ThreadPoolExecutor, as_completed

def _single_generate_batch(topic: str, batch_size: int, headers: Dict, max_retries: int = 3) -> List[Dict]:
    """
    Internal helper to generate a single batch of questions.
    """
    system_prompt = f"""
    You are a strict Japanese N1 Exam expert. 
    Generate {batch_size} multiple-choice questions testing the following topic: "{topic}".

    Constraint Checklist:
    1. Strict N1 level? Yes.
    2. No duplicate questions? Yes.
    3. JSON output only? Yes.
    4. IMPORTANT: The "knowledge_point" field MUST be exactly "{topic}" for ALL questions.

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
        "explanation": "Detailed explanation in Chinese/Japanese.",
        "memorization_tip": "A short, catchy tip.",
        "knowledge_point": "{topic}"
      }}
    ]
    """

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please generate {batch_size} questions about {topic}."}
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    for attempt in range(max_retries):
        try:
            timeout = 100 + (attempt * 40)
            response = requests.post(API_URL, headers=headers, json=data, timeout=timeout)
            response.raise_for_status()
            
            result_json = response.json()
            content = result_json['choices'][0]['message']['content'].strip()
            
            # Clean up code blocks
            if content.startswith("```"):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
                content = content.strip()
            
            questions = json.loads(content)
            if isinstance(questions, dict) and "questions" in questions:
                questions = questions["questions"]
                
            return questions if isinstance(questions, list) else []
            
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            if attempt == max_retries - 1:
                print(f"  [Batch Request] Final Error: {e}")
                return []
    return []

def generate_questions_from_topic(topic: str, num_questions: int = 5, batch_size: int = 2) -> List[Dict]:
    """
    Generates N1-level Japanese questions using SiliconFlow API.
    Uses ultra-fast models and high concurrency for maximum speed.
    """
    if not API_KEY:
        print("Error: API_KEY is not set.")
        return []

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    all_questions = []
    
    # Calculate batches (Smaller batches + Higher concurrency = Faster overall completion)
    batches = []
    remaining = num_questions
    while remaining > 0:
        current_batch_size = min(batch_size, remaining)
        batches.append(current_batch_size)
        remaining -= current_batch_size

    print(f"Starting ultra-fast parallel generation of {num_questions} questions for topic: {topic}")
    
    # Increase max_workers to push for higher throughput
    with ThreadPoolExecutor(max_workers=min(len(batches), 25)) as executor:
        futures = {executor.submit(_single_generate_batch, topic, b_size, headers): i for i, b_size in enumerate(batches)}
        
        for future in as_completed(futures):
            batch_index = futures[future]
            try:
                batch_questions = future.result()
                if batch_questions:
                    for q in batch_questions:
                        if q.get('content'):
                            unique_string = f"{q.get('content', '')}-{json.dumps(q.get('options', {}), sort_keys=True)}"
                            q['hash'] = hashlib.sha256(unique_string.encode()).hexdigest()
                            all_questions.append(q)
                    print(f"  [Batch {batch_index+1}] Done.")
            except Exception:
                pass

    print(f"Completed: {len(all_questions)}/{num_questions} questions.")
    return all_questions
    
    return []

if __name__ == "__main__":
    # Test run
    print("Testing SiliconFlow API...")
    result = generate_questions_from_topic("N1 Grammar: ～ざるを得ない", num_questions=1)
    print(json.dumps(result, indent=2, ensure_ascii=False))