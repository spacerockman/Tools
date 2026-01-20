import os
import json
from sqlalchemy import create_engine, func, distinct
from sqlalchemy.orm import sessionmaker
from backend import models, database

# Setup
DB_PATH = os.path.join(os.getcwd(), "backend", "n1_app.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    num_per_point = 10
    all_points = db.query(func.coalesce(models.Question.knowledge_point, "未分类")).distinct().all()
    all_points = [p[0] if p[0] else "未分类" for p in all_points]
    print(f"DEBUG: Found {len(all_points)} unique points")

    selected_questions = []
    
    mastered_subquery = db.query(models.AnswerAttempt.question_id).filter(models.AnswerAttempt.is_correct == 1)
    
    # Let's also check total unattempted
    attempted_subquery = db.query(models.AnswerAttempt.question_id)

    for point in all_points:
        point_filter = (models.Question.knowledge_point == point)
        if point == "未分类":
            point_filter = (models.Question.knowledge_point == None) | (models.Question.knowledge_point == "")

        # Current Logic
        point_qs = db.query(models.Question).filter(
            point_filter,
            (~models.Question.id.in_(mastered_subquery)) | (models.Question.is_favorite == True)
        ).all()
        
        # New Target Logic (Unattempted only)
        new_point_qs = db.query(models.Question).filter(
            point_filter,
            (~models.Question.id.in_(attempted_subquery))
        ).all()
        
        print(f"Point '{point}': current_pool_size={len(point_qs)}, unattempted_size={len(new_point_qs)}")
        
        if point_qs:
            import random
            sample_size = min(len(point_qs), num_per_point)
            samples = random.sample(point_qs, sample_size)
            selected_questions.extend(samples)

    print(f"DEBUG: Selected {len(selected_questions)} total questions using current logic")

finally:
    db.close()
