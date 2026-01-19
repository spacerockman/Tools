---
description: How to generate and ingest new N1 quiz questions
---
// turbo-all
1. Identify the target grammar point (e.g., from `backend/知识点/语法.md`).
2. Run the generation script:
   ```bash
   python .agent/skills/n1-quiz/scripts/generate_questions.py "<grammar_point>" 10
   ```
3. (Optional) Force ingest if the API didn't handle it:
   ```bash
   python .agent/skills/n1-quiz/scripts/ingest_questions.py
   ```
4. Verify the new JSON file exists in `backend/json_questions/`.
