#!/usr/bin/env bash
set -e

echo "Starting PayGuard 360..."
python scripts/reset_demo.py

echo "Starting Backend API on http://127.0.0.1:8000..."
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

echo "Starting Frontend on http://localhost:5173..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
