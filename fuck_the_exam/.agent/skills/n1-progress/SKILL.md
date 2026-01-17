---
name: n1-progress
description: Ability to analyze and summarize the user's learning progress and review history.
---
# N1 Progress Analytics Skill

This skill provides insights into the user's learning journey by parsing log files in `knowledge_base/`.

## Available Tools (via scripts)
- **`analyze_progress.py`**: Summarizes the `knowledge_base/progress.md` file to show recent activity and accuracy trends.
- **`review_wrong_questions.py`**: Parses `knowledge_base/wrong_questions.md` to identify recurring weak points.

## Critical Paths
- `knowledge_base/progress.md`: Main log for quiz sessions.
- `knowledge_base/wrong_questions.md`: The "Black Book" of missed questions.

## Usage
"How has my study progress been over the last week? Which grammar points should I focus on next?"
