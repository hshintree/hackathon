#!/usr/bin/env python3
"""
Basic tests for the Autonomous Trading Agent
Simple tests to verify core functionality works.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def test_environment_variables():
    """Test that required environment variables are set"""
    required_vars = [
        "FINNHUB_API_KEY",
        "APCA_API_KEY_ID",
        "FRED_API_KEY",
        "TAVILY_API_KEY",
    ]

    for var in required_vars:
        assert os.getenv(var) is not None, f"Environment variable {var} is not set"


def test_core_imports():
    """Test that all core packages can be imported"""
    try:
        import yfinance
        import streamlit
        import fastapi
        import pandas
        import numpy
        import plotly

        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import core package: {e}")


def test_market_data_fetch():
    """Test basic market data fetching"""
    try:
        from data_sources.alpaca_client import AlpacaClient

        client = AlpacaClient()
        data = client.get_market_data_for_symbol("AAPL", "5d")

        assert not data.empty, "Market data should not be empty"
        assert "close" in data.columns, "Market data should have close column"
        assert len(data) > 0, "Should have at least some data points"

    except Exception as e:
        pytest.fail(f"Market data fetch failed: {e}")


def test_api_health_endpoint():
    """Test that the API health endpoint works"""
    try:
        from api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    except Exception as e:
        pytest.fail(f"API health check failed: {e}")


def test_portfolio_metrics_calculation():
    """Test basic portfolio metrics calculation"""
    # Generate sample returns
    returns = pd.Series(np.random.randn(252) * 0.02)

    # Test basic calculations
    total_return = float((1 + returns).prod() - 1)
    volatility = returns.std() * np.sqrt(252)

    assert isinstance(total_return, float), "Total return should be a float"
    assert isinstance(volatility, float), "Volatility should be a float"
    assert volatility > 0, "Volatility should be positive"


def test_app_syntax():
    """Test that main app files have valid syntax"""
    import py_compile

    files_to_check = ["app.py", "api.py", "start_app.py"]

    for file in files_to_check:
        if os.path.exists(file):
            try:
                py_compile.compile(file, doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Syntax error in {file}: {e}")


if __name__ == "__main__":
    # Run tests directly if called as script
    pytest.main([__file__, "-v"])
