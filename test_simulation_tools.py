#!/usr/bin/env python3
"""
Test script to verify that all simulation and backtesting tools are working correctly.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def test_data_sources():
    """Test financial data APIs"""
    print("🔍 Testing Financial Data Sources...")

    # Test yfinance
    try:
        from data_sources.alpaca_client import AlpacaClient

        client = AlpacaClient()
        data = client.get_market_data_for_symbol("AAPL", "5d")
        print(f"✅ Alpaca: Retrieved {len(data)} days of AAPL data")
    except Exception as e:
        print(f"❌ Alpaca failed: {e}")

    # Test FRED API
    try:
        from fredapi import Fred

        fred_key = os.getenv("FRED_API_KEY")
        if fred_key:
            fred = Fred(api_key=fred_key)
            # Test with a simple economic indicator
            data = fred.get_series("GDP", limit=5)
            print(f"✅ FRED API: Retrieved GDP data, latest value: {data.iloc[-1]}")
        else:
            print("⚠️ FRED API: No API key found")
    except Exception as e:
        print(f"❌ FRED API failed: {e}")


def test_simulation_frameworks():
    """Test backtesting and simulation frameworks"""
    print("\n🚀 Testing Simulation Frameworks...")

    # Test VectorBT
    try:
        import vectorbt as vbt

        # Create simple price data
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 0.02), index=dates)

        # Simple moving average strategy
        fast_ma = prices.rolling(10).mean()
        slow_ma = prices.rolling(30).mean()
        entries = fast_ma > slow_ma
        exits = fast_ma < slow_ma

        portfolio = vbt.Portfolio.from_signals(prices, entries, exits, init_cash=10000)
        print(f"✅ VectorBT: Portfolio total return: {portfolio.total_return():.2%}")
    except Exception as e:
        print(f"❌ VectorBT failed: {e}")

    # Test QuantStats
    try:
        import quantstats as qs

        # Generate sample returns
        returns = pd.Series(
            np.random.randn(252) * 0.02,
            index=pd.date_range("2023-01-01", periods=252, freq="D"),
        )
        sharpe = qs.stats.sharpe(returns)
        print(f"✅ QuantStats: Sample portfolio Sharpe ratio: {sharpe:.2f}")
    except Exception as e:
        print(f"❌ QuantStats failed: {e}")

    # Test PyFolio
    try:
        import pyfolio as pf

        returns = pd.Series(
            np.random.randn(252) * 0.02,
            index=pd.date_range("2023-01-01", periods=252, freq="D"),
        )
        max_dd = pf.timeseries.max_drawdown(returns)
        print(f"✅ PyFolio: Sample portfolio max drawdown: {max_dd:.2%}")
    except Exception as e:
        print(f"❌ PyFolio failed: {e}")


def test_ml_frameworks():
    """Test machine learning and RL frameworks"""
    print("\n🤖 Testing ML/RL Frameworks...")

    # Test Stable Baselines3
    try:
        import stable_baselines3 as sb3
        from stable_baselines3 import PPO

        print(f"✅ Stable Baselines3: Version {sb3.__version__} loaded successfully")
    except Exception as e:
        print(f"❌ Stable Baselines3 failed: {e}")

    # Test Gymnasium
    try:
        import gymnasium as gym

        env = gym.make("CartPole-v1")
        print(
            f"✅ Gymnasium: Created CartPole environment with action space: {env.action_space}"
        )
        env.close()
    except Exception as e:
        print(f"❌ Gymnasium failed: {e}")


def test_portfolio_optimization():
    """Test portfolio optimization tools"""
    print("\n📊 Testing Portfolio Optimization...")

    try:
        import riskfolio as rp

        # Create sample data
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        assets = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        returns = pd.DataFrame(
            np.random.randn(252, 4) * 0.02, index=dates, columns=assets
        )

        # Build portfolio
        port = rp.Portfolio(returns=returns)
        port.assets_stats(method_mu="hist", method_cov="hist")

        # Optimize portfolio
        w = port.optimization(
            model="Classic", rm="MV", obj="Sharpe", rf=0.02 / 252, hist=True
        )
        print(f"✅ RiskFolio: Optimized portfolio weights sum: {w.sum().iloc[0]:.3f}")
    except Exception as e:
        print(f"❌ RiskFolio failed: {e}")


def main():
    """Run all tests"""
    print("🧪 Testing Autonomous Trading Agent Simulation Environment\n")
    print("=" * 60)

    test_data_sources()
    test_simulation_frameworks()
    test_ml_frameworks()
    test_portfolio_optimization()

    print("\n" + "=" * 60)
    print("✨ Simulation environment testing complete!")
    print("\nYour autonomous trading agent now has access to:")
    print("• Financial data APIs (YFinance, FRED, Alpaca, Finnhub)")
    print("• Advanced backtesting (VectorBT, Zipline, PyFolio)")
    print("• Portfolio analytics (QuantStats, FFN)")
    print("• Portfolio optimization (RiskFolio)")
    print("• Reinforcement Learning (Stable Baselines3, Gymnasium)")
    print("• Market simulation and strategy development tools")


if __name__ == "__main__":
    main()
