# Japanese N1 Quiz App

A comprehensive tool for preparing for the Japanese N1 exam. This project consists of a FastAPI backend and a Next.js frontend.

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **uv**: An extremely fast Python package installer and resolver (recommended).

## Project Structure

- `backend/`: FastAPI application, database logic, and API endpoints.
- `frontend/`: Next.js web application.
- `knowledge_base/`: Markdown files for quiz content.

## 🚀 Quick Start (Recommended: Docker)

The easiest way to run the application is using Docker.

```bash
# 1. Start the application
docker-compose up --build
```

The application will be available at:
- **Frontend**: [http://localhost:23333](http://localhost:23333)
- **Backend API**: [http://localhost:28888/docs](http://localhost:28888/docs)

*Note: You need to set the `GOOGLE_API_KEY` in environment variable or `.env` file for the backend to work correctly with AI features.*

## 🛠️ Manual Setup

If you prefer to run the services locally without Docker:

### 1. Backend Setup

```bash
# 1. Install dependencies (using uv)
uv sync

# 2. Run the server
# This will start the backend on http://0.0.0.0:28888
python backend/main.py
```
*Note: If you are not using `uv`, you can verify dependencies in `pyproject.toml`.*

### 2. Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start the development server
npm run dev
```

## ⚠️ Important Notes

### Git & Large Files
- **Do not commit `node_modules`**: This project includes a `.gitignore` file that excludes `node_modules`, `.next`, and virtual environment folders.
- **Large File Limits**: GitHub has a file size limit of 100MB. The `.gitignore` prevents large dependency files from being pushed accidentally.
- **Syncing**: If you need to sync with the remote repository, standard `git pull origin master` and `git push origin master` should work smoothly now that the history has been cleaned.

### Configuration
- The backend listens on `0.0.0.0`, allowing access from other devices on your local network.
- Ensure your `knowledge_base` has the correct directory structure if you are adding new quizzes manually.

### ⚡ Performance Optimization
- **Lightweight Build**: All heavy RAG dependencies (PyTorch, FAISS, Tesseract OCR) have been removed to ensure the Docker build takes < 2 minutes.
- **Domestic Mirrors**: Dockerfiles are pre-configured with Tsinghua and Aliyun mirrors for ultra-fast dependency installation in China.
- **Markdown Knowledge Base**: The system uses a high-performance local markdown parser for grammar grounding instead of a vector database.
