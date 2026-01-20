import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "backend", "n1_app.db")

def diag():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT COALESCE(knowledge_point, '未分类') FROM questions")
    all_points = [r[0] for r in cursor.fetchall()]
    
    print("--- Detailed Diagnostics ---")
    
    selected_total = 0
    num_per_point = 10
    
    for point in all_points:
        if point == '未分类':
            where_clause = "(knowledge_point IS NULL OR knowledge_point = '')"
        else:
            # Use placeholders for safety
            where_clause = "knowledge_point = ?"
            
        params = (point,) if point != '未分类' else ()
        
        # Original current logic
        q_current = f"""
            SELECT COUNT(*) FROM questions 
            WHERE {where_clause} 
            AND (id NOT IN (SELECT question_id FROM answer_attempts WHERE is_correct = 1) OR is_favorite = 1)
        """
        cursor.execute(q_current, params)
        current_count = cursor.fetchone()[0]
        
        # Target logic: Never done
        q_never = f"""
            SELECT COUNT(*) FROM questions 
            WHERE {where_clause} 
            AND id NOT IN (SELECT question_id FROM answer_attempts)
        """
        cursor.execute(q_never, params)
        never_count = cursor.fetchone()[0]
        
        if current_count > 0 or never_count > 0:
            print(f"Point '{point}': current={current_count}, never={never_count}")
        
        selected_total += min(current_count, num_per_point)
        
    print(f"\nConceptual total selected: {selected_total}")
    
    # Check if any question_id in answer_attempts is NULL
    cursor.execute("SELECT COUNT(*) FROM answer_attempts WHERE question_id IS NULL")
    null_ids = cursor.fetchone()[0]
    print(f"NULL question_ids in attempts: {null_ids}")
    
    conn.close()

if __name__ == "__main__":
    diag()
