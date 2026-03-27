#!/bin/bash
cd "$(dirname "$0")"
echo "Starting GPT Researcher server at http://localhost:8000"
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
