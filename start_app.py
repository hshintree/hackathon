#!/usr/bin/env python3
"""
Startup script for the Autonomous Trading Agent
Runs both the FastAPI backend and Streamlit frontend
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
        import streamlit
        import fastapi
        import uvicorn
        import yfinance

        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False


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
    """Start both FastAPI and Streamlit services"""
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

    # Start Streamlit frontend
    print("🎨 Starting Streamlit dashboard on http://localhost:8501")
    streamlit_process = subprocess.Popen(
        [
            "streamlit",
            "run",
            "app.py",
            "--server.port",
            "8501",
            "--server.address",
            "0.0.0.0",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=Path(__file__).parent,
    )

    print("\n" + "=" * 60)
    print("🤖 AUTONOMOUS TRADING AGENT IS RUNNING!")
    print("=" * 60)
    print("📊 Dashboard: http://localhost:8501")
    print("📡 API: http://localhost:8080")
    print("📚 API Docs: http://localhost:8080/docs")
    print("=" * 60)
    print("Press Ctrl+C to stop all services")
    print("=" * 60)

    def signal_handler(sig, frame):
        print("\n🛑 Shutting down services...")
        api_process.terminate()
        streamlit_process.terminate()
        print("✅ All services stopped")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Wait for processes
        api_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)


def main():
    """Main startup function"""
    print("🧪 Checking system requirements...")

    if not check_dependencies():
        sys.exit(1)

    check_environment()

    start_services()


if __name__ == "__main__":
    main()
