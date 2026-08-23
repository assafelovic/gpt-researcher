#!/bin/bash
set -e
cd /home/gian/Documents/gpt-researcher
OUTPUT=/tmp/gptr_setup_output.txt
exec > "$OUTPUT" 2>&1

echo "=== STEP 1: Python version ==="
.venv/bin/python3 --version
echo ""

echo "=== STEP 2: Install dependencies ==="
source .venv/bin/activate
pip install -r requirements.txt 2>&1
echo ""

echo "=== STEP 3: Check key packages ==="
pip list 2>&1 | grep -iE "fastapi|uvicorn|langchain|openai|tavily"
echo ""

echo "=== STEP 4: Try importing app ==="
python -c "from backend.server.app import app; print('Import OK')" 2>&1
echo ""

echo "=== DONE ==="
