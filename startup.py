#!/usr/bin/env python3
"""
Comprehensive startup script for the Autonomous Trading Agent
Initializes database, starts FastAPI backend, and provides status information
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    logger.info("🔍 Checking environment variables...")
    
    required_vars = [
        "FINNHUB_API_KEY",
        "APCA_API_KEY_ID", 
        "APCA_API_SECRET_KEY",
        "FRED_API_KEY",
        "TAVILY_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work properly.")
        return False
    else:
        logger.info("✅ All required environment variables are set")
        return True

def check_database():
    """Check if database is running"""
    logger.info("🗄️  Checking database connection...")
    
    try:
        from database.connection import initialize_database, is_database_connected
        
        if initialize_database():
            logger.info("✅ Database initialized successfully")
            return True
        else:
            logger.error("❌ Database initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")
        return False

def check_dependencies():
    """Check if all Python dependencies are installed"""
    logger.info("📦 Checking Python dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "pandas",
        "numpy",
        "alpaca-py",
        "finnhub-python",
        "fredapi"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ Missing Python packages: {', '.join(missing_packages)}")
        logger.error("Please run: pip install -r requirements.txt")
        return False
    else:
        logger.info("✅ All Python dependencies are installed")
        return True

def check_node_dependencies():
    """Check if Node.js dependencies are installed"""
    logger.info("📦 Checking Node.js dependencies...")
    
    my_app_path = Path(__file__).parent / "my-app"
    package_json = my_app_path / "package.json"
    node_modules = my_app_path / "node_modules"
    
    if not package_json.exists():
        logger.error("❌ my-app/package.json not found")
        return False
    
    if not node_modules.exists():
        logger.warning("⚠️  Node.js dependencies not installed")
        logger.info("Installing Node.js dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=my_app_path, check=True)
            logger.info("✅ Node.js dependencies installed")
        except subprocess.CalledProcessError:
            logger.error("❌ Failed to install Node.js dependencies")
            return False
    
    logger.info("✅ Node.js dependencies are ready")
    return True

def start_services():
    """Start both FastAPI and Next.js services"""
    logger.info("🚀 Starting Autonomous Trading Agent services...")

    # Start FastAPI backend
    logger.info("📡 Starting FastAPI backend on http://localhost:8080")
    api_process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import uvicorn; from api import app; uvicorn.run(app, host='0.0.0.0', port=8080, log_level='info')",
        ],
        cwd=Path(__file__).parent,
    )

    # Wait for API to start
    time.sleep(5)

    # Start Next.js frontend
    logger.info("🎨 Starting Next.js dashboard on http://localhost:3000")
    my_app_path = Path(__file__).parent / "my-app"
    nextjs_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=my_app_path,
        env={**os.environ, "PORT": "3000"}
    )

    logger.info("\n" + "=" * 60)
    logger.info("🤖 AUTONOMOUS TRADING AGENT IS RUNNING!")
    logger.info("=" * 60)
    logger.info("🎨 Next.js Dashboard: http://localhost:3000")
    logger.info("📡 FastAPI Backend: http://localhost:8080")
    logger.info("📚 API Docs: http://localhost:8080/docs")
    logger.info("🔍 Health Check: http://localhost:8080/health")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop all services")
    logger.info("=" * 60)

    def signal_handler(sig, frame):
        logger.info("\n🛑 Shutting down services...")
        api_process.terminate()
        nextjs_process.terminate()
        logger.info("✅ All services stopped")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Wait for processes
        api_process.wait()
        nextjs_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

def test_api_endpoints():
    """Test API endpoints to ensure they're working"""
    logger.info("🧪 Testing API endpoints...")
    
    import requests
    import time
    
    # Wait for API to be ready
    time.sleep(3)
    
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api/system/status", "System status"),
        ("/api/portfolio/pnl", "Portfolio P&L"),
        ("/api/agents/status", "Agent status"),
        ("/api/strategies/active", "Active strategies"),
        ("/api/market/status", "Market status"),
    ]
    
    base_url = "http://localhost:8080"
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ {description}: OK")
            else:
                logger.warning(f"⚠️  {description}: Status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ {description}: Failed - {e}")

def main():
    """Main startup function"""
    logger.info("🧪 Starting Autonomous Trading Agent...")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed")
        sys.exit(1)
    
    if not check_node_dependencies():
        logger.error("❌ Node.js dependency check failed")
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Check database
    if not check_database():
        logger.error("❌ Database check failed")
        sys.exit(1)
    
    # Start services
    start_services()

if __name__ == "__main__":
    main() 