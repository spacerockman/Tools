# Japanese N1 Quiz App - System Design & Architecture

## 1. System Architecture Design

The system follows a **Modern Web Application** architecture with a focus on local deployment and "File as Source of Truth" for progress tracking.

### High-Level Architecture
```mermaid
graph TD
    User[User (Mobile/Desktop)] -->|HTTP/REST| Frontend[Frontend (Next.js)]
    Frontend -->|API Calls| Backend[Backend (FastAPI)]
    
    subgraph "Backend Services"
        Backend -->|Query/Store| DB[(SQLite Database)]
        Backend -->|High-Speed Generate| AI[AI Service (SiliconFlow DeepSeek)]
        Backend -->|Local Grounding| MD[Markdown Knowledge Base]
    end
    
    subgraph "Storage Layer"
        DB -->|Structured Data| SQLiteFiles
        MD -->|Grounding Reference| MDFiles[MD Knowledge Base]
        Backend -->|Study Logs| LogFiles[Markdown Study Logs]
    end
```

### Module Breakdown
1.  **Frontend (Next.js)**:
    -   **Tech**: Next.js 14+ (App Router), TailwindCSS, Framer Motion (animations), Lucide React (icons).
    -   **Style**: "Notion-like" minimalist aesthetic. Clean typography, card-based layout, subtle borders.
    -   **Responsibility**: UI rendering, state management, API integration.
2.  **Backend (FastAPI)**:
    -   **Tech**: Python 3.10+, FastAPI, SQLAlchemy (ORM), Pydantic.
    -   **Responsibility**: Business logic, DB operations, AI orchestration, Markdown file management.
3.  **AI Service**:
    -   **Tech**: `google-generativeai` SDK.
    -   **Responsibility**: Prompt construction, calling Gemini, parsing JSON responses.
4.  **Data Layer**:
    -   **Primary (Hot Data)**: SQLite for immediate transactional integrity (deduplication, relationships).
    -   **Secondary (Cold/Log Data)**: Markdown files for long-term storage and user visibility.

## 2. Frontend Page Design

### Design Philosophy
-   **Visuals**: Black/White monochrome with functional colors (Green=Correct, Red=Wrong, Blue=Action).
-   **Typography**: Inter (UI), Noto Sans JP (Japanese text).
-   **Components**: Cards with soft shadows, glassmorphism headers.

### Core Pages
1.  **Dashboard (`/`)**:
    -   **Hero Section**: "Keep pushing! N1 is close." (Motivational quote).
    -   **Stats Card**: Today's Questions (count), Accuracy Rate (%), Streak (days).
    -   **Quick Actions**: "Start Random Quiz", "Review Wrong Questions".
    -   **Recent Logs**: List of recently generated study logs.
2.  **Quiz Generator (`/quiz/new`)**:
    -   **Input**: "Topic/Knowledge Point" (e.g., "Grammar: ～ざるを得ない", "Reading: Philosophy").
    -   **Settings**: Number of questions (default 5).
    -   **Action**: "Generate via AI" (Loading state with interesting facts/animations).
3.  **Quiz Session (`/quiz/[id]`)**:
    -   **Layout**: Single card focus.
    -   **Interaction**: Select option -> Immediate feedback (Correct/Wrong) + Explanation expanding below.
    -   **Navigation**: "Next Question" floats at bottom.
4.  **Wrong Questions (`/review`)**:
    -   **Filter**: By incorrect count, by date.
    -   **Mode**: "Flashcard Mode" or "List Mode".

## 3. Backend API Design

| Method | Path | Description |
| :--- | :--- | :--- |
| **Quiz** | | |
| `POST` | `/api/quiz/generate` | Generate questions via AI given a topic. |
| `GET` | `/api/questions` | Get list of questions (filter by new/reviewed). |
| `POST` | `/api/questions/{id}/submit` | Submit answer. Returns correctness & explanation. Triggers MD sync. |
| **Review** | | |
| `GET` | `/api/wrong-questions` | Get list of questions user got wrong. |
| **Stats** | | |
| `GET` | `/api/stats/dashboard` | Get aggregate stats for the dashboard. |

## 4. Database Schema (SQLite)

```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,          -- Question stem
    options JSON NOT NULL,          -- {"A": "...", "B": "..."} stored as JSON
    correct_answer VARCHAR(1) NOT NULL,
    explanation TEXT,
    knowledge_point TEXT,           -- The topic used to generate this
    exam_type VARCHAR(20) DEFAULT 'N1', -- N1, N2, etc.
    hash VARCHAR(64) UNIQUE,        -- Content hash for deduplication
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE study_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    user_answer VARCHAR(1),
    is_correct BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(question_id) REFERENCES questions(id)
);
```

## 5. Gemini Prompt Template

```python
PROMPT_TEMPLATE = """
You are a strict Japanese N1 Exam expert. 
Generate {num} multiple-choice questions testing the following topic: "{topic}".

Constraint Checklist & Confidence Score:
1. Strict N1 level? Yes.
2. No duplicate questions? Yes.
3. JSON output only? Yes.

Output Format (strictly valid JSON list, no markdown):
[
  {{
    "content": "JAPANESE_QUESTION_TEXT",
    "options": {{
        "A": "OPTION_A_TEXT",
        "B": "OPTION_B_TEXT",
        "C": "OPTION_C_TEXT",
        "D": "OPTION_D_TEXT"
    }},
    "correct_answer": "A",
    "explanation": "Detailed explanation in Chinese/Japanese focusing on why the answer is correct and why others are wrong.",
    "knowledge_point": "{topic}"
  }}
]
"""
```

## 6. Markdown Knowledge Base Structure

The system acts as a "logger" to your local file system.

```text
/Users/xujintao/Documents/workspace/Tools/fuck_the_exam/
├── knowledge_base/
│   ├── progress.md          <-- Daily summary (auto-updated)
│   ├── wrong_questions.md   <-- The "Black Book" of errors
│   └── 2024-01-16/          <-- Daily folders
│       ├── quiz_01.md       <-- Specific quiz session logs
│       └── quiz_02.md
```

**Example `progress.md` content:**
```markdown
# Learning Progress
## 2024-01-16
- **Focus**: Grammar (～なしに)
- **Score**: 4/5 (80%)
- **Mistakes**: 1 (Added to wrong_questions.md)
```

## 7. MVP Implementation Strategy

1.  **Backend Core**:
    -   Setup `FastAPI` + `SQLAlchemy`.
    -   Implement `GeminiClient` class using `google-generativeai`.
    -   Implement `MarkdownLogger` service.
2.  **Frontend Core**:
    -   Init `Next.js` app.
    -   Create `QuizCard` component.
    -   Connect `useQuery` (Tanstack Query) to fetch questions.
3.  **Deployment**:
    -   `Dockerfile` containing both (or multi-stage build) or `docker-compose.yml` for separation.
    -   Bind mount the `knowledge_base` directory so files persist on host.

## 8. Scalability & Extensions
-   **Multi-User**: Add `users` table and JWT auth.
-   **TTS**: Use OpenAI TTS to read the Japanese questions aloud.
-   **Spaced Repetition (SRS)**: Implement SuperMemo-2 algorithm for the "Wrong Questions" review schedule.