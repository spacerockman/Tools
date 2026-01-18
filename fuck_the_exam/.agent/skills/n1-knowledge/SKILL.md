---
name: n1-knowledge
description: Ability to query and explore the Japanese N1 knowledge base, including grammar points and vocabulary details.
---
# N1 Knowledge Base Skill

This skill allows the agent to navigate the project's curated knowledge base, located in `backend/知识点`.

## Available Tools (via scripts)
- **`search_knowledge.py <query>`**: Searches all markdown files in the knowledge base for a specific grammar point or keyword.
- **`list_knowledge_points.py`**: Lists all available knowledge points categorized by file.

## Critical Paths
- `backend/知识点/`: Source of truth for N1 knowledge.
- `backend/services/knowledge_service.py`: Service used to parse knowledge points.

## Usage
"What does the grammar point '～こそすれ' mean? Search the knowledge base for details."
