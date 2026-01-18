# Agentic Setup for Japanese N1 Quiz App

This project is optimized for AI agents using the `.agent` configuration directory.

## Directory Structure

- `.agent/skills/`: Specialized capabilities for the agent.
    - `n1-knowledge`: Research grammar and vocabulary.
    - `n1-progress`: Analyze user learning trends.
    - `n1-quiz`: Content generation and management.
- `.agent/workflows/`: Standard operating procedures for the agent.
- `.agent/task.md`: Active task tracking (view with `view_file`).

## How to use Skills

Agents can invoke scripts within the `scripts/` directory of each skill to perform complex operations. For example:
- `python .agent/skills/n1-knowledge/scripts/search_knowledge.py "～を皮切りに"`

## How to use Workflows

Workflows provide step-by-step instructions for multi-stage tasks. Follow them strictly to ensure consistency.
