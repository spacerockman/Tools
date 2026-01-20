import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "backend", "n1_app.db")

def diag():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all points
    cursor.execute("SELECT DISTINCT COALESCE(knowledge_point, '未分类') FROM questions")
    all_points = [r[0] for r in cursor.fetchall()]
    print(f"DEBUG: Found {len(all_points)} unique points")
    
    selected_total = 0
    num_per_point = 10
    
    for point in all_points:
        # mastered filter
        mastered_query = "SELECT question_id FROM answer_attempts WHERE is_correct = 1"
        
        if point == '未分类':
            where_clause = "(knowledge_point IS NULL OR knowledge_point = '')"
        else:
            where_clause = f"knowledge_point = '{point}'"
            
        cursor.execute(f"""
            SELECT id FROM questions 
            WHERE {where_clause} 
            AND (id NOT IN ({mastered_query}) OR is_favorite = 1)
        """)
        current_pool = cursor.fetchall()
        
        # unattempted filter
        cursor.execute(f"""
            SELECT id FROM questions 
            WHERE {where_clause} 
            AND id NOT IN (SELECT question_id FROM answer_attempts)
        """)
        unattempted_pool = cursor.fetchall()
        
        print(f"Point '{point}': current_pool_size={len(current_pool)}, unattempted_size={len(unattempted_pool)}")
        selected_total += min(len(current_pool), num_per_point)
        
    print(f"DEBUG: Selected {selected_total} total questions conceptually using current logic")
    conn.close()

if __name__ == "__main__":
    diag()
