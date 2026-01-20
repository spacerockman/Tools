from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    options = Column(Text, nullable=False) # Stored as JSON string
    correct_answer = Column(String(1), nullable=False)
    explanation = Column(Text, nullable=True)
    memorization_tip = Column(Text, nullable=True)
    knowledge_point = Column(Text, nullable=True, index=True)
    exam_type = Column(String(20), default='N1')
    hash = Column(String(64), unique=True, index=True)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    attempts = relationship("AnswerAttempt", back_populates="question")

class AnswerAttempt(Base):
    __tablename__ = "answer_attempts"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    selected_answer = Column(String(1), nullable=False)
    is_correct = Column(Integer, nullable=False) # 1 for true, 0 for false
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())

    question = relationship("Question", back_populates="attempts")

class WrongQuestion(Base):
    __tablename__ = "wrong_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    review_count = Column(Integer, default=0)
    last_reviewed_at = Column(DateTime(timezone=True), onupdate=func.now())

    question = relationship("Question")

    # Spaced Repetition Fields
    next_review_at = Column(DateTime(timezone=True), server_default=func.now())
    interval = Column(Integer, default=1) # Iteration interval in days
    ease_factor = Column(Integer, default=250) # Multiplied by 100 to store as int (2.5 -> 250)

class StudyRecord(Base):
    __tablename__ = "study_records"

    id = Column(Integer, primary_key=True, index=True)
    study_date = Column(DateTime(timezone=True), server_default=func.now())
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)

class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_key = Column(String(64), unique=True, index=True)
    topic = Column(Text, nullable=True)
    questions_json = Column(Text, nullable=False)
    results_json = Column(Text, nullable=False)
    current_index = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
