import os
import datetime
import json

class MarkdownService:
    def __init__(self, base_path: str = "knowledge_base"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
        self.progress_file = os.path.join(self.base_path, "progress.md")
        self.wrong_questions_file = os.path.join(self.base_path, "wrong_questions.md")

    def _ensure_daily_dir(self):
        today = datetime.date.today().isoformat()
        daily_dir = os.path.join(self.base_path, today)
        os.makedirs(daily_dir, exist_ok=True)
        return daily_dir, today

    def log_quiz_session(self, topic: str, questions: list, results: list):
        """
        Logs a quiz session to a markdown file in the daily directory.
        """
        daily_dir, today = self._ensure_daily_dir()
        timestamp = datetime.datetime.now().strftime("%H-%M-%S")
        filename = f"quiz_{timestamp}.md"
        filepath = os.path.join(daily_dir, filename)

        score = sum(1 for r in results if r['is_correct'])
        total = len(results)
        
        content = f"# Quiz Session: {topic}\n"
        content += f"**Date**: {today} {timestamp}\n"
        content += f"**Score**: {score}/{total}\n\n"
        
        content += "## Details\n"
        for i, (q, r) in enumerate(zip(questions, results)):
            status = "✅" if r['is_correct'] else "❌"
            content += f"### Q{i+1} {status}\n"
            content += f"**Question**: {q.content}\n\n"
            content += f"**Your Answer**: {r['selected_answer']} | **Correct**: {q.correct_answer}\n\n"
            if not r['is_correct']:
                content += f"> **Explanation**: {q.explanation}\n\n"
            content += "---\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        self._update_daily_progress(today, topic, score, total)

    def _update_daily_progress(self, date: str, topic: str, score: int, total: int):
        """
        Appends a summary line to the main progress.md file.
        """
        if not os.path.exists(self.progress_file):
            with open(self.progress_file, "w", encoding="utf-8") as f:
                f.write("# Learning Progress Tracker\n\n")

        line = f"- **{date}**: Tested on `{topic}`. Score: {score}/{total} ({int(score/total*100)}%)\n"
        
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(line)

    def log_wrong_question(self, question):
        """
        Appends a wrong question to the wrong_questions.md file.
        """
        if not os.path.exists(self.wrong_questions_file):
            with open(self.wrong_questions_file, "w", encoding="utf-8") as f:
                f.write("# Wrong Questions Black Book\n\n")

        # Basic deduplication check could be added here, but for now we append
        options = question.options
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except:
                options = {}
        
        content = f"## [{datetime.date.today()}] {question.knowledge_point}\n"
        content += f"**Q**: {question.content}\n"
        content += f"- A: {options.get('A')}\n"
        content += f"- B: {options.get('B')}\n"
        content += f"- C: {options.get('C')}\n"
        content += f"- D: {options.get('D')}\n"
        content += f"\n**Correct Answer**: {question.correct_answer}\n"
        content += f"**Explanation**: {question.explanation}\n"
        content += "---\n\n"

        with open(self.wrong_questions_file, "a", encoding="utf-8") as f:
            f.write(content)
