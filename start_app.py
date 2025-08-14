#!/usr/bin/env python3
"""
Startup script for the Autonomous Trading Agent
Runs both the FastAPI backend and Next.js frontend
"""

import subprocess
import time
import sys
import os
import signal
from pathlib import Path


def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import yfinance

        print("✅ All Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False


def check_node_dependencies():
    """Check if Node.js dependencies are installed"""
    my_app_path = Path(__file__).parent / "my-app"
    package_json = my_app_path / "package.json"
    node_modules = my_app_path / "node_modules"
    
    if not package_json.exists():
        print("❌ my-app/package.json not found")
        return False
    
    if not node_modules.exists():
        print("⚠️  Node.js dependencies not installed")
        print("Installing Node.js dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=my_app_path, check=True)
            print("✅ Node.js dependencies installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install Node.js dependencies")
            return False
    
    return True


def check_environment():
    """Check if environment variables are set"""
    required_vars = [
        "FINNHUB_API_KEY",
        "APCA_API_KEY_ID",
        "FRED_API_KEY",
        "TAVILY_API_KEY",
    ]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Some features may not work properly.")
        print("Please check your .env file or run 'direnv allow'")
    else:
        print("✅ All environment variables are set")

    return len(missing_vars) == 0


def start_services():
    """Start both FastAPI and Next.js services"""
    print("🚀 Starting Autonomous Trading Agent...")

    # Start FastAPI backend
    print("📡 Starting FastAPI backend on http://localhost:8080")
    api_process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import uvicorn; from api import app; uvicorn.run(app, host='0.0.0.0', port=8080, log_level='info')",
        ],
        cwd=Path(__file__).parent,
    )

    # Wait a moment for API to start
    time.sleep(3)

    # Start Next.js frontend
    print("🎨 Starting Next.js dashboard on http://localhost:3000")
    my_app_path = Path(__file__).parent / "my-app"
    nextjs_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=my_app_path,
        env={**os.environ, "PORT": "3000"}
    )

    print("\n" + "=" * 60)
    print("🤖 AUTONOMOUS TRADING AGENT IS RUNNING!")
    print("=" * 60)
    print("🎨 Next.js Dashboard: http://localhost:3000")
    print("📡 FastAPI Backend: http://localhost:8080")
    print("📚 API Docs: http://localhost:8080/docs")
    print("=" * 60)
    print("Press Ctrl+C to stop all services")
    print("=" * 60)

    def signal_handler(sig, frame):
        print("\n🛑 Shutting down services...")
        api_process.terminate()
        nextjs_process.terminate()
        print("✅ All services stopped")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Wait for processes
        api_process.wait()
        nextjs_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)


def main():
    """Main startup function"""
    print("🧪 Checking system requirements...")

    if not check_dependencies():
        sys.exit(1)

    if not check_node_dependencies():
        sys.exit(1)

    check_environment()

    start_services()


if __name__ == "__main__":
    main()
