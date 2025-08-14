#!/usr/bin/env python3
"""
Quick test for setup verification - faster version of simulation tests
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_quick_setup():
    """Quick test of core functionality for setup verification"""
    print("🚀 Quick Setup Verification...")

    # Test environment variables
    required_vars = [
        "FINNHUB_API_KEY",
        "APCA_API_KEY_ID",
        "FRED_API_KEY",
        "TAVILY_API_KEY",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
    else:
        print("✅ All environment variables loaded")

    # Test core imports
    try:
        import yfinance
        import streamlit
        import fastapi
        import pandas
        import numpy
        import vectorbt
        import quantstats

        print("✅ All core packages imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    # Quick market data test
    try:
        import yfinance as yf

        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="2d")  # Smaller dataset for speed
        if not data.empty:
            print("✅ Market data fetch working")
        else:
            print("⚠️ Market data empty")
    except Exception as e:
        print(f"⚠️ Market data test failed: {e}")

    print("✅ Quick setup verification complete!")
    return True


if __name__ == "__main__":
    test_quick_setup()
