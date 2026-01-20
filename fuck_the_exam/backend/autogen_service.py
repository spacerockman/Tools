import time
import threading
import os
import json
import hashlib
import re
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from . import models, ai_client, database

class AutoGenService:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.is_running = False
        self.thread = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("AutoGenService started.")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
        print("AutoGenService stopped.")

    def _run(self):
        # Initial delay to allow the main app to start smoothly
        print("AutoGenService: Initial delay of 60 seconds...")
        time.sleep(60)

        while self.is_running:
            print("AutoGenService: Running check for question generation.")
            try:
                self.check_and_generate_questions()
            except Exception as e:
                print(f"Error in AutoGenService loop: {e}")
            
            print(f"AutoGenService: Check finished. Sleeping for 4 hours...")
            # Sleep for 4 hours
            time.sleep(4 * 60 * 60)

    def check_and_generate_questions(self, min_unanswered=10):
        db = self.db_session_factory()
        try:
            # 1. Get all distinct knowledge points
            knowledge_points = db.query(distinct(models.Question.knowledge_point)).all()
            knowledge_points = [kp[0] for kp in knowledge_points if kp[0]]
            print(f"AutoGenService: Found {len(knowledge_points)} knowledge points to check.")

            for point in knowledge_points:
                if not self.is_running:
                    print("AutoGenService: Stopping check early.")
                    break
                    
                # 2. For each point, count unanswered questions
                answered_question_ids = db.query(distinct(models.AnswerAttempt.question_id)).join(models.Question).filter(models.Question.knowledge_point == point).subquery()
                
                unanswered_count = db.query(models.Question).filter(
                    models.Question.knowledge_point == point,
                    ~models.Question.id.in_(answered_question_ids)
                ).count()

                print(f"AutoGenService: Knowledge point '{point}' has {unanswered_count} unanswered questions.")

                # 3. If count is low, generate more
                if unanswered_count < min_unanswered:
                    num_to_generate = min_unanswered - unanswered_count
                    print(f"AutoGenService: Generating {num_to_generate} new questions for '{point}'...")
                    self._generate_and_save(point, num_to_generate, db)
                
                # Yield control to other threads to avoid blocking the server
                time.sleep(10)

        finally:
            db.close()

    def _generate_and_save(self, topic: str, num_questions: int, db: Session):
        # Refactored from backend/main.py
        
        # 1. Generate from AI
        generated_questions = ai_client.generate_questions_from_topic(topic, num_questions)
        if not generated_questions:
            print(f"Failed to generate questions for topic '{topic}' from AI.")
            return

        # 2. Save to File
        self._save_generated_questions_to_file(topic, generated_questions)

        # 3. Save to DB
        for q_data in generated_questions:
            if 'hash' not in q_data:
                 unique_string = f"{q_data['content']}-{json.dumps(q_data['options'], sort_keys=True)}"
                 q_data['hash'] = hashlib.sha256(unique_string.encode()).hexdigest()
            
            existing_q = db.query(models.Question).filter(models.Question.hash == q_data['hash']).first()
            
            if not existing_q:
                db_q = models.Question(
                    content=q_data['content'],
                    options=json.dumps(q_data['options'], ensure_ascii=False),
                    correct_answer=q_data['correct_answer'],
                    explanation=q_data.get('explanation'),
                    memorization_tip=q_data.get('memorization_tip'),
                    knowledge_point=q_data.get('knowledge_point') or topic,
                    exam_type="N1",
                    hash=q_data['hash']
                )
                db.add(db_q)
        
        db.commit()
        print(f"Successfully generated and saved {len(generated_questions)} questions for '{topic}'.")

    def _save_generated_questions_to_file(self, topic: str, questions: list):
        # Refactored from backend/main.py
        safe_topic = re.sub(r'[\\/*?:"<>|]', "", topic).replace(" ", "_")
        filename = f"{safe_topic}.json"
        json_dir = os.path.join(os.path.dirname(__file__), "json_questions")
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

        existing_hashes = {q.get('hash') for q in existing_data if q.get('hash')}

        new_questions = []
        for q in questions:
            if 'hash' not in q:
                 unique_string = f"{q['content']}-{json.dumps(q['options'], sort_keys=True)}"
                 q['hash'] = hashlib.sha256(unique_string.encode()).hexdigest()

            if q['hash'] not in existing_hashes:
                new_questions.append(q)
                existing_hashes.add(q['hash'])
        
        if new_questions:
            final_data = existing_data + new_questions
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(new_questions)} new questions to {filepath}")
