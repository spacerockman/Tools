import os
import re
from typing import List, Dict

class KnowledgeService:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.knowledge_dir = os.path.join(base_path, "知识点")

    def get_all_knowledge_points(self) -> List[Dict]:
        """
        Parses all markdown files in the knowledge directory and extracts knowledge points.
        Assumes tables with format: | Knowledge Point | ... |
        """
        points = []
        if not os.path.exists(self.knowledge_dir):
            return points

        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(self.knowledge_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple regex to find table rows. 
                    # Adjust based on actual table format in `grammar.md`
                    # Example row: | 〜とみられる | ...
                    matches = re.findall(r'\|\s*([^|]+)\s*\|', content)
                    # This regex is too broad, it captures every cell.
                    # Better to read line by line.
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    in_table = False
                    headers = []
                    
                    for line in lines:
                        if line.strip().startswith("|"):
                            parts = [p.strip() for p in line.split("|") if p.strip()]
                            if "语法" in parts or "Knowledge Point" in parts: # Header detection
                                in_table = True
                                continue
                            if in_table and "---" in line: # Separator
                                continue
                            if in_table and parts:
                                # Assuming first column is the point
                                point = parts[0]
                                description = parts[1] if len(parts) > 1 else ""
                                points.append({
                                    "point": point,
                                    "description": description,
                                    "source_file": filename
                                })

        return points

    def get_suggestions(self, wrong_question_topics: list) -> List[Dict]:
         # Basic matching logic
         knowledge_map = {p['point']: p for p in self.get_all_knowledge_points()}
         suggestions = []
         # Logic to find relevant knowledge points based on failures
         # For now return all as suggestions with a flag if it matches a wrong topic
         return list(knowledge_map.values())[:5] # Mock return top 5
