#!/bin/bash

echo "🚀 Starting Exam Grading Backend..."

# Optional: activate venv if you use one
if [ -d "venv" ]; then
    source venv/bin/activate
fi

uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
