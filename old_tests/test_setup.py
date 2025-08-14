#!/usr/bin/env python3
"""
Test script to verify the trading agent setup is working correctly.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all major packages can be imported."""
    print("🧪 Testing package imports...")
    
    try:
        import fastapi
        import uvicorn
        import streamlit
        print("✅ Web framework imports successful")
    except ImportError as e:
        print(f"❌ Web framework import failed: {e}")
        return False
    
    try:
        import pandas as pd
        import numpy as np
        print("✅ Data processing imports successful")
    except ImportError as e:
        print(f"❌ Data processing import failed: {e}")
        return False
    
    try:
        import alpaca
        import finnhub
        import fredapi
        import yfinance
        print("✅ Financial API imports successful")
    except ImportError as e:
        print(f"❌ Financial API import failed: {e}")
        return False
    
    try:
        import openai
        import anthropic
        import langchain
        import chromadb
        print("✅ AI/LLM framework imports successful")
    except ImportError as e:
        print(f"❌ AI/LLM framework import failed: {e}")
        return False
    
    try:
        import modal
        import pgvector
        print("✅ Infrastructure imports successful")
    except ImportError as e:
        print(f"❌ Infrastructure import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database connection."""
    print("\n🗄️ Testing database connection...")
    
    try:
        from database.schema import create_database_engine
        engine = create_database_engine()
        
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected: {version}")
            
            # Test pgvector extension
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                print("✅ pgvector extension is available")
            else:
                print("❌ pgvector extension not found")
                return False
                
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_environment():
    """Test environment variables."""
    print("\n🔧 Testing environment variables...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"
    ]
    
    optional_vars = [
        "FINNHUB_API_KEY", "APCA_API_KEY_ID", "FRED_API_KEY", "TAVILY_API_KEY"
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.getenv(var) or os.getenv(var) == f"your_{var.lower()}_here":
            missing_optional.append(var)
    
    if missing_required:
        print(f"❌ Missing required environment variables: {', '.join(missing_required)}")
        return False
    else:
        print("✅ All required environment variables are set")
    
    if missing_optional:
        print(f"⚠️  Missing optional API keys: {', '.join(missing_optional)}")
        print("   Some features may not work without these keys")
    else:
        print("✅ All optional API keys are set")
    
    return True

def test_app_imports():
    """Test that the main applications can be imported."""
    print("\n🚀 Testing application imports...")
    
    try:
        from api import app
        print("✅ FastAPI application imports successfully")
    except Exception as e:
        print(f"❌ FastAPI application import failed: {e}")
        return False
    
    try:
        import app as streamlit_app
        print("✅ Streamlit application imports successfully")
    except Exception as e:
        print(f"❌ Streamlit application import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🤖 Autonomous Trading Agent Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database,
        test_environment,
        test_app_imports
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready to go!")
        print("\n🚀 To start the application, run:")
        print("   python start_app.py")
        print("\n📊 Dashboard will be available at: http://localhost:8501")
        print("📡 API will be available at: http://localhost:8080")
        print("📚 API docs will be available at: http://localhost:8080/docs")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 