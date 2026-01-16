FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching (assumes requirements.txt is in the build context i.e. backend/)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code into a subdirectory named 'backend'
# This allows 'from . import models' to work because we will run it as a module
COPY . ./backend

# Set the python path to include /app so we can import 'backend'
ENV PYTHONPATH=/app

# Run uvicorn on the module backend.main
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
