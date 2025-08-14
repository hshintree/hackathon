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

echo "🔍 Checking required ports..."
check_port 8080 || echo "   Backend port 8080 is busy"
check_port 3000 || echo "   Frontend port 3000 is busy"
check_port 8001 || echo "   MCP Librarian port 8001 is busy"
check_port 8003 || echo "   MCP Quant port 8003 is busy"
check_port 8004 || echo "   MCP Risk port 8004 is busy"
check_port 8005 || echo "   MCP Allocator port 8005 is busy"

echo "🐳 Starting Docker database..."
docker-compose up -d
sleep 3

echo "🗄️ Initializing database schema..."
python database/connection.py

echo "🔧 Setting up environment..."
export PYTHONPATH=$(pwd):$PYTHONPATH
export USE_MODAL=1

echo "🤖 Starting MCP services..."
echo "   Starting MCP Librarian on port 8001..."
python -m uvicorn agents.mcp_librarian:app --port 8001 --host 0.0.0.0 &
MCP_LIBRARIAN_PID=$!

echo "   Starting MCP Quant on port 8003..."
python -m uvicorn agents.mcp_quant:app --port 8003 --host 0.0.0.0 &
MCP_QUANT_PID=$!

echo "   Starting MCP Risk on port 8004..."
python -m uvicorn agents.mcp_risk:app --port 8004 --host 0.0.0.0 &
MCP_RISK_PID=$!

echo "   Starting MCP Allocator on port 8005..."
python -m uvicorn agents.mcp_allocator:app --port 8005 --host 0.0.0.0 &
MCP_ALLOCATOR_PID=$!

echo "⏳ Waiting for MCP services to initialize..."
sleep 8

echo "🚀 Starting Enhanced FastAPI backend on port 8080..."
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
echo "   🔧 Enhanced Backend API: http://localhost:8080"
echo "   📚 API Documentation: http://localhost:8080/docs"
echo "   🤖 MCP Services:"
echo "      📚 Librarian: http://localhost:8001"
echo "      📊 Quant: http://localhost:8003"
echo "      ⚠️  Risk: http://localhost:8004"
echo "      💼 Allocator: http://localhost:8005"
echo "   🌐 Modal Integration: Enabled (USE_MODAL=1)"
echo ""
echo "🔧 Process IDs:"
echo "   Backend: $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo "   MCP Librarian: $MCP_LIBRARIAN_PID"
echo "   MCP Quant: $MCP_QUANT_PID"
echo "   MCP Risk: $MCP_RISK_PID"
echo "   MCP Allocator: $MCP_ALLOCATOR_PID"
echo ""
echo "🛑 To stop the system:"
echo "   kill $BACKEND_PID $FRONTEND_PID $MCP_LIBRARIAN_PID $MCP_QUANT_PID $MCP_RISK_PID $MCP_ALLOCATOR_PID"
echo "   or press Ctrl+C to stop this script"
echo ""

cleanup() {
    echo ""
    echo "🛑 Shutting down system..."
    kill $BACKEND_PID $FRONTEND_PID $MCP_LIBRARIAN_PID $MCP_QUANT_PID $MCP_RISK_PID $MCP_ALLOCATOR_PID 2>/dev/null
    echo "   Stopping Docker containers..."
    docker-compose down
    echo "✅ System stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

wait
