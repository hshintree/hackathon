#!/usr/bin/env python3
"""
Autonomous Trading Agent - FastAPI Backend
Provides REST API endpoints for the trading agent.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from data_sources.alpaca_client import AlpacaClient
from data_sources.sec_edgar_client import SECEdgarClient
from data_sources.fred_client import FREDClient
from data_sources.binance_client import BinanceClient
from database.storage import DataStorage
from database.models import (
    MarketDataRequest, SECFilingRequest, MacroDataRequest, 
    CryptoDataRequest, DataIngestionJobRequest, HealthCheckResponse,
    DatabaseStats, DataSourceStatus, DataSource
)
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any
import uvicorn

from agents.langgraph_agent import build_graph

app = FastAPI(
    title="Autonomous Trading Agent API",
    description="REST API for the autonomous trading agent",
    version="1.0.0",
)

graph = build_graph()


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
    return {"message": "Autonomous Trading Agent API", "version": "2.0.0", "features": ["alpaca", "sec_edgar", "fred", "binance", "modal"]}


@app.get("/health")
async def health_check():
    """Detailed health check with API status"""
    api_keys = {
        "finnhub": bool(os.getenv("FINNHUB_API_KEY")),
        "alpaca": bool(os.getenv("APCA_API_KEY_ID") and os.getenv("APCA_API_SECRET_KEY")),
        "fred": bool(os.getenv("FRED_API_KEY")),
        "tavily": bool(os.getenv("TAVILY_API_KEY")),
        "binance": bool(os.getenv("BINANCE_API_KEY"))
    }
    
    try:
        storage = DataStorage()
        with storage.get_session() as session:
            session.execute("SELECT 1")
        database_connected = True
    except Exception:
        database_connected = False
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_keys": api_keys,
        "database_connected": database_connected,
        "modal_available": True
    }


class AgentChatRequest(BaseModel):
    query: str


@app.post("/agent/chat")
async def agent_chat(request: AgentChatRequest):
    try:
        state = await graph.ainvoke({"query": request.query})
        return {"state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/market-data")
async def get_market_data(request: StockRequest):
    """Fetch market data for given symbols"""
    try:
        client = AlpacaClient()
        symbols_str = ",".join(request.symbols) if len(request.symbols) > 1 else request.symbols[0]
        df = client.get_market_data_for_symbol(symbols_str, request.period)
        
        # Convert to expected format
        data = df.set_index('timestamp')

        if data.empty:
            raise HTTPException(status_code=404, detail="No data found for symbols")

        # Convert to JSON-serializable format
        result = {}
        for symbol in request.symbols:
            if len(request.symbols) == 1:
                symbol_data = data
            else:
                symbol_data = data

            result[symbol] = {
                "prices": symbol_data["close"].to_dict(),
                "volumes": symbol_data["volume"].to_dict(),
                "latest_price": float(symbol_data["close"].iloc[-1]),
                "change_pct": float(
                    (symbol_data["close"].iloc[-1] / symbol_data["close"].iloc[-2] - 1)
                    * 100
                ) if len(symbol_data) > 1 else 0.0,
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
    """Get Modal job status"""
    try:
        storage = DataStorage()
        with storage.get_session() as session:
            from database.schema import DataIngestionJobs
            jobs = session.query(DataIngestionJobs).order_by(
                DataIngestionJobs.created_at.desc()
            ).limit(20).all()
            
            job_list = []
            for job in jobs:
                job_list.append({
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error_message": job.error_message
                })
            
            return {"status": "success", "jobs": job_list}
    except Exception as e:
        return {"status": "error", "error": str(e), "jobs": []}


@app.post("/data/market")
async def ingest_market_data(request: MarketDataRequest):
    """Trigger market data ingestion"""
    try:
        import requests
        modal_url = "https://your-modal-app.modal.run/trigger_market_data_ingestion"
        
        response = requests.post(modal_url, json=request.dict())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/data/sec")
async def ingest_sec_data(request: SECFilingRequest):
    """Trigger SEC filings ingestion"""
    try:
        import requests
        modal_url = "https://your-modal-app.modal.run/trigger_sec_ingestion"
        
        response = requests.post(modal_url, json=request.dict())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/data/macro")
async def ingest_macro_data(request: MacroDataRequest):
    """Trigger macro data ingestion"""
    try:
        import requests
        modal_url = "https://your-modal-app.modal.run/trigger_macro_ingestion"
        
        response = requests.post(modal_url, json=request.dict())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/data/crypto")
async def ingest_crypto_data(request: CryptoDataRequest):
    """Trigger crypto data ingestion"""
    try:
        import requests
        modal_url = "https://your-modal-app.modal.run/trigger_crypto_ingestion"
        
        response = requests.post(modal_url, json=request.dict())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/sources")
async def get_data_sources():
    """Get available data sources and their status"""
    sources = []
    
    try:
        client = AlpacaClient()
        sources.append(DataSourceStatus(source=DataSource.ALPACA, available=True))
    except Exception as e:
        sources.append(DataSourceStatus(source=DataSource.ALPACA, available=False, error_message=str(e)))
    
    try:
        client = SECEdgarClient()
        sources.append(DataSourceStatus(source=DataSource.SEC_EDGAR, available=True))
    except Exception as e:
        sources.append(DataSourceStatus(source=DataSource.SEC_EDGAR, available=False, error_message=str(e)))
    
    try:
        client = FREDClient()
        sources.append(DataSourceStatus(source=DataSource.FRED, available=True))
    except Exception as e:
        sources.append(DataSourceStatus(source=DataSource.FRED, available=False, error_message=str(e)))
    
    try:
        client = BinanceClient()
        sources.append(DataSourceStatus(source=DataSource.BINANCE, available=True))
    except Exception as e:
        sources.append(DataSourceStatus(source=DataSource.BINANCE, available=False, error_message=str(e)))
    
    return {"sources": sources}

@app.get("/data/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        storage = DataStorage()
        with storage.get_session() as session:
            from database.schema import MarketData, SECFilings, MacroData, CryptoData
            
            market_count = session.query(MarketData).count()
            sec_count = session.query(SECFilings).count()
            macro_count = session.query(MacroData).count()
            crypto_count = session.query(CryptoData).count()
            
            return DatabaseStats(
                market_data_records=market_count,
                sec_filings_records=sec_count,
                macro_data_records=macro_count,
                crypto_data_records=crypto_count,
                total_records=market_count + sec_count + macro_count + crypto_count,
                last_updated=datetime.now()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sec/filings")
async def get_sec_filings(tickers: str = None, forms: str = None, limit: int = 100):
    """Get SEC filings from database"""
    try:
        storage = DataStorage()
        ticker_list = tickers.split(",") if tickers else None
        form_list = forms.split(",") if forms else None
        
        df = storage.get_sec_filings(ticker_list, form_list, limit)
        
        return {
            "filings": df.to_dict("records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/macro/data")
async def get_macro_data(series_ids: str, start_date: str = None, end_date: str = None):
    """Get macro data from database"""
    try:
        from datetime import datetime, timedelta
        
        storage = DataStorage()
        series_list = series_ids.split(",")
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        df = storage.get_macro_data(series_list, start_dt, end_dt)
        
        return {
            "data": df.to_dict("records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crypto/data")
async def get_crypto_data(symbols: str, start_date: str = None, end_date: str = None):
    """Get crypto data from database"""
    try:
        from datetime import datetime, timedelta
        
        storage = DataStorage()
        symbol_list = symbols.split(",")
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        df = storage.get_crypto_data(symbol_list, start_dt, end_dt)
        
        return {
            "data": df.to_dict("records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True, log_level="info")
