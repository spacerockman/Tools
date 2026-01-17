FROM python:3.11-slim

# Install Tesseract OCR and Japanese language data
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-jpn \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching (assumes requirements.txt is in the build context i.e. backend/)
COPY requirements.txt .

# Use BuildKit cache mount to cache pip downloads
# This significantly speeds up rebuilds even when requirements change
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code into a subdirectory named 'backend'
# This allows 'from . import models' to work because we will run it as a module
COPY . ./backend

# Set the python path to include /app so we can import 'backend'
ENV PYTHONPATH=/app

# Run uvicorn on the module backend.main
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
