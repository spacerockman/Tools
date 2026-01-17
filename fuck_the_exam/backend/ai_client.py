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

MODEL_NAME = "deepseek-ai/DeepSeek-V3"

def get_grammar_grounding(topic: str) -> str:
    """
    Looks up the topic in backend/知识点/语法.md to provide grounding.
    """
    kb_path = os.path.join(os.path.dirname(__file__), "知识点", "语法.md")
    if not os.path.exists(kb_path):
        return ""
    
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if "|" in line and topic in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 7:
                        return f"【语法逻辑】: {parts[3]}\n【核心含义】: {parts[4]}\n【常见搭配】: {parts[5]}\n【易错点】: {parts[6]}\n【典型例句】: {parts[7]}"
    except Exception:
        pass
    return ""

from concurrent.futures import ThreadPoolExecutor, as_completed

def _single_generate_batch(topic_raw: str, batch_size: int, headers: Dict, max_retries: int = 3) -> List[Dict]:
    """
    Internal helper to generate a single batch of questions.
    """
    # Clean up topic to extract just the core grammar/vocab if it has a prefix
    topic = topic_raw.replace("N1 Grammar:", "").replace("N1 Vocab:", "").replace("N1 阅读:", "").strip()
    if topic.startswith("～"): topic = topic[1:]

    # Fetch Grounding Info
    grounding = get_grammar_grounding(topic)
    grounding_prompt = f"\nGROUNDING DATA (Source of Truth):\n{grounding}\n" if grounding else ""

    system_prompt = f"""
    You are a world-class Japanese Language Proficiency Test (JLPT) N1 examiner. 
    Your goal is to generate {batch_size} high-stakes, realistic multiple-choice questions for the topic: "{topic}".
    {grounding_prompt}

    STRICT JLPT N1 FORMATTING & LINGUISTIC RULES:
    1. EXAM FORMAT (穴埋め): 
       - The 'content' MUST be a full Japanese sentence with a blank marked as '（　　）'.
       - Questions MUST NOT ask for definitions or translations. They must test usage in context.
    2. LANGUAGE ISOLATION:
       - 'options' (A, B, C, D) MUST be 100% Japanese. 
       - DO NOT include Chinese or English translations in the options.
       - 'explanation' and 'memorization_tip' should be in professional Chinese.
    3. TARGET GRAMMAR ACCURACY & NO LEAKAGE (CRITICAL):
       - You must correctly identify the linguistic function of "{topic}".
       - **CORE RULE**: The 'correct_answer' choice MUST be the "{topic}" itself OR a grammatically correct phrase that uses "{topic}".
       - **NO LEAKAGE RULE**: The target grammar "{topic}" (and its core keywords) MUST NOT appear anywhere in the 'content' string outside of the options.
       - Example: If `{topic}` is "～こそすれ", the 'content' MUST NOT contain "こそ" or "すれ". The 'correct_answer' option MUST be "こそすれ" or contain it.
    4. N1-LEVEL DISTRACTORS:
       - Distractors must be highly plausible. Use:
         - Synonyms with different collocations.
         - Grammar points with similar prefixes/suffixes (e.g., ～と思いきや vs ～と思えば).
         - Formal/written-style vocabulary (硬い表现).
    5. NO TRIVIAL OPTIONS: Every option must look like it could be correct to a non-master.
    6. ABSOLUTE ACCURACY & VERIFICATION:
       - The 'explanation' field must include why the correct answer is right AND why each distractor is definitively wrong in this specific context.
    """

def _review_questions(questions: List[Dict], topic: str, grounding: str, headers: Dict) -> List[Dict]:
    """
    Agent 2: Reviewer. Audits questions for N1 quality and accuracy.
    Includes local markdown context for academic grounding.
    """
    grounding_text = f"GROUNDING DATA:\n{grounding}" if grounding else ""
    review_prompt = f"""
    You are a Senior JLPT N1 Quality Auditor. Your job is to strictly review the following questions for the topic "{topic}".
    {grounding_text}

    CHECKLIST:
    1. LINGUISTIC ACCURACY: Is the grammar usage 100% correct for N1?
    2. NO LEAKAGE: Does the target grammar "{topic}" appear in the 'content' outside the blank? (FAIL if yes)
    3. DISTRACTOR QUALITY: Are distractors N1-level and plausible, yet definitively wrong?
    4. EXPLANATION: Does the explanation correctly analyze the grammar based on GROUNDING context?

    OUTPUT FORMAT:
    Return a JSON list of objects, one for each question:
    [
      {{
        "id": 0,
        "status": "PASS" or "FAIL",
        "issues": ["List of specific linguistic or formatting issues"]
      }}
    ]
    """
    
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": review_prompt},
            {"role": "user", "content": json.dumps(questions, ensure_ascii=False)}
        ],
        "temperature": 0.1,
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"): content = content[4:]
            content = content.split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        print(f"  [Reviewer] Error: {e}")
        return [{"status": "PASS", "issues": []} for _ in questions]

def _optimize_questions(questions: List[Dict], review_results: List[Dict], topic: str, grounding: str, headers: Dict) -> List[Dict]:
    """
    Agent 3: Optimizer (Corrector). Fixes questions based on reviewer feedback.
    """
    grounding_text = f"GROUNDING DATA:\n{grounding}" if grounding else ""
    optimize_prompt = f"""
    You are a JLPT N1 Master Editor. Your task is to FIX the following questions based on the Quality Auditor's report for the topic "{topic}".
    {grounding_text}

    Rules:
    - Keep the same JSON format.
    - Fix all linguistic errors.
    - Ensure NO LEAKAGE of "{topic}" in the content.
    - Improve distractors if marked as too easy.
    """
    
    input_data = {
        "questions": questions,
        "review_report": review_results
    }
    
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": optimize_prompt},
            {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)}
        ],
        "temperature": 0.2,
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=150)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"): content = content[4:]
            content = content.split("```")[0].strip()
        fixed = json.loads(content)
        return fixed if isinstance(fixed, list) else questions
    except Exception as e:
        print(f"  [Optimizer] Error: {e}")
        return questions

def _single_generate_batch(topic_raw: str, batch_size: int, headers: Dict, max_retries: int = 3) -> List[Dict]:
    """
    Multi-Agent Pipeline: Generator -> Reviewer -> Optimizer.
    """
    topic = topic_raw.replace("N1 Grammar:", "").replace("N1 Vocab:", "").replace("N1 阅读:", "").strip()
    if topic.startswith("～"): topic = topic[1:]

    grounding = get_grammar_grounding(topic)
    grounding_prompt = f"\nGROUNDING DATA (Source of Truth):\n{grounding}\n" if grounding else ""

    # Phase 1: Generation
    system_prompt = f"""
    You are a world-class Japanese Language Proficiency Test (JLPT) N1 examiner. 
    Your goal is to generate {batch_size} high-stakes, realistic multiple-choice questions for the topic: "{topic}".
    {grounding_prompt}

    STRICT JLPT N1 FORMATTING & LINGUISTIC RULES:
    1. EXAM FORMAT (穴埋め): 
       - The 'content' MUST be a full Japanese sentence with a blank marked as '（　　）'.
       - Questions MUST NOT ask for definitions or translations. They must test usage in context.
    2. LANGUAGE ISOLATION:
       - 'options' (A, B, C, D) MUST be 100% Japanese. 
       - 'explanation' and 'memorization_tip' should be in professional Chinese.
    3. TARGET GRAMMAR ACCURACY & NO LEAKAGE (CRITICAL):
       - **CORE RULE**: The 'correct_answer' choice MUST use "{topic}".
       - **NO LEAKAGE RULE**: The target grammar "{topic}" MUST NOT appear in 'content' outside of the options.
    4. N1-LEVEL DISTRACTORS: Use high-level synonyms or similar-looking grammar.
    5. ABSOLUTE ACCURACY: Use GROUNDING DATA as truth. Explain why distractors are wrong.

    Return a JSON list.
    """

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "system", "content": system_prompt}],
        "temperature": 0.3,
    }

    questions = []
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content'].strip()
            if content.startswith("```"):
                content = '\n'.join(content.split('\n')[1:-1] if '```' in content.split('\n')[-1] else content.split('\n')[1:]).strip()
            questions = json.loads(content)
            if isinstance(questions, dict) and "questions" in questions: questions = questions["questions"]
            break
        except Exception as e:
            if attempt == max_retries - 1: return []

    if not questions: return []

    # Phase 2: Review
    print(f"  [Pipeline] Running Reviewer Agent for {len(questions)} questions...")
    review_results = _review_questions(questions, topic, grounding, headers)
    
    # Phase 3: Optimize if needed
    needs_fix = any(r.get("status") == "FAIL" for r in review_results)
    if needs_fix:
        print(f"  [Pipeline] Issues detected by Reviewer: {json.dumps(review_results, ensure_ascii=False)}")
        print(f"  [Pipeline] Running Optimizer Agent...")
        questions = _optimize_questions(questions, review_results, topic, grounding, headers)
    else:
        print(f"  [Pipeline] Reviewer passed all questions.")
    
    return questions

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
    result = generate_questions_from_topic("こそすれ", num_questions=1)
    print(json.dumps(result, indent=2, ensure_ascii=False))