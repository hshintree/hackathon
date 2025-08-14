#!/bin/bash


echo "🚀 Starting Autonomous Trading Agent System..."

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

echo "🔧 Starting FastAPI backend on port 8080..."
python api.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

echo "⏳ Waiting for backend to initialize..."
sleep 5

echo "🏥 Testing backend health..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "📦 Setting up frontend dependencies..."
cd my-app
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
echo "   🔧 Backend API: http://localhost:8080"
echo "   📚 API Documentation: http://localhost:8080/docs"
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
    echo "✅ System stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

wait
