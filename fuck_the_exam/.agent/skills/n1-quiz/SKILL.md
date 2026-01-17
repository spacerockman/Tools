---
name: n1-quiz
description: Ability to generate, ingest, and manage Japanese N1 level quiz questions through the project's backend API.
---
# N1 Quiz Management Skill

This skill allows the agent to interact with the quiz engine, focusing on automated content generation and data synchronization.

## Available Tools (via scripts)
- **`generate_questions.py <topic> [num]`**: Triggers the parallel question generator for a specific topic.
- **`ingest_questions.py`**: Force-scans the `backend/json_questions` directory and imports new questions into the database.

## Critical Paths
- `backend/ai_client.py`: High-speed generation logic (use for reference).
- `backend/json_questions/`: Directory for persistent question storage.

## Usage
"Please generate 10 questions about '～といえども' and make sure they are ingested into the DB."
