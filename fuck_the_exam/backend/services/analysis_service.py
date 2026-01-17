import json
import random
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models

class AnalysisService:
    def __init__(self, ai_client=None):
        # ai_client is preserved for backward compatibility in constructor signature
        # but is currently unused by the local engine.
        self.ai_client = ai_client

    def generate_local_diagnostic(self, db: Session) -> Dict[str, Any]:
        """
        Deterministic, token-free diagnostic engine.
        Calculates mastery and generates reports based on database statistics.
        """
        total_attempts = db.query(models.AnswerAttempt).count()
        if total_attempts < 5:
            return {
                "summary": "数据收集不足（需至少5次答题），目前主要基于初始评估。",
                "mastery_scores": {"grammar": 30, "vocab": 30, "reading": 20},
                "weakness_analysis": [
                    {"point": "数据积累中", "reason": "练习量尚少", "advice": "请继续完成练习，AI 将在数据充足后为你生成深度改进建议。"}
                ],
                "prediction": "待评估 (数据不足)"
            }

        correct_attempts = db.query(models.AnswerAttempt).filter(models.AnswerAttempt.is_correct == 1).count()
        accuracy = (correct_attempts / total_attempts) * 100

        # Category-based mastery (Heuristic based on keywords in knowledge_point)
        categories = {"grammar": [], "vocab": [], "reading": []}
        all_attempts = db.query(models.Question.knowledge_point, models.AnswerAttempt.is_correct) \
                         .join(models.AnswerAttempt, models.Question.id == models.AnswerAttempt.question_id).all()
        
        for kp, is_correct in all_attempts:
            category = "grammar" 
            kp_lower = (kp or "").lower()
            if any(x in kp_lower for x in ["vocab", "词汇", "单词", "训读", "音读"]):
                category = "vocab"
            elif any(x in kp_lower for x in ["reading", "阅读", "长文", "短文"]):
                category = "reading"
            categories[category].append(1 if is_correct else 0)

        mastery_scores = {}
        for cat, results in categories.items():
            if not results:
                mastery_scores[cat] = 40
            else:
                cat_acc = (sum(results) / len(results)) * 100
                volume_bonus = min(len(results), 50) / 50 * 30
                mastery_scores[cat] = int((cat_acc * 0.7) + volume_bonus)

        # Weakness analysis (Top 3 failed points)
        wrong_points = db.query(
            models.Question.knowledge_point,
            func.count(models.AnswerAttempt.id).label('count')
        ).join(models.AnswerAttempt, models.Question.id == models.AnswerAttempt.question_id) \
         .filter(models.AnswerAttempt.is_correct == 0) \
         .group_by(models.Question.knowledge_point) \
         .order_by(func.count(models.AnswerAttempt.id).desc()) \
         .limit(3).all()

        weakness_analysis = []
        for p, count in wrong_points:
            if not p: continue
            weakness_analysis.append({
                "point": p,
                "reason": f"在该考点已累积错误 {count} 次，说明记忆提取路径存在偏差。",
                "advice": "建议重点复习该语法的使用接续和反义表达。"
            })

        # Fallback if no wrongs yet
        if not weakness_analysis:
            weakness_analysis.append({
                "point": "全面发展中",
                "reason": "目前保持全对记录",
                "advice": "继续保持，建议挑战更高难度的综合阅读题目。"
            })

        # Summary & Prediction Templates
        if accuracy > 85:
            summary = "状态极佳！你的基础非常扎实，目前已进入最后的冲刺稳固期。"
            prediction = "备考就绪 (建议维持现状)"
        elif accuracy > 65:
            summary = "进度良好，但在特定 N1 语法接续上仍有波动，需强化细节。"
            prediction = "约需 15 天强化练习"
        else:
            summary = "当前正确率较低，建议放慢进度，重新整理错题背后的语法逻辑。"
            prediction = "约需 30-45 天系统复习"

        return {
            "summary": summary,
            "mastery_scores": mastery_scores,
            "weakness_analysis": weakness_analysis,
            "prediction": prediction
        }

    def generate_diagnostic_report(self, db: Session) -> Dict[str, Any]:
        """
        Wrapper that now routes to the local engine to save tokens.
        """
        return self.generate_local_diagnostic(db)
