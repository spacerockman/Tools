import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "backend", "n1_app.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Step 1: Creating new tables...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    print("Step 2: Adding user_id columns to existing tracking tables...")
    # SQLite allows adding columns. We use try-except in case they already exist.
    tables_to_update = ["answer_attempts", "wrong_questions", "study_records", "quiz_sessions"]
    for table in tables_to_update:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")
            print(f"  Added user_id to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  user_id already exists in {table}")
            else:
                raise e

    print("Step 3: Creating default user...")
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'Default User')")
    
    print("Step 4: Mapping existing data to default user...")
    for table in tables_to_update:
        cursor.execute(f"UPDATE {table} SET user_id = 1 WHERE user_id IS NULL")
    
    print("Step 5: Migrating favorites...")
    # Check if is_favorite column exists in questions
    cursor.execute("PRAGMA table_info(questions)")
    columns = [row[1] for row in cursor.fetchall()]
    if "is_favorite" in columns:
        cursor.execute("""
        INSERT INTO user_favorites (user_id, question_id)
        SELECT 1, id FROM questions WHERE is_favorite = 1
        AND id NOT IN (SELECT question_id FROM user_favorites WHERE user_id = 1)
        """)
        print("  Migrated favorites to user_favorites table")
    
    # Note: We keep is_favorite in questions for now to avoid complex table recreation, 
    # but the app logic will use user_favorites.

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
