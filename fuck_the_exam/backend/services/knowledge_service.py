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
        Supports tables and returns all columns as a dictionary.
        """
        points = []
        if not os.path.exists(self.knowledge_dir):
            return points

        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(self.knowledge_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    headers = []
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if not line.startswith("|"):
                            continue
                        
                        # Split by | and remove empty strings from both sides
                        parts = [p.strip() for p in line.split("|") if p.strip()]
                        
                        # Header detection: if it's the first table line or contains N1/语法
                        if not headers:
                            if any(h in ["语法", "Knowledge Point", "项目"] for h in parts):
                                headers = parts
                                continue
                        
                        # Skip separator line
                        if line.replace(" ", "").replace("|", "").replace("-", "") == "":
                            continue
                        if "---" in line and i > 0:
                            continue

                        if headers and parts:
                            entry = {
                                "point": parts[0],
                                "source_file": filename
                            }
                            # Map additional columns to header names
                            for idx, val in enumerate(parts):
                                h_name = headers[idx] if idx < len(headers) else f"col_{idx}"
                                entry[h_name] = val
                            
                            # Fallback for description
                            if "description" not in entry:
                                entry["description"] = parts[1] if len(parts) > 1 else ""
                                
                            points.append(entry)
                except Exception as e:
                    print(f"Error parsing {filename}: {e}")

        return points

    def get_suggestions(self, wrong_question_topics: list) -> List[Dict]:
         # Basic matching logic
         knowledge_map = {p['point']: p for p in self.get_all_knowledge_points()}
         suggestions = []
         # Logic to find relevant knowledge points based on failures
         # For now return all as suggestions with a flag if it matches a wrong topic
         return list(knowledge_map.values())[:5] # Mock return top 5
