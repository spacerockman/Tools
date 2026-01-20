import json
import os
import re
import hashlib
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

import secrets
from . import models, database, ai_client
from .database import engine, SessionLocal
from .services.markdown_service import MarkdownService
from .services.knowledge_service import KnowledgeService
from .services.backup_service import BackupService
from .services.analysis_service import AnalysisService
from .autogen_service import AutoGenService
from pydantic import BaseModel, Json

# Ensure DB tables are created
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Japanese N1 Quiz App")

autogen_service_instance = None

# Initialize Services
markdown_service = MarkdownService(base_path=os.path.join(os.getcwd(), "knowledge_base"))
knowledge_service = KnowledgeService(base_path=os.path.join(os.getcwd(), "backend"))
backup_service = BackupService(
    db_path=os.path.join(os.getcwd(), "backend", "n1_app.db"),
    backup_dir=os.path.join(os.getcwd(), "backend", "backups")
)
analysis_service = AnalysisService(ai_client=ai_client)

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:23333",
    "http://192.168.0.39:3000", # Mobile access
    "http://192.168.0.39:23333",
    "*", # Allow all for local dev flexibility
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- User Management Dependency ---
def get_current_user_id(x_user_id: Optional[int] = Header(None)):
    if x_user_id is None:
        return 1 # Fallback to default user
    return x_user_id

# --- Pydantic Models ---

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    content: str
    options: Dict[str, str] # Changed to Dict for JSON options
    correct_answer: str
    explanation: Optional[str] = None
    memorization_tip: Optional[str] = None
    knowledge_point: Optional[str] = None
    exam_type: str = "N1"

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    hash: Optional[str] = None
    is_favorite: bool = False

    class Config:
        from_attributes = True

class AnswerSubmit(BaseModel):
    question_id: int
    selected_answer: str
    quality: Optional[int] = None # SM-2 Quality (0-5) or simplified (1-4)

class WrongQuestion(BaseModel):
    id: int
    question: Question
    review_count: int

    class Config:
        from_attributes = True

class GenerateRequest(BaseModel):
    topic: str
    num_questions: int = 5
    exam_type: str = "N1"

class StatsResponse(BaseModel):
    total_answered: int
    correct_count: int
    wrong_count: int
    daily_stats: List[Dict[str, Any]]
    top_wrong_points: List[Dict[str, Any]]

class QuizSessionPayload(BaseModel):
    session_key: Optional[str] = "default"
    topic: Optional[str] = None
    questions: List[Dict[str, Any]]
    results: List[Any]
    current_index: int = 0
# --- Auth Utils ---
def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    phash = hashlib.sha256((password + salt).encode()).hexdigest()
    return phash, salt

def verify_password(password: str, salt: str, phash: str):
    return hash_password(password, salt)[0] == phash

# --- API Endpoints ---

@app.on_event("startup")
def on_startup():
    global autogen_service_instance
    database.create_db_and_tables()
    # Migration: Add is_favorite column if it doesn't exist
    try:
        from sqlalchemy import text
        db = database.SessionLocal()
        db.execute(text('ALTER TABLE questions ADD COLUMN is_favorite BOOLEAN DEFAULT 0'))
        db.commit()
        db.close()
        print("Migration: Added is_favorite column to questions table.")
    except Exception as e:
        # Probable cause: column already exists
        pass

    # Migration: Add password columns to users
    try:
        from sqlalchemy import text
        db = database.SessionLocal()
        db.execute(text('ALTER TABLE users ADD COLUMN password_hash VARCHAR(128)'))
        db.execute(text('ALTER TABLE users ADD COLUMN salt VARCHAR(32)'))
        db.commit()
        db.close()
        print("Migration: Added password columns to users table.")
    except Exception as e:
        pass
    
    ingest_json_questions()

    # Data Recovery: If no wrong questions but backup exists, restore from JSON.
    db_rec = SessionLocal()
    try:
        if db_rec.query(models.WrongQuestion).count() == 0:
            restored = backup_service.restore_progress_from_json(db_rec)
            if restored > 0:
                print(f"Recovery: Restored {restored} SRS records from backup.")
    except Exception as e:
        print(f"Recovery failed: {e}")
    finally:
        db_rec.close()

    # Start the autogen service
    autogen_service_instance = AutoGenService(database.SessionLocal)
    autogen_service_instance.start()

@app.on_event("shutdown")
def on_shutdown():
    global autogen_service_instance
    if autogen_service_instance:
        autogen_service_instance.stop()

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
    
    # Scan both n1/ and databricks/ subfolders
    base_json_dir = os.path.join(os.path.dirname(__file__), "json_questions")
    files = []
    for mode in ["n1", "databricks"]:
        mode_dir = os.path.join(base_json_dir, mode)
        if os.path.exists(mode_dir):
            files.extend([(f, mode.upper()) for f in glob.glob(os.path.join(mode_dir, "*.json"))])
    
    db = database.SessionLocal()
    
    try:
        count = 0
        for json_file, mode_type in files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                original_is_dict = isinstance(data, dict)
                file_modified = False
                    
                if isinstance(data, dict): 
                     data = [data]
                
                default_point = os.path.basename(json_file).replace('.json', '')

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

                    # Backfill knowledge_point from filename if missing
                    if not q_data.get('knowledge_point'):
                        q_data['knowledge_point'] = default_point
                        file_modified = True

                    # Validate required fields
                    if 'content' not in q_data or 'options' not in q_data or 'correct_answer' not in q_data:
                        continue # Silent skip

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
                            memorization_tip=q_data.get('memorization_tip'),
                            knowledge_point=q_data.get('knowledge_point') or os.path.basename(json_file).replace('.json', ''),
                            exam_type=mode_type,
                            hash=q_data['hash']
                        )
                        db.add(db_q)
                        count += 1
                    else:
                         # Sync/Update fields even if question exists
                         if q_data.get('memorization_tip'):
                             exists.memorization_tip = q_data.get('memorization_tip')
                         if q_data.get('knowledge_point'):
                             exists.knowledge_point = q_data.get('knowledge_point')
                         if q_data.get('explanation') and (not exists.explanation or exists.explanation == "暂无解析"):
                             exists.explanation = q_data.get('explanation')
                if file_modified:
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data[0] if original_is_dict else data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        db.commit()
        print(f"Loaded {count} new questions from JSON files.")
    finally:
        db.close()

def get_safe_filename(topic: str) -> str:
    """
    Consistently sanitizes a topic name for use as a filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "", topic).replace(" ", "_") + ".json"

def save_generated_questions_to_file(topic: str, questions: List[Dict], exam_type: str = "N1"):
    """
    Saves generated questions to backend/json_questions/{topic}.json
    Appends if file exists.
    """
    filename = get_safe_filename(topic)
    mode_subfolder = (exam_type or "N1").lower()
    json_dir = os.path.join(os.path.dirname(__file__), "json_questions", mode_subfolder)
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
        
    filepath = os.path.join(json_dir, filename)
    
    existing_data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                    if isinstance(existing_data, dict):
                        existing_data = [existing_data]
        except Exception as e:
            print(f"Error reading existing file {filepath}: {e}")
            existing_data = []

    # Dedup against file content (simple hash check)
    existing_hashes = set()
    for q in existing_data:
        unique_string = f"{q.get('content')}-{json.dumps(q.get('options'), sort_keys=True)}"
        h = hashlib.sha256(unique_string.encode()).hexdigest()
        existing_hashes.add(h)

    new_questions = []
    for q in questions:
        # Client might not generate hash, let's gen it just for check
        unique_string = f"{q.get('content')}-{json.dumps(q.get('options'), sort_keys=True)}"
        h = hashlib.sha256(unique_string.encode()).hexdigest()
        if h not in existing_hashes:
            new_questions.append(q)
            existing_hashes.add(h)
    
    if new_questions:
        final_data = existing_data + new_questions
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(new_questions)} new questions to {filepath}")

@app.get("/api/users", response_model=List[User])
def get_users(db: Session = Depends(database.get_db)):
    return db.query(models.User).all()

@app.post("/api/users", response_model=User)
def create_user(user_data: UserCreate, db: Session = Depends(database.get_db)):
    # Check if user already exists
    existing = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    phash, salt = hash_password(user_data.password)
    new_user = models.User(
        username=user_data.username,
        password_hash=phash,
        salt=salt
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/login", response_model=User)
def login_user(payload: UserLogin, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Handle legacy users with no password
    if not db_user.password_hash:
        return db_user

    if not verify_password(payload.password, db_user.salt, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    return db_user

@app.post("/api/quiz/generate")
def generate_quiz(req: GenerateRequest, db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    """
    Generates N1 questions via AI, deduplicates, saves to file, and saves to DB.
    """
    print(f"--- API CALL: generate_quiz for topic '{req.topic}' ---")
    # 1. Generate questions from AI
    generated_questions = ai_client.generate_questions_from_topic(req.topic, req.num_questions)
    
    if not generated_questions:
        raise HTTPException(status_code=500, detail="Failed to generate questions from AI.")

    # 2. Save to File
    save_generated_questions_to_file(req.topic, generated_questions, req.exam_type)

    # 3. Save to DB
    saved_questions = []

    for q_data in generated_questions:
        # Ensure hash
        if 'hash' not in q_data:
             unique_string = f"{q_data['content']}-{json.dumps(q_data['options'], sort_keys=True)}"
             q_data['hash'] = hashlib.sha256(unique_string.encode()).hexdigest()
        
        existing_q = db.query(models.Question).filter(models.Question.hash == q_data['hash']).first()
        
        if existing_q:
            saved_questions.append(existing_q)
        else:
            db_q = models.Question(
                content=q_data['content'],
                options=json.dumps(q_data['options'], ensure_ascii=False),
                correct_answer=q_data['correct_answer'],
                explanation=q_data.get('explanation'),
                memorization_tip=q_data.get('memorization_tip'),
                knowledge_point=q_data.get('knowledge_point') or req.topic,
                exam_type=req.exam_type,
                hash=q_data['hash']
            )
            db.add(db_q)
            db.flush() 
            saved_questions.append(db_q)
    
    db.commit()

    # 4. Filter mastered questions (unless favorite)
    # Mastered = exists a correct attempt BY THIS USER
    
    final_questions = []
    for q in saved_questions:
        # Check if mastered BY THIS USER
        is_mastered = db.query(models.AnswerAttempt).filter(
            models.AnswerAttempt.question_id == q.id,
            models.AnswerAttempt.user_id == user_id,
            models.AnswerAttempt.is_correct == 1
        ).first() is not None
        
        is_favorite = db.query(models.UserFavorite).filter(
            models.UserFavorite.user_id == user_id,
            models.UserFavorite.question_id == q.id
        ).first() is not None
        
        if not is_mastered or is_favorite:
            final_questions.append((q, is_favorite))
    
    return [
        {
            "id": q.id,
            "content": q.content,
            "options": json.loads(q.options) if isinstance(q.options, str) else q.options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "memorization_tip": q.memorization_tip,
            "knowledge_point": q.knowledge_point,
            "is_favorite": fav
        } for q, fav in final_questions
    ]

@app.get("/api/stats", response_model=StatsResponse)
def get_stats(exam_type: str = "N1", db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    # Total Answered by this user in this mode
    total = db.query(models.AnswerAttempt).join(models.Question)\
        .filter(models.AnswerAttempt.user_id == user_id, models.Question.exam_type == exam_type).count()
    
    correct = db.query(models.AnswerAttempt).join(models.Question)\
        .filter(
            models.AnswerAttempt.user_id == user_id,
            models.AnswerAttempt.is_correct == 1,
            models.Question.exam_type == exam_type
        ).count()
    wrong = total - correct

    # Daily Stats (Last 7 days) for this user in this mode
    daily_stats = []
    rows = db.query(
        func.date(models.AnswerAttempt.attempted_at).label('date'),
        func.sum(models.AnswerAttempt.is_correct).label('correct'),
        func.count(models.AnswerAttempt.id).label('total')
    ).join(models.Question)\
     .filter(models.AnswerAttempt.user_id == user_id, models.Question.exam_type == exam_type)\
     .group_by(func.date(models.AnswerAttempt.attempted_at))\
     .order_by(func.date(models.AnswerAttempt.attempted_at).desc())\
     .limit(7).all()

    for r in rows:
        daily_stats.append({
            "date": r.date,
            "correct": r.correct,
            "wrong": r.total - r.correct
        })
    daily_stats.reverse()

    # Top Wrong Knowledge Points in this mode
    wrong_points = db.query(
        models.Question.knowledge_point,
        func.count(models.AnswerAttempt.id).label('count')
    ).join(models.AnswerAttempt, models.Question.id == models.AnswerAttempt.question_id) \
     .filter(
         models.AnswerAttempt.is_correct == 0, 
         models.AnswerAttempt.user_id == user_id,
         models.Question.exam_type == exam_type
     ) \
     .group_by(models.Question.knowledge_point) \
     .order_by(func.count(models.AnswerAttempt.id).desc()) \
     .limit(5).all()

    top_wrong = [{"point": p[0], "count": p[1]} for p in wrong_points if p[0]]

    return {
        "total_answered": total,
        "correct_count": correct,
        "wrong_count": wrong,
        "daily_stats": daily_stats,
        "top_wrong_points": top_wrong
    }

@app.get("/api/stats/analysis")
def get_ai_analysis(db: Session = Depends(database.get_db)):
    """
    Returns high-level diagnostic report generated locally.
    Note: This uses deterministic logic and is token-free.
    """
    return analysis_service.generate_diagnostic_report(db)

@app.get("/api/suggestions")
def get_suggestions(exam_type: str = "N1", db: Session = Depends(database.get_db)):
    # Parse markdown files and return list
    try:
        # Get raw suggestions from service (mode-aware for MD files)
        all_points = knowledge_service.get_all_knowledge_points(exam_type=exam_type)
        
        # Further refine: Only show points that have questions in the DB for this exam_type
        # OR if it's N1 and from the MD file (to allow generating questions for them)
        db_points = db.query(models.Question.knowledge_point)\
            .filter(models.Question.exam_type == exam_type)\
            .distinct().all()
        db_point_names = {p[0] for p in db_points if p[0]}
        
        filtered = []
        for p in all_points:
            # If it has questions in DB, definitely keep it
            if p['point'] in db_point_names:
                filtered.append(p)
            # If it's N1 and from MD, keep it (allows user to see topics to generate)
            elif exam_type == "N1" and p.get('source_file', '').endswith('.md'):
                filtered.append(p)
        
        return filtered
    except Exception as e:
        print(f"Error getting suggestions: {e}")
        return []

@app.get("/api/knowledge/counts")
def get_knowledge_counts(exam_type: str = "N1", db: Session = Depends(database.get_db)):
    """
    Returns a list of {point: str, count: int} filtered by exam_type.
    """
    try:
        results = db.query(
            models.Question.knowledge_point, 
            func.count(models.Question.id)
        ).filter(models.Question.exam_type == exam_type)\
         .group_by(models.Question.knowledge_point).all()
        
        return [{"point": r[0] or "未分类", "count": r[1]} for r in results]
    except Exception as e:
        print(f"Error getting counts: {e}")
        return []

@app.get("/api/knowledge/{name}")
def get_knowledge_detail(name: str):
    try:
        points = knowledge_service.get_all_knowledge_points()
        for p in points:
            if p['point'] == name:
                return p
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questions", response_model=List[Question])
def get_questions(topic: str = None, exam_type: str = "N1", skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    query = db.query(models.Question).filter(models.Question.exam_type == exam_type)
    if topic:
        query = query.filter(models.Question.knowledge_point == topic)
    
    if limit > 0:
        query = query.offset(skip).limit(limit)
    elif skip > 0:
        query = query.offset(skip)
        
    questions = query.all()
    results = []
    
    # Get favorite IDs for this user
    favorite_ids = set(r[0] for r in db.query(models.UserFavorite.question_id).filter(models.UserFavorite.user_id == user_id).all())
    
    for q in questions:
        q_dict = q.__dict__.copy()
        if isinstance(q.options, str):
            q_dict['options'] = json.loads(q.options)
        q_dict['is_favorite'] = q.id in favorite_ids
        results.append(Question(**q_dict))
    return results

@app.post("/api/favorites/toggle/{question_id}")
def toggle_favorite(question_id: int, db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    existing = db.query(models.UserFavorite).filter(
        models.UserFavorite.user_id == user_id,
        models.UserFavorite.question_id == question_id
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()
        return {"is_favorite": False}
    else:
        new_fav = models.UserFavorite(user_id=user_id, question_id=question_id)
        db.add(new_fav)
        db.commit()
        return {"is_favorite": True}

@app.get("/api/quiz/session")
def get_quiz_session(session_key: str = "default", db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    session = db.query(models.QuizSession).filter(
        models.QuizSession.session_key == session_key,
        models.QuizSession.user_id == user_id
    ).first()
    if not session:
        return {"exists": False}

    return {
        "exists": True,
        "session_key": session.session_key,
        "topic": session.topic,
        "questions": json.loads(session.questions_json),
        "results": json.loads(session.results_json),
        "current_index": session.current_index,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None
    }

@app.post("/api/quiz/session")
def save_quiz_session(payload: QuizSessionPayload, db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    session_key = payload.session_key or "default"
    existing = db.query(models.QuizSession).filter(
        models.QuizSession.session_key == session_key,
        models.QuizSession.user_id == user_id
    ).first()

    if not existing:
        existing = models.QuizSession(session_key=session_key, user_id=user_id)
        db.add(existing)

    existing.topic = payload.topic
    existing.questions_json = json.dumps(payload.questions, ensure_ascii=False)
    existing.results_json = json.dumps(payload.results, ensure_ascii=False)
    existing.current_index = payload.current_index
    db.commit()

    return {"message": "Session saved", "session_key": session_key}

@app.delete("/api/quiz/session")
def delete_quiz_session(session_key: str = "default", db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    session = db.query(models.QuizSession).filter(
        models.QuizSession.session_key == session_key,
        models.QuizSession.user_id == user_id
    ).first()
    if not session:
        return {"message": "Session not found"}

    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}

@app.get("/api/quiz/study")
def get_study_session(limit_new: int = 5, limit_review: int = 10, exam_type: str = "N1", db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    ingest_json_questions()
    
    now = datetime.now()
    due_reviews = db.query(models.WrongQuestion).join(models.Question)\
        .filter(models.WrongQuestion.user_id == user_id, 
                models.Question.exam_type == exam_type,
                models.WrongQuestion.next_review_at <= now)\
        .order_by(models.WrongQuestion.next_review_at)\
        .limit(limit_review)\
        .all()
    
    review_structure = []
    for w in due_reviews:
        q = w.question
        options = json.loads(q.options) if isinstance(q.options, str) else q.options
        q_dict = {
            "id": q.id,
            "content": q.content,
            "options": options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "memorization_tip": q.memorization_tip,
            "knowledge_point": q.knowledge_point,
            "is_review": True,
            "srs_interval": w.interval,
            "srs_next_review": w.next_review_at.isoformat() if w.next_review_at else None
        }
        review_structure.append(q_dict)

    # Answered questions by this user
    answered_subquery = db.query(models.AnswerAttempt.question_id).filter(
        models.AnswerAttempt.user_id == user_id,
        models.AnswerAttempt.is_correct == 1
    )
    
    # Favorite IDs for this user
    favorite_ids = db.query(models.UserFavorite.question_id).filter(models.UserFavorite.user_id == user_id)

    new_qs = db.query(models.Question)\
        .filter(models.Question.exam_type == exam_type)\
        .filter((~models.Question.id.in_(answered_subquery)) | (models.Question.id.in_(favorite_ids)))\
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
            "memorization_tip": q.memorization_tip,
            "knowledge_point": q.knowledge_point
        }
        new_structure.append(q_dict)
    
    return review_structure + new_structure

@app.get("/api/quiz/gap")
def get_gap_quiz(target_total: int = 20, num_per_point: int = 2, exam_type: str = "N1", db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    """
    Selects a mix of:
    1. NEVER attempted questions.
    2. Favorited questions.
    3. Wrong questions (currently in SRS).
    
    Picks num_per_point from each point until target_total is reached.
    """
    # 0. Data Hygiene: Clear any attempts with NULL question_id
    db.query(models.AnswerAttempt).filter(models.AnswerAttempt.question_id == None).delete(synchronize_session=False)
    db.commit()

    # 1. Subqueries and filters
    point_filter_base = (models.Question.exam_type == exam_type)
    attempted_ids = db.query(models.AnswerAttempt.question_id).filter(
        models.AnswerAttempt.user_id == user_id,
        models.AnswerAttempt.question_id != None
    )
    wrong_ids = db.query(models.WrongQuestion.question_id).filter(models.WrongQuestion.user_id == user_id)
    favorite_ids = db.query(models.UserFavorite.question_id).filter(models.UserFavorite.user_id == user_id)
    
    # 2. Get all distinct knowledge points for this exam_type
    points_rows = db.query(func.coalesce(models.Question.knowledge_point, "未分类"))\
        .filter(models.Question.exam_type == exam_type)\
        .distinct().all()
    points = [p[0] if p[0] else "未分类" for p in points_rows]
    import random
    random.shuffle(points) # Randomize point order
    
    selected_questions = []
    
    for point in points:
        if len(selected_questions) >= target_total:
            break
            
        point_filter = (models.Question.knowledge_point == point)
        if point == "未分类":
            point_filter = (models.Question.knowledge_point == None) | (models.Question.knowledge_point == "")

        # Pool: (Never Attempted) OR (Favorite) OR (Wrong)
        point_qs = db.query(models.Question).filter(
            point_filter,
            (
                ~models.Question.id.in_(attempted_ids) | 
                models.Question.id.in_(favorite_ids) |
                models.Question.id.in_(wrong_ids)
            )
        ).all()
        
        if point_qs:
            sample_size = min(len(point_qs), num_per_point)
            # Ensure we don't exceed target_total in this step
            remaining = target_total - len(selected_questions)
            sample_size = min(sample_size, remaining)
            
            samples = random.sample(point_qs, sample_size)
            selected_questions.extend(samples)
    
    # Final shuffle for the session
    random.shuffle(selected_questions)
    
    results = []
    for q in selected_questions:
        q_dict = q.__dict__.copy()
        if isinstance(q_dict.get('options'), str):
            try:
                q_dict['options'] = json.loads(q_dict['options'])
            except:
                pass
        results.append(q_dict)
    
    return results

@app.post("/api/questions/{question_id}/submit")
def submit_answer_and_log(question_id: int, answer: AnswerSubmit, db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    db_ans = db_question.correct_answer.strip().upper()
    user_ans = answer.selected_answer.strip().upper()
    is_correct = db_ans == user_ans
    
    # 1. Record Attempt
    attempt = models.AnswerAttempt(
        question_id=question_id,
        user_id=user_id,
        selected_answer=answer.selected_answer,
        is_correct=1 if is_correct else 0
    )
    db.add(attempt)
    db.flush()

    # 2. Update Wrong Question (SRS)
    wrong_q = db.query(models.WrongQuestion).filter(
        models.WrongQuestion.question_id == question_id,
        models.WrongQuestion.user_id == user_id
    ).first()

    # Determine Quality (0-5)
    # If not provided, map is_correct to binary quality
    quality = answer.quality
    if quality is None:
        quality = 4 if is_correct else 1 # 4: Good, 1: Forgot

    if quality < 3: # "Forgot" or "Hard-Failure"
        if not wrong_q:
            wrong_q = models.WrongQuestion(
                question_id=question_id,
                user_id=user_id,
                review_count=0,
                interval=1,
                ease_factor=250,
                next_review_at=datetime.now() + timedelta(days=1)
            )
            db.add(wrong_q)
        else:
            wrong_q.interval = 1
            # Adjust Ease Factor (EF) - Standard SM-2 formula part
            # EF = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
            # Here we simplify slightly for 1-4 scale or 0-5
            wrong_q.ease_factor = max(130, wrong_q.ease_factor - 20)
            wrong_q.next_review_at = datetime.now() + timedelta(days=1)
        
        if wrong_q.review_count is None: wrong_q.review_count = 0
        wrong_q.review_count += 1
        
        try:
            markdown_service.log_wrong_question(db_question)
        except Exception as e:
            print(f"Failed to log wrong question to markdown: {e}")

    else: # Success (Quality 3, 4, 5)
        if wrong_q:
            if wrong_q.interval is None: wrong_q.interval = 1
            if wrong_q.ease_factor is None: wrong_q.ease_factor = 250
            
            # Standard SM-2 EF adjustment
            # q=3 (Good-ish), q=4 (Good), q=5 (Easy)
            # EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
            # If q=4, EF change ~= 0. If q=5, EF increases. If q=3, EF decreases.
            q = quality
            ef_change = (0.1 - (5-q) * (0.08 + (5-q) * 0.02)) * 100
            wrong_q.ease_factor = max(130, int(wrong_q.ease_factor + ef_change))

            new_interval = int(wrong_q.interval * (wrong_q.ease_factor / 100.0))
            if new_interval <= wrong_q.interval: new_interval = wrong_q.interval + 1
            
            # Bonus for "Easy" (q=5)
            if q == 5: new_interval = int(new_interval * 1.3)
            
            wrong_q.interval = new_interval
            wrong_q.next_review_at = datetime.now() + timedelta(days=new_interval)

    db.commit()
    
    # Backup after progress change
    try:
        backup_service.export_progress_to_json(db)
    except Exception as e:
        print(f"Backup failed: {e}")
    
    return {
        "is_correct": is_correct,
        "correct_answer": db_question.correct_answer,
        "explanation": db_question.explanation or "暂无解析",
        "memorization_tip": db_question.memorization_tip
    }

@app.post("/api/quiz/finish")
def finish_quiz_session(topic: str, session_data: List[Dict], db: Session = Depends(database.get_db)):
    log_data_questions = []
    log_data_results = []

    for item in session_data:
        q = db.query(models.Question).filter(models.Question.id == item['question_id']).first()
        if q:
            log_data_questions.append(q)
            log_data_results.append(item)

    markdown_service.log_quiz_session(topic, log_data_questions, log_data_results)
    return {"message": "Session logged successfully"}

@app.get("/api/wrong-questions")
def get_wrong_questions_api(db: Session = Depends(database.get_db), user_id: int = Depends(get_current_user_id)):
    wqs = db.query(models.WrongQuestion).filter(models.WrongQuestion.user_id == user_id).all()
    results = []
    for w in wqs:
        q = w.question
        if not q:
            continue
            
        q_dict = q.__dict__.copy()
        if isinstance(q.options, str):
            q_dict['options'] = json.loads(q.options)
        
        results.append({
            "id": w.id,
            "question": Question(**q_dict),
            "review_count": w.review_count
        })
    return results

@app.delete("/api/knowledge")
def delete_knowledge_point(name: str, db: Session = Depends(database.get_db)):
    """
    Deletes all questions associated with a specific knowledge point.
    Also removes the corresponding source JSON file.
    """
    # 1. Delete questions from DB (cascades will handle attempts and wrong_questions)
    if name == "未分类":
        # Delete questions where knowledge_point is literally "未分类", None, or empty string
        count = db.query(models.Question).filter(
            (models.Question.knowledge_point == "未分类") | 
            (models.Question.knowledge_point == None) | 
            (models.Question.knowledge_point == "")
        ).delete(synchronize_session=False)
    else:
        count = db.query(models.Question).filter(models.Question.knowledge_point == name).delete()
    
    db.commit()
    
    # 2. Delete the source JSON file if it exists
    # We check in both n1 and databricks folders or use current mode if we knew it.
    # Knowledge points are associated with exam_type in questions table.
    # For safety, search in both subdirs.
    json_dir = os.path.join(os.path.dirname(__file__), "json_questions")
    filename = get_safe_filename(name)
    
    deleted_any = False
    for mode in ["n1", "databricks"]:
        json_path = os.path.join(json_dir, mode, filename)
        if os.path.exists(json_path):
            try:
                os.remove(json_path)
                deleted_any = True
            except Exception as e:
                print(f"Failed to delete JSON file {json_path}: {e}")
            
    # 3. Trigger backup to reflect changes in JSON mirrors
    try:
        backup_service.export_progress_to_json(db)
    except Exception as e:
        print(f"Post-knowledge-deletion backup failed: {e}")
        
    return {"message": f"Successfully deleted knowledge point '{name}' and {count} associated questions."}

@app.delete("/api/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(database.get_db)):
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    q_hash = db_question.hash
    db.delete(db_question)
    db.commit()
    
    # Backup after deletion
    try:
        backup_service.export_progress_to_json(db)
    except Exception as e:
        print(f"Backup failed: {e}")

    if q_hash:
        try:
            remove_question_from_json(q_hash)
        except Exception as e:
            print(f"Failed to remove question from JSON: {e}")

    return {"message": "Question deleted successfully"}

@app.post("/api/admin/backup")
def create_manual_backup():
    try:
        path = backup_service.backup_db_file()
        return {"message": "Backup created successfully", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/questions/{question_id}/favorite")
def toggle_favorite(question_id: int, db: Session = Depends(database.get_db)):
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db_question.is_favorite = not db_question.is_favorite
    db.commit()
    
    # Sync to source JSON and update backup
    try:
        sync_question_state_to_json(db_question.hash, {"is_favorite": db_question.is_favorite})
        backup_service.export_progress_to_json(db)
    except Exception as e:
        print(f"State sync/backup failed: {e}")

    return {"id": db_question.id, "is_favorite": db_question.is_favorite}

def sync_question_state_to_json(q_hash: str, updates: Dict):
    import glob
    json_dir = os.path.join(os.path.dirname(__file__), "json_questions")
    files = glob.glob(os.path.join(json_dir, "**", "*.json"), recursive=True)
    for json_file in files:
        updated = False
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not data: continue
            if isinstance(data, dict): data = [data]
            
            for q in data:
                # Direct hash match
                if q.get('hash') == q_hash:
                    q.update(updates)
                    updated = True
                else:
                    # Content/Options match
                    content = q.get('content', q.get('question'))
                    options = q.get('options')
                    if content and options:
                        h = hashlib.sha256(f"{content}-{json.dumps(options, sort_keys=True)}".encode()).hexdigest()
                        if h == q_hash:
                            q.update(updates)
                            updated = True
            
            if updated:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error syncing to {json_file}: {e}")

def remove_question_from_json(q_hash: str):
    import glob
    json_dir = os.path.join(os.path.dirname(__file__), "json_questions")
    if not os.path.exists(json_dir):
        return

    files = glob.glob(os.path.join(json_dir, "**", "*.json"), recursive=True)
    for json_file in files:
        updated = False
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data: continue
            if isinstance(data, dict):
                data = [data]
            
            new_data = []
            for q in data:
                # Content normalization (matching ingestion)
                content = q.get('content', q.get('question'))
                options = q.get('options')
                if not options and 'option_a' in q:
                    options = {
                        'A': q.get('option_a'),
                        'B': q.get('option_b'),
                        'C': q.get('option_c'),
                        'D': q.get('option_d')
                    }
                
                # Check hash
                if q.get('hash') == q_hash:
                    updated = True
                    continue
                
                if content and options:
                    unique_string = f"{content}-{json.dumps(options, sort_keys=True)}"
                    h = hashlib.sha256(unique_string.encode()).hexdigest()
                    if h == q_hash:
                        updated = True
                        continue
                
                new_data.append(q)
            
            if updated:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2, ensure_ascii=False)
                print(f"Removed question {q_hash} from {json_file}")
                
        except Exception as e:
            print(f"Error processing {json_file} for removal: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=28888)
