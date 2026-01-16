import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from backend import database, models
from backend.main import generate_quiz, GenerateRequest
from backend.services.markdown_service import MarkdownService

def test_backend_flow():
    print("1. Initializing DB...")
    database.create_db_and_tables()
    
    # Mock AI Client to avoid spending money/quota and network calls for this quick test
    # We will temporarily monkeypatch the ai_client in main.py if possible, 
    # but since we import generate_quiz, we can just patch ai_client.generate_questions_from_topic
    
    from backend import ai_client
    
    def mock_generate(topic, num):
        print(f"   [Mock AI] Generating questions for {topic}...")
        return [
            {
                "content": "Test Question 1",
                "options": {"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"},
                "correct_answer": "A",
                "explanation": "Exp 1",
                "knowledge_point": topic,
                "hash": "hash1"
            }
        ]
    
    original_generate = ai_client.generate_questions_from_topic
    ai_client.generate_questions_from_topic = mock_generate
    
    try:
        print("2. Testing Generate Endpoint Logic...")
        db = next(database.get_db())
        req = GenerateRequest(topic="Testing N1", num_questions=1)
        result = generate_quiz(req, db)
        
        print(f"   Generated {len(result)} questions.")
        assert len(result) == 1
        assert result[0]['content'] == "Test Question 1"
        assert result[0]['options']['A'] == "Opt A"
        print("   ✅ Generate success.")

        print("3. Testing Markdown Service...")
        ms = MarkdownService()
        ms.log_quiz_session("Testing N1", 
                           [models.Question(content="Q1", correct_answer="A", explanation="Exp")], 
                           [{'is_correct': True, 'selected_answer': 'A'}])
        
        if os.path.exists("knowledge_base/progress.md"):
            print("   ✅ Markdown file created.")
        else:
            print("   ❌ Markdown file NOT created.")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ai_client.generate_questions_from_topic = original_generate
        # Cleanup
        if os.path.exists("n1_app.db"):
            # os.remove("n1_app.db") # Keep it for inspection if needed
            pass

if __name__ == "__main__":
    test_backend_flow()
