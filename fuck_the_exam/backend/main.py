import json
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

from . import models, database, ai_client
from .services.markdown_service import MarkdownService
from .database import engine
from pydantic import BaseModel, Json

# Ensure DB tables are created
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Japanese N1 Quiz App")

# Initialize Markdown Service
markdown_service = MarkdownService(base_path=os.path.join(os.getcwd(), "knowledge_base"))

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://192.168.0.39:3000", # Mobile access
    "*", # Allow all for local dev flexibility
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class QuestionBase(BaseModel):
    content: str
    options: Dict[str, str] # Changed to Dict for JSON options
    correct_answer: str
    explanation: Optional[str] = None
    knowledge_point: Optional[str] = None
    exam_type: str = "N1"

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    hash: Optional[str] = None

    class Config:
        from_attributes = True
        # Custom validator or config might be needed if Pydantic doesn't auto-convert JSON str to dict
        # But for response model, we need to ensure the DB text is parsed.
        # SQLAlchemy's JSON type (or our Text column) needs handling.

class AnswerSubmit(BaseModel):
    question_id: int
    selected_answer: str

class WrongQuestion(BaseModel):
    id: int
    question: Question
    review_count: int

    class Config:
        from_attributes = True

class GenerateRequest(BaseModel):
    topic: str
    num_questions: int = 5

# --- API Endpoints ---

@app.on_event("startup")
def on_startup():
    database.create_db_and_tables()
    ingest_json_questions()

def ingest_json_questions():
    """
    Scans backend/json_questions for .json files and imports them.
    """
    json_dir = os.path.join(os.path.dirname(__file__), "json_questions")
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
        print(f"Created directory: {json_dir}")
        return

    import glob
    import hashlib
    
    files = glob.glob(os.path.join(json_dir, "*.json"))
    db = database.SessionLocal()
    
    try:
        count = 0
        for json_file in files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, dict): # Handle single object or wrapped list
                     data = [data]
                
                for q_data in data:
                    # Normalize options if they are flat option_a, option_b etc.
                    if 'options' not in q_data and 'option_a' in q_data:
                        q_data['options'] = {
                            'A': q_data.get('option_a'),
                            'B': q_data.get('option_b'),
                            'C': q_data.get('option_c'),
                            'D': q_data.get('option_d')
                        }
                    
                    # Normalize field names (support both formats)
                    if 'question' in q_data and 'content' not in q_data:
                        q_data['content'] = q_data['question']
                    if 'answer' in q_data and 'correct_answer' not in q_data:
                        q_data['correct_answer'] = q_data['answer']

                    # Validate required fields
                    if 'content' not in q_data or 'options' not in q_data or 'correct_answer' not in q_data:
                        print(f"Skipping invalid question in {json_file}: Missing fields")
                        continue

                    # Generate Hash if missing
                    if 'hash' not in q_data:
                        unique_string = f"{q_data['content']}-{json.dumps(q_data['options'], sort_keys=True)}"
                        q_data['hash'] = hashlib.sha256(unique_string.encode()).hexdigest()
                    
                    # Check Duplicate
                    exists = db.query(models.Question).filter(models.Question.hash == q_data['hash']).first()
                    if not exists:
                        db_q = models.Question(
                            content=q_data['content'],
                            options=json.dumps(q_data['options'], ensure_ascii=False) if isinstance(q_data['options'], (dict, list)) else q_data['options'],
                            correct_answer=q_data['correct_answer'],
                            explanation=q_data.get('explanation'),
                            knowledge_point=q_data.get('knowledge_point'),
                            exam_type=q_data.get('exam_type', 'N1'),
                            hash=q_data['hash']
                        )
                        db.add(db_q)
                        count += 1
                    else:
                        # Update existing question if new data has explanation/knowledge_point
                        updated = False
                        new_explanation = q_data.get('explanation')
                        new_knowledge_point = q_data.get('knowledge_point')
                        
                        if new_explanation and not exists.explanation:
                            exists.explanation = new_explanation
                            updated = True
                        if new_knowledge_point and not exists.knowledge_point:
                            exists.knowledge_point = new_knowledge_point
                            updated = True
                        
                        if updated:
                            print(f"Updated question {exists.id} with new metadata")
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        db.commit()
        print(f"Loaded {count} new questions from JSON files.")
    finally:
        db.close()

@app.post("/api/quiz/generate")
def generate_quiz(req: GenerateRequest, db: Session = Depends(database.get_db)):
    """
    Generates N1 questions via AI, deduplicates, and saves to DB.
    """
    # 1. Generate questions from AI
    generated_questions = ai_client.generate_questions_from_topic(req.topic, req.num_questions)
    
    if not generated_questions:
        raise HTTPException(status_code=500, detail="Failed to generate questions from AI.")

    saved_questions = []

    for q_data in generated_questions:
        # Check for duplicates using hash
        if 'hash' not in q_data:
             # If AI client didn't generate hash (e.g. error), skip or re-hash
             continue
        
        existing_q = db.query(models.Question).filter(models.Question.hash == q_data['hash']).first()
        
        if existing_q:
            saved_questions.append(existing_q)
        else:
            # Create new question
            # Note: options dict needs to be dumped to string for SQLite Text column if not using JSON type
            db_q = models.Question(
                content=q_data['content'],
                options=json.dumps(q_data['options'], ensure_ascii=False),
                correct_answer=q_data['correct_answer'],
                explanation=q_data.get('explanation'),
                knowledge_point=q_data.get('knowledge_point'),
                exam_type="N1",
                hash=q_data['hash']
            )
            db.add(db_q)
            db.flush() # Get ID
            saved_questions.append(db_q)
    
    db.commit()
    
    # Return questions with parsed options
    return [
        {
            "id": q.id,
            "content": q.content,
            "options": json.loads(q.options) if isinstance(q.options, str) else q.options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "knowledge_point": q.knowledge_point
        } for q in saved_questions
    ]

@app.get("/api/questions", response_model=List[Question])
def get_questions(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    questions = db.query(models.Question).offset(skip).limit(limit).all()
    # Manual parsing of options string to dict for response
    results = []
    for q in questions:
        q_dict = q.__dict__.copy()
        if isinstance(q.options, str):
            q_dict['options'] = json.loads(q.options)
        results.append(Question(**q_dict))
    return results

@app.get("/api/quiz/study")
def get_study_session(limit_new: int = 5, limit_review: int = 10, db: Session = Depends(database.get_db)):
    """
    Generates a study session combining:
    1. Due SRS reviews (from WrongQuestion).
    2. New questions (never attempted correctly).
    """
    # Re-scan JSON files for new questions on each study request
    ingest_json_questions()
    
    # 1. Get Due Reviews
    now = datetime.now()
    due_reviews = db.query(models.WrongQuestion)\
        .filter(models.WrongQuestion.next_review_at <= now)\
        .order_by(models.WrongQuestion.next_review_at)\
        .limit(limit_review)\
        .all()
    
    review_structure = []
    for w in due_reviews:
        q = w.question
        # Parse options if str
        options = json.loads(q.options) if isinstance(q.options, str) else q.options
        q_dict = {
            "id": q.id,
            "content": q.content,
            "options": options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "knowledge_point": q.knowledge_point,
            "is_review": True
        }
        review_structure.append(q_dict)

    # 2. Get New Questions
    # Logic: Questions that do not have a corresponding AnswerAttempt(is_correct=1)
    
    subquery = db.query(models.AnswerAttempt.question_id).filter(models.AnswerAttempt.is_correct == 1)
    new_qs = db.query(models.Question)\
        .filter(~models.Question.id.in_(subquery))\
        .limit(limit_new)\
        .all()

    new_structure = []
    for q in new_qs:
        options = json.loads(q.options) if isinstance(q.options, str) else q.options
        q_dict = {
            "id": q.id,
            "content": q.content,
            "options": options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "knowledge_point": q.knowledge_point
        }
        new_structure.append(q_dict)
    
    return review_structure + new_structure

@app.post("/api/questions/{question_id}/submit")
def submit_answer_and_log(question_id: int, answer: AnswerSubmit, db: Session = Depends(database.get_db)):
    """
    Checks answer, updates stats, and logs to Markdown.
    """
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    import logging
    logger = logging.getLogger("uvicorn")
    
    # Normalize strings
    db_ans = db_question.correct_answer.strip().upper()
    user_ans = answer.selected_answer.strip().upper()
    
    is_correct = db_ans == user_ans
    
    logger.info(f"DEBUG_CHECK: QID={question_id}")
    logger.info(f"DB_Answer='{db_ans}' (Raw: {repr(db_question.correct_answer)})")
    logger.info(f"User_Answer='{user_ans}' (Raw: {repr(answer.selected_answer)})")
    logger.info(f"IsCorrect={is_correct}")
    logger.info(f"Explanation Len: {len(db_question.explanation) if db_question.explanation else 0}")

    # 1. Record Attempt in DB
    attempt = models.AnswerAttempt(
        question_id=question_id,
        selected_answer=answer.selected_answer,
        is_correct=1 if is_correct else 0
    )
    db.add(attempt)

    # 2. Update Wrong Question Table (SRS Logic)
    from datetime import datetime, timedelta
    
    wrong_q = db.query(models.WrongQuestion).filter(models.WrongQuestion.question_id == question_id).first()

    if not is_correct:
        # User got it WRONG -> Reset/Add to SRS queue
        if not wrong_q:
            wrong_q = models.WrongQuestion(
                question_id=question_id,
                review_count=0,
                interval=1,
                ease_factor=250,
                next_review_at=datetime.now() + timedelta(days=1)
            )
            db.add(wrong_q)
        else:
            # Forgot it! Reset interval
            wrong_q.interval = 1
            wrong_q.ease_factor = max(130, wrong_q.ease_factor - 20)
            wrong_q.next_review_at = datetime.now() + timedelta(days=1)
        
        if wrong_q.review_count is None:
            wrong_q.review_count = 0
        wrong_q.review_count += 1
        
        # 3. Log to Markdown (Black Book)
        markdown_service.log_wrong_question(db_question)

    else:
        # User got it RIGHT
        if wrong_q:
            if wrong_q.interval is None: wrong_q.interval = 1
            if wrong_q.ease_factor is None: wrong_q.ease_factor = 250
            
            # It was in the review queue, process SRS success
            # Algorithm: I(n) = I(n-1) * EF
            new_interval = int(wrong_q.interval * (wrong_q.ease_factor / 100.0))
            if new_interval <= wrong_q.interval:
                 new_interval = wrong_q.interval + 1 # Ensure growth
            
            wrong_q.interval = new_interval
            wrong_q.next_review_at = datetime.now() + timedelta(days=new_interval)

    db.commit()
    
    # 4. Return result with explanation
    return {
        "is_correct": is_correct,
        "correct_answer": db_question.correct_answer,
        "explanation": db_question.explanation or "暂无解析"
    }

@app.post("/api/quiz/finish")
def finish_quiz_session(topic: str, session_data: List[Dict], db: Session = Depends(database.get_db)):
    """
    Logs the entire quiz session to a Markdown file.
    session_data expected format: [{question_id: 1, selected_answer: "A", is_correct: True}, ...]
    """
    # Create a list of (Question, Result) tuples for the logger
    log_data_questions = []
    log_data_results = []

    for item in session_data:
        q = db.query(models.Question).filter(models.Question.id == item['question_id']).first()
        if q:
            # Parse options for the logger if needed, though logger might raw access
            log_data_questions.append(q)
            log_data_results.append(item)

    markdown_service.log_quiz_session(topic, log_data_questions, log_data_results)
    
    return {"message": "Session logged successfully"}

@app.get("/api/wrong-questions")
def get_wrong_questions_api(db: Session = Depends(database.get_db)):
    wqs = db.query(models.WrongQuestion).all()
    results = []
    for w in wqs:
        q = w.question
        q_dict = q.__dict__.copy()
        if isinstance(q.options, str):
            q_dict['options'] = json.loads(q.options)
        
        results.append({
            "id": w.id,
            "question": Question(**q_dict),
            "review_count": w.review_count
        })
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
