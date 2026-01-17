import os
import json
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from .. import models

class BackupService:
    def __init__(self, db_path: str, backup_dir: str):
        self.db_path = db_path
        self.backup_dir = backup_dir
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

    def backup_db_file(self):
        """Creates a timestamped copy of the SQLite database file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"n1_app_{timestamp}.db.bak")
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def export_progress_to_json(self, db: Session):
        """Mirror SRS state (wrong_questions) to a JSON file."""
        wqs = db.query(models.WrongQuestion).all()
        export_data = []
        for w in wqs:
            q = w.question
            export_data.append({
                "question_hash": q.hash,
                "review_count": w.review_count,
                "interval": w.interval,
                "ease_factor": w.ease_factor,
                "next_review_at": w.next_review_at.isoformat() if w.next_review_at else None,
                "last_reviewed_at": w.last_reviewed_at.isoformat() if w.last_reviewed_at else None
            })
        
        filepath = os.path.join(self.backup_dir, "progress_backup.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        return filepath

    def restore_progress_from_json(self, db: Session):
        """Restore SRS state from JSON back into the database."""
        filepath = os.path.join(self.backup_dir, "progress_backup.json")
        if not os.path.exists(filepath):
            return 0

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            for item in data:
                q = db.query(models.Question).filter(models.Question.hash == item['question_hash']).first()
                if not q:
                    continue
                
                # Check if entry already exists
                existing = db.query(models.WrongQuestion).filter(models.WrongQuestion.question_id == q.id).first()
                if not existing:
                    new_w = models.WrongQuestion(
                        question_id=q.id,
                        review_count=item['review_count'],
                        interval=item['interval'],
                        ease_factor=item['ease_factor'],
                        next_review_at=datetime.fromisoformat(item['next_review_at']) if item['next_review_at'] else None,
                        last_reviewed_at=datetime.fromisoformat(item['last_reviewed_at']) if item['last_reviewed_at'] else None
                    )
                    db.add(new_w)
                    count += 1
            
            db.commit()
            return count
        except Exception as e:
            print(f"Failed to restore progress: {e}")
            return 0
