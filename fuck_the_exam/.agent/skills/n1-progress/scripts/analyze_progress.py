import os

def analyze_progress():
    """
    Summarizes the progress.md file.
    """
    progress_file = os.path.join(os.getcwd(), "knowledge_base", "progress.md")
    if not os.path.exists(progress_file):
        print("No progress log found yet. Keep studying!")
        return

    with open(progress_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    print(f"Total sessions logged: {len(lines) - 2}") # Skip header
    print("Recent activity:")
    for line in lines[-5:]:
        if line.startswith("-"):
            print(line.strip())

if __name__ == "__main__":
    analyze_progress()
