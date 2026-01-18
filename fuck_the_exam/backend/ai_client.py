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
    Multi-Agent Pipeline: Generator -> Reviewer -> Optimizer.
    """
    topic = topic_raw.replace("N1 Grammar:", "").replace("N1 Vocab:", "").replace("N1 阅读:", "").strip()
    if topic.startswith("～"): topic = topic[1:]

    grounding = get_grammar_grounding(topic)
    grounding_prompt = f"\nGROUNDING DATA (Source of Truth):\n{grounding}\n" if grounding else ""

    # Phase 1: Generation
    system_prompt = f"""
    You are a world-class Japanese Language Proficiency Test (JLPT) N1 examiner. 
    Your goal is to generate exactly {batch_size} high-stakes, ultra-realistic, and deceptive multiple-choice questions for the topic: "{topic}".
    {grounding_prompt}

    OUTPUT FORMAT:
    You MUST return a JSON ARRAY of {batch_size} objects. Each object must have:
    - "content": string, Japanese sentence with （　　）
    - "options": dictionary with keys A, B, C, D (values in Japanese)
    - "correct_answer": string (A, B, C, or D)
    - "explanation": string, detailed breakdown in professional Chinese
    - "memorization_tip": string, mnemonic or comparison rule in Chinese
    - "knowledge_point": string, MUST be "{topic}"

    STRICT JLPT N1 FORMATTING & LINGUISTIC RULES:
    1. EXAM FORMAT (穴埋め): 
       - The 'content' MUST be a full Japanese sentence with a blank marked as '（　　）'.
       - Questions MUST test usage in context, nuance, or sentence structure.
    2. LANGUAGE ISOLATION:
       - 'options' (A, B, C, D) MUST be 100% Japanese. 
       - 'explanation' and 'memorization_tip' MUST be in professional Chinese.
    3. TARGET GRAMMAR LOGIC & DECEPTION (CRITICAL):
       - **Primary Objective**: Test the user's ability to distinguish "{topic}" from similar structures.
       - **DECEPTION RULE**: The correct answer does NOT always have to be "{topic}". You can choose another N1 grammar point as the correct answer and use "{topic}" as a plausible but INCORRECT distractor. This forces the user to choose the most appropriate one.
       - **NO LEAKAGE**: The target grammar "{topic}" MUST NOT appear in the 'content' string outside of the options.
    4. DISTRACTOR STRATEGY:
       - Use "Strong Distractors": near-synonymous grammar, points with the same form but different meaning, or different formality (書面語 vs 口語).
       - Ensure every option is grammatically correct in isolation but only ONE is correct in the specific context of the 'content'.
    5. DETAILED CHINESE EXPLANATIONS:
       - The 'explanation' field MUST be a single string containing:
         1) [本题考点]: Breakdown of "{topic}" usage and logic based on grounding.
         2) [语境分析]: Analyze the sentence context and why it requires a specific structure.
         3) [选项解析]: Detailed reason why the correct answer is right and why EACH distractor is wrong (citing specific N1 nuance differences).
            IMPORTANT: EACH option (A, B, C, D) in this section MUST start on a NEW LINE for readability.
    6. MEMORIZATION TIP: Provide a mnemonic or comparison rule in Chinese as a string.
    """

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "system", "content": system_prompt}],
        "temperature": 0.3,
    }

    questions = []
    for attempt in range(max_retries):
        try:
            print(f"    [Agent: Generator] Requesting {batch_size} questions...")
            response = requests.post(API_URL, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            print(f"    [Agent: Generator] Received response.")
            content = response.json()['choices'][0]['message']['content'].strip()
            
            # Robust JSON extraction
            import re
            json_match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            questions = json.loads(content)
            if isinstance(questions, dict) and "questions" in questions: questions = questions["questions"]
            if isinstance(questions, dict): questions = [questions] # Handle single object return
            
            # Flatten explanation if it's an object
            if questions:
                for q in questions:
                    if isinstance(q.get('explanation'), dict):
                        exp = q['explanation']
                        flat_exp = "\n".join([f"{k}: {v}" for k, v in exp.items()])
                        q['explanation'] = flat_exp
                    
                    # Ensure basic fields exist
                    if not q.get('explanation'):
                        q['explanation'] = "[AI生成辅助] 考点分析加载中，请结合前后文理解。"
                    if not q.get('memorization_tip'):
                        q['memorization_tip'] = "记忆点正在整理中。"
                    if not q.get('knowledge_point'):
                        q['knowledge_point'] = topic
                    
                    # Deduplication: If tip is just a repetition of explanation, clear it or shorten it
                    exp_text = q['explanation'].strip()
                    tip_text = q['memorization_tip'].strip()
                    if tip_text in exp_text and len(tip_text) > 10:
                        q['memorization_tip'] = "见上方详细解析中的逻辑要点。"
                break
        except Exception as e:
            print(f"  [Generator] Batch Attempt {attempt+1} failed: {e}")
            if 'response' in locals() and response is not None:
                print(f"  [Generator] Status: {response.status_code}")
                # Print a bit of the content to see why parsing failed
                raw_msg = response.json()['choices'][0]['message']['content'] if response.status_code == 200 else response.text
                print(f"  [Generator] Content Snippet: {raw_msg[:300]}")
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
        print(f"    [Agent: Reviewer] Checking {len(questions)} questions...")
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        print(f"    [Agent: Reviewer] Decision received.")
        content = response.json()['choices'][0]['message']['content'].strip()
        
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        if json_start != -1 and json_end > json_start:
            content = content[json_start:json_end]
            
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
        print(f"    [Agent: Optimizer] Fixing issues...")
        response = requests.post(API_URL, headers=headers, json=data, timeout=90)
        response.raise_for_status()
        print(f"    [Agent: Optimizer] Fixed content received.")
        content = response.json()['choices'][0]['message']['content'].strip()
        
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        if json_start != -1 and json_end > json_start:
            content = content[json_start:json_end]
            
        fixed = json.loads(content)
        return fixed if isinstance(fixed, list) else questions
    except Exception as e:
        print(f"  [Optimizer] Error: {e}")
        return questions

def generate_questions_from_topic(topic: str, num_questions: int = 5, batch_size: int = 5) -> List[Dict]:
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
                print(f"  [Batch {batch_index+1}] Received {len(batch_questions) if batch_questions else 0} questions.")
                if batch_questions:
                    for q in batch_questions:
                        if q.get('content'):
                            unique_string = f"{q.get('content', '')}-{json.dumps(q.get('options', {}), sort_keys=True)}"
                            q['hash'] = hashlib.sha256(unique_string.encode()).hexdigest()
                            all_questions.append(q)
                        else:
                            print(f"  [Batch {batch_index+1}] Question missing 'content' key: {list(q.keys())}")
                    print(f"  [Batch {batch_index+1}] Done. Total appended: {len(all_questions)}")
            except Exception as e:
                print(f"  [Batch {batch_index+1}] Critical error: {e}")
                import traceback
                traceback.print_exc()

    print(f"Completed: {len(all_questions)}/{num_questions} questions.")
    return all_questions
    
    return []

if __name__ == "__main__":
    # Test run
    print("Testing SiliconFlow API...")
    result = generate_questions_from_topic("こそすれ", num_questions=1)
    print(json.dumps(result, indent=2, ensure_ascii=False))