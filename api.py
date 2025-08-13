#!/usr/bin/env python3
"""
Autonomous Trading Agent - FastAPI Backend
Provides REST API endpoints for the trading agent.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any
import uvicorn

app = FastAPI(
    title="Autonomous Trading Agent API",
    description="REST API for the autonomous trading agent",
    version="1.0.0",
)


class StockRequest(BaseModel):
    symbols: List[str]
    period: str = "30d"


class PortfolioMetrics(BaseModel):
    total_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Autonomous Trading Agent API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Detailed health check with API status"""
    api_status = {
        "finnhub": bool(os.getenv("FINNHUB_API_KEY")),
        "alpaca": bool(os.getenv("APCA_API_KEY_ID")),
        "fred": bool(os.getenv("FRED_API_KEY")),
        "tavily": bool(os.getenv("TAVILY_API_KEY")),
    }

    return {
        "status": "healthy",
        "api_keys": api_status,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/market-data")
async def get_market_data(request: StockRequest):
    """Fetch market data for given symbols"""
    try:
        data = yf.download(request.symbols, period=request.period, interval="1d")

        if data.empty:
            raise HTTPException(status_code=404, detail="No data found for symbols")

        # Convert to JSON-serializable format
        result = {}
        for symbol in request.symbols:
            if len(request.symbols) == 1:
                symbol_data = data
            else:
                symbol_data = data.xs(symbol, level=1, axis=1)

            result[symbol] = {
                "prices": symbol_data["Close"].to_dict(),
                "volumes": symbol_data["Volume"].to_dict(),
                "latest_price": float(symbol_data["Close"].iloc[-1]),
                "change_pct": float(
                    (symbol_data["Close"].iloc[-1] / symbol_data["Close"].iloc[-2] - 1)
                    * 100
                ),
            }

        return {
            "symbols": request.symbols,
            "period": request.period,
            "data": result,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching market data: {str(e)}"
        )


@app.get("/portfolio/metrics")
async def get_portfolio_metrics():
    """Get current portfolio performance metrics"""
    # Generate mock portfolio data for demo
    dates = pd.date_range(start="2024-01-01", end=datetime.now(), freq="D")
    returns = np.random.randn(len(dates)) * 0.02
    cumulative_returns = (1 + pd.Series(returns, index=dates)).cumprod()

    # Calculate metrics
    total_return = (cumulative_returns.iloc[-1] - 1) * 100
    volatility = returns.std() * np.sqrt(252) * 100
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
    max_dd = (
        (cumulative_returns / cumulative_returns.expanding().max()) - 1
    ).min() * 100

    return PortfolioMetrics(
        total_return=round(total_return, 2),
        volatility=round(volatility, 2),
        sharpe_ratio=round(sharpe, 2),
        max_drawdown=round(max_dd, 2),
    )


@app.get("/agents/status")
async def get_agent_status():
    """Get status of all trading agents"""
    return {
        "agents": {
            "macro_analyst": {
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "message": "Analyzing Fed meeting minutes and global economic indicators",
            },
            "quant_research": {
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "message": "Running Monte Carlo simulations on 10,000 assets",
            },
            "risk_manager": {
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "message": "Portfolio VaR at 2.3%, within acceptable limits",
            },
            "execution_agent": {
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "message": "Optimal execution window: 2:30-3:00 PM EST",
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/modal/jobs")
async def get_modal_jobs():
    """Get status of Modal compute jobs"""
    return {
        "jobs": [
            {
                "name": "Market Data Ingestion",
                "status": "running",
                "workers": 12,
                "duration": "00:45:23",
                "cost": "$2.34",
            },
            {
                "name": "Sentiment Analysis",
                "status": "queued",
                "workers": 0,
                "duration": "00:00:00",
                "cost": "$0.00",
            },
            {
                "name": "Portfolio Optimization",
                "status": "completed",
                "workers": 8,
                "duration": "00:12:45",
                "cost": "$1.23",
            },
            {
                "name": "Risk Simulation",
                "status": "running",
                "workers": 24,
                "duration": "00:23:12",
                "cost": "$4.56",
            },
        ],
        "total_active_workers": 36,
        "total_cost_today": "$8.13",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True, log_level="info")
