import requests

def verify():
    try:
        response = requests.get('http://localhost:28888/api/quiz/gap')
        data = response.json()
        print(f"Total questions returned: {len(data)}")
        if data:
            # Check unique points
            points = set(q['knowledge_point'] for q in data)
            print(f"Represented knowledge points: {len(points)}")
            print(f"First 5 questions sample points: {[q['knowledge_point'] for q in data[:5]]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
