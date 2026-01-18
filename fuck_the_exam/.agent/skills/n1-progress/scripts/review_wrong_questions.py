import os

def review_wrong_questions():
    """
    Parses knowledge_base/wrong_questions.md and prints a summary.
    """
    wrong_file = os.path.join(os.getcwd(), "knowledge_base", "wrong_questions.md")
    if not os.path.exists(wrong_file):
        print("No wrong questions log found. Great job!")
        return

    print("Checking recently missed questions...")
    with open(wrong_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Simple count of questions (assuming each starts with ## or ###)
    count = content.count("## ")
    print(f"Total entries in 'Black Book': {count}")
    
    # Show last 3 entries
    entries = content.split("## ")
    for entry in entries[-3:]:
        if entry.strip():
            print("-" * 20)
            print("Question: " + entry.split("\n")[0])

if __name__ == "__main__":
    review_wrong_questions()
