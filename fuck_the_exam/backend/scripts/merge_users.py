import sqlite3
import hashlib
import os
import secrets

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "n1_app.db")

def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    phash = hashlib.sha256((password + salt).encode()).hexdigest()
    return phash, salt

def merge_users(from_id, to_id, new_password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print(f"Merging data from User {from_id} to User {to_id}...")

        # Ensure columns exist
        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        if "password_hash" not in cols:
            print("Adding password_hash column...")
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(128)")
        if "salt" not in cols:
            print("Adding salt column...")
            cursor.execute("ALTER TABLE users ADD COLUMN salt VARCHAR(32)")

        # Update all progress tables
        tables = [
            "answer_attempts",
            "wrong_questions",
            "user_favorites",
            "study_records",
            "quiz_sessions"
        ]

        for table in tables:
            # Check for duplicates if it's favorites or wrong questions
            if table in ["user_favorites", "wrong_questions"]:
                # Find duplicates
                cursor.execute(f"SELECT question_id FROM {table} WHERE user_id = ?", (from_id,))
                from_questions = set(row[0] for row in cursor.fetchall())
                
                cursor.execute(f"SELECT question_id FROM {table} WHERE user_id = ?", (to_id,))
                to_questions = set(row[0] for row in cursor.fetchall())
                
                duplicates = from_questions.intersection(to_questions)
                
                if duplicates:
                    print(f"Removing {len(duplicates)} duplicate entries from {table}...")
                    placeholders = ', '.join(['?'] * len(duplicates))
                    cursor.execute(f"DELETE FROM {table} WHERE user_id = ? AND question_id IN ({placeholders})", (from_id, *duplicates))

            # Update remaining
            cursor.execute(f"UPDATE {table} SET user_id = ? WHERE user_id = ?", (to_id, from_id))
            print(f"Updated {cursor.rowcount} rows in {table}.")

        # Update password for target user
        print(f"Setting password for User {to_id}...")
        phash, salt = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (phash, salt, to_id))

        # Delete source user
        print(f"Deleting source User {from_id}...")
        cursor.execute("DELETE FROM users WHERE id = ?", (from_id,))

        conn.commit()
        print("Success: Merge complete.")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # From ID 1 (Default User) to ID 2 (xujintao)
    merge_users(1, 2, "1226")
