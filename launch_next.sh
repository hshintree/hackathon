#!/bin/bash

# Launch script for Autonomous Trading Agent with Next.js frontend
# This script starts both the FastAPI backend and Next.js frontend

echo "🚀 Starting Autonomous Trading Agent with Next.js Frontend..."

# Function to cleanup processes on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill $FASTAPI_PID 2>/dev/null
    kill $NEXTJS_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if my-app directory exists
if [ ! -d "my-app" ]; then
    echo "❌ my-app directory not found. Please ensure the Next.js frontend is in the my-app directory."
    exit 1
fi

# Activate virtual environment and start FastAPI backend
echo "📡 Starting FastAPI backend on http://localhost:8080"
source venv/bin/activate
python api.py &
FASTAPI_PID=$!

# Wait a moment for FastAPI to start
sleep 3

# Check if FastAPI is running
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "❌ FastAPI backend failed to start"
    kill $FASTAPI_PID 2>/dev/null
    exit 1
fi

echo "✅ FastAPI backend is running"

# Start Next.js frontend
echo "🎨 Starting Next.js dashboard on http://localhost:3000"
cd my-app
npm run dev &
NEXTJS_PID=$!
cd ..

# Wait a moment for Next.js to start
sleep 5

# Check if Next.js is running
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Next.js frontend failed to start"
    kill $FASTAPI_PID 2>/dev/null
    kill $NEXTJS_PID 2>/dev/null
    exit 1
fi

echo "✅ Next.js frontend is running"

echo ""
echo "=" * 60
echo "🤖 AUTONOMOUS TRADING AGENT IS RUNNING!"
echo "=" * 60
echo "🎨 Next.js Dashboard: http://localhost:3000"
echo "📡 FastAPI Backend: http://localhost:8080"
echo "📚 API Docs: http://localhost:8080/docs"
echo "=" * 60
echo "Press Ctrl+C to stop all services"
echo "=" * 60

# Wait for processes
wait 