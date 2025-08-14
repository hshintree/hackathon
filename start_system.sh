#!/bin/bash

echo "🚀 Starting Enhanced Autonomous Trading Agent System..."

if [ ! -f "api.py" ]; then
    echo "❌ Error: Please run this script from the hackathon repository root"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Using .env.example as template"
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys before running the system"
fi

check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

echo "🔍 Checking and cleaning up existing services..."

echo "   Cleaning up existing MCP services..."
pkill -f "uvicorn.*mcp_" 2>/dev/null || true
lsof -ti:8001,8003,8004,8005 2>/dev/null | xargs kill -9 2>/dev/null || true

if docker ps | grep -q "pgvector-db"; then
    echo "🐳 Database container already running - skipping Docker startup"
else
    echo "🐳 Starting Docker database..."
    docker-compose up -d
    sleep 3
fi

echo "🔍 Checking required ports..."
check_port 8080 || echo "   Backend port 8080 is busy"
check_port 3000 || echo "   Frontend port 3000 is busy"

echo "🗄️ Initializing database schema..."
python database/connection.py

echo "🔧 Setting up environment..."
export PYTHONPATH=$(pwd):$PYTHONPATH

echo "   Loading database environment variables..."
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "   ✅ Database credentials loaded: DB_HOST=$DB_HOST, DB_NAME=$DB_NAME"
else
    echo "   ⚠️  .env file not found - using defaults"
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_NAME=trading_agent
    export DB_USER=postgres
    export DB_PASSWORD=Y2RUH53T
fi

export USE_MODAL=1

echo "🚀 Starting Enhanced FastAPI backend with direct tool integration..."
python -m uvicorn api:app --port 8080 --host 0.0.0.0 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

echo "⏳ Waiting for backend to initialize..."
sleep 5

echo "🏥 Testing backend health..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    kill $BACKEND_PID $MCP_LIBRARIAN_PID $MCP_QUANT_PID $MCP_RISK_PID $MCP_ALLOCATOR_PID 2>/dev/null
    exit 1
fi

echo "📦 Setting up frontend dependencies..."
cd simple-query-app
if [ ! -d "node_modules" ]; then
    echo "   Installing npm packages..."
    npm install
fi

echo "🎨 Starting Next.js frontend on port 3000..."
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo "⏳ Waiting for frontend to initialize..."
sleep 10

echo ""
echo "🎉 System startup complete!"
echo ""
echo "📊 Access Points:"
echo "   🎨 Frontend (Query Interface): http://localhost:3000"
echo "   🔧 Enhanced Backend API with Direct Tool Integration: http://localhost:8080"
echo "   📚 API Documentation: http://localhost:8080/docs"
echo "   🌐 Modal Integration: Enabled (USE_MODAL=1)"
echo "   🔧 Direct Tool Calls: Enabled (No MCP services needed)"
echo ""
echo "🔧 Process IDs:"
echo "   Backend: $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "🛑 To stop the system:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or press Ctrl+C to stop this script"
echo ""

cleanup() {
    echo ""
    echo "🛑 Shutting down system..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "   Stopping Docker containers..."
    docker-compose down
    echo "✅ System stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

wait
