#!/usr/bin/env python3
"""
Autonomous Trading Agent - Local Demo
A simplified version that demonstrates the key components locally.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from data_sources.alpaca_client import AlpacaClient
from data_sources.sec_edgar_client import SECEdgarClient
from data_sources.fred_client import FREDClient
from data_sources.binance_client import BinanceClient
from database.storage import DataStorage
import os
from fredapi import Fred
import asyncio
import time
import requests


def main():
    st.set_page_config(
        page_title="Autonomous Trading Agent 🤖📈",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🤖 Autonomous Trading Agent Dashboard")
    st.markdown("*Gigacontext Financial AI with Real-time Analysis*")

    # Sidebar for controls
    st.sidebar.header("🎛️ Agent Controls")

    # Check API keys
    api_status = check_api_keys()
    st.sidebar.markdown("### 🔑 API Status")
    for api, status in api_status.items():
        emoji = "✅" if status else "❌"
        st.sidebar.markdown(f"{emoji} {api}")

    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📊 Live Market Data",
            "🧠 Agent Reasoning",
            "📈 Portfolio Analysis",
            "⚡ Modal Compute",
        ]
    )

    with tab1:
        show_market_data()

    with tab2:
        show_agent_reasoning()

    with tab3:
        show_portfolio_analysis()

    with tab4:
        show_modal_compute()


def check_api_keys():
    """Check which API keys are available"""
    return {
        "Finnhub": bool(os.getenv("FINNHUB_API_KEY")),
        "Alpaca": bool(os.getenv("APCA_API_KEY_ID")),
        "FRED": bool(os.getenv("FRED_API_KEY")),
        "Tavily": bool(os.getenv("TAVILY_API_KEY")),
    }


def show_market_data():
    """Display live market data and analysis"""
    st.header("📊 Real-time Market Intelligence")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Stock selection
        symbols = st.multiselect(
            "Select stocks to analyze:",
            ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN"],
            default=["AAPL", "TSLA"],
        )

        if symbols:
            # Fetch and display data
            data = fetch_market_data(symbols)
            if not data.empty:
                fig = create_price_chart(data, symbols)
                st.plotly_chart(fig, use_container_width=True)

                # Show recent data
                st.subheader("📋 Recent Price Data")
                st.dataframe(data.tail(10), use_container_width=True)

    with col2:
        st.subheader("🎯 AI Analysis")
        if symbols:
            for symbol in symbols:
                with st.expander(f"Analysis: {symbol}"):
                    analysis = generate_mock_analysis(symbol)
                    st.markdown(analysis)


def show_agent_reasoning():
    """Show the multi-agent reasoning process"""
    st.header("🧠 Multi-Agent Reasoning Layer")

    # Simulate agent conversations
    agents = {
        "🌍 Macro Analyst": "Analyzing global economic indicators and regime changes...",
        "🔬 Quant Research": "Running Monte Carlo simulations on 10,000 assets...",
        "⚠️ Risk Manager": "Monitoring portfolio drawdown and exposure limits...",
        "⚡ Execution Agent": "Preparing optimal order execution strategies...",
    }

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🤖 Agent Status")
        for agent, status in agents.items():
            st.info(f"**{agent}**\n{status}")

    with col2:
        st.subheader("💬 Agent Conversations")

        # Mock conversation log
        conversations = [
            (
                "🌍 Macro Analyst",
                "Fed meeting minutes suggest dovish stance. Recommending growth allocation increase.",
            ),
            (
                "⚠️ Risk Manager",
                "Current portfolio VaR at 2.3%. Within acceptable limits.",
            ),
            (
                "🔬 Quant Research",
                "Momentum factor showing strong alpha in tech sector. Confidence: 87%",
            ),
            (
                "⚡ Execution Agent",
                "Optimal execution window identified: 2:30-3:00 PM EST",
            ),
        ]

        for agent, message in conversations:
            st.chat_message("assistant").write(f"**{agent}**: {message}")


def show_portfolio_analysis():
    """Display portfolio performance and analytics"""
    st.header("📈 Portfolio Performance Analytics")

    # Generate mock portfolio data
    dates = pd.date_range(start="2024-01-01", end=datetime.now(), freq="D")
    returns = np.random.randn(len(dates)) * 0.02
    cumulative_returns = (1 + pd.Series(returns, index=dates)).cumprod()

    col1, col2 = st.columns([3, 1])

    with col1:
        # Portfolio performance chart
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cumulative_returns,
                mode="lines",
                name="Portfolio Value",
                line=dict(color="#00ff88", width=2),
            )
        )
        fig.update_layout(
            title="Portfolio Performance (YTD)",
            xaxis_title="Date",
            yaxis_title="Cumulative Returns",
            template="plotly_dark",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Key Metrics")

        # Calculate metrics
        total_return = (cumulative_returns.iloc[-1] - 1) * 100
        volatility = returns.std() * np.sqrt(252) * 100
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
        max_dd = (
            (cumulative_returns / cumulative_returns.expanding().max()) - 1
        ).min() * 100

        st.metric("Total Return", f"{total_return:.1f}%")
        st.metric("Volatility", f"{volatility:.1f}%")
        st.metric("Sharpe Ratio", f"{sharpe:.2f}")
        st.metric("Max Drawdown", f"{max_dd:.1f}%")


def show_modal_compute():
    """Show Modal compute status and data ingestion jobs"""
    st.header("🚀 Modal Compute & Data Status")
    
    try:
        import requests
        response = requests.get("http://localhost:8080/modal/jobs")
        if response.status_code == 200:
            job_data = response.json()
            jobs = job_data.get("jobs", [])
            
            col1, col2, col3, col4 = st.columns(4)
            
            active_jobs = len([j for j in jobs if j["status"] == "running"])
            completed_today = len([j for j in jobs if j["status"] == "completed"])
            failed_jobs = len([j for j in jobs if j["status"] == "failed"])
            
            with col1:
                st.metric("Active Jobs", active_jobs)
            
            with col2:
                st.metric("Completed", completed_today, "+2")
            
            with col3:
                st.metric("Failed", failed_jobs)
            
            with col4:
                st.metric("Total Jobs", len(jobs))
            
            st.subheader("Recent Data Ingestion Jobs")
            
            if jobs:
                df = pd.DataFrame(jobs)
                df = df[['job_id', 'job_type', 'status', 'created_at', 'completed_at', 'error_message']]
                df.columns = ['Job ID', 'Type', 'Status', 'Created', 'Completed', 'Error']
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No jobs found. Start data ingestion to see job status here.")
        else:
            st.error("Failed to fetch job status from API")
            
    except Exception as e:
        st.error(f"Error fetching Modal status: {str(e)}")
    
    st.subheader("📊 Data Sources Status")
    
    try:
        response = requests.get("http://localhost:8080/data/sources")
        if response.status_code == 200:
            sources_data = response.json()
            sources = sources_data.get("sources", [])
            
            for source in sources:
                col1, col2 = st.columns([3, 1])
                with col1:
                    status_icon = "✅" if source["available"] else "❌"
                    st.write(f"{status_icon} **{source['source'].upper()}**")
                    if not source["available"] and source.get("error_message"):
                        st.caption(f"Error: {source['error_message']}")
                with col2:
                    if source["available"]:
                        st.success("Available")
                    else:
                        st.error("Unavailable")
        else:
            st.error("Failed to fetch data source status")
            
    except Exception as e:
        st.error(f"Error fetching data source status: {str(e)}")
    
    st.subheader("🗄️ Database Statistics")
    
    try:
        response = requests.get("http://localhost:8080/data/stats")
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Market Data", f"{stats['market_data_records']:,}")
            
            with col2:
                st.metric("SEC Filings", f"{stats['sec_filings_records']:,}")
            
            with col3:
                st.metric("Macro Data", f"{stats['macro_data_records']:,}")
            
            with col4:
                st.metric("Crypto Data", f"{stats['crypto_data_records']:,}")
            
            st.metric("Total Records", f"{stats['total_records']:,}")
            
        else:
            st.error("Failed to fetch database statistics")
            
    except Exception as e:
        st.error(f"Error fetching database statistics: {str(e)}")
    
    st.subheader("🔄 Manual Data Ingestion")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Trigger Market Data Ingestion"):
            try:
                payload = {
                    "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-15"
                }
                response = requests.post("http://localhost:8080/data/market", json=payload)
                if response.status_code == 200:
                    st.success("Market data ingestion job started!")
                else:
                    st.error("Failed to start market data ingestion")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("Trigger SEC Filings Ingestion"):
            try:
                payload = {
                    "forms": ["10-K", "10-Q"],
                    "limit": 50
                }
                response = requests.post("http://localhost:8080/data/sec", json=payload)
                if response.status_code == 200:
                    st.success("SEC filings ingestion job started!")
                else:
                    st.error("Failed to start SEC filings ingestion")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def fetch_market_data(symbols):
    """Fetch real market data using yfinance"""
    try:
        client = AlpacaClient()
        if len(symbols) == 1:
            data = client.get_market_data_for_symbol(symbols[0], "1mo")
            data = data.set_index('timestamp')
            data.columns = [f"{symbols[0]}_{col}" for col in data.columns]
        else:
            all_data = []
            for symbol in symbols:
                symbol_data = client.get_market_data_for_symbol(symbol, "1mo")
                symbol_data = symbol_data.set_index('timestamp')
                symbol_data.columns = [f"{symbol}_{col}" for col in symbol_data.columns]
                all_data.append(symbol_data)
            data = pd.concat(all_data, axis=1)
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()


def create_price_chart(data, symbols):
    """Create an interactive price chart"""
    fig = go.Figure()

    for symbol in symbols:
        if len(symbols) == 1:
            close_col = f"{symbol}_close"
        else:
            close_col = f"{symbol}_close"

        if close_col in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[close_col],
                    mode="lines",
                    name=symbol,
                    line=dict(width=2),
                )
            )

    fig.update_layout(
        title="Stock Price Movement (30 Days)",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_dark",
        hovermode="x unified",
    )

    return fig


def generate_mock_analysis(symbol):
    """Generate mock AI analysis for a stock"""
    analyses = {
        "AAPL": """
        **Technical Analysis**: Strong uptrend with RSI at 67. Support at $180.
        **Sentiment**: Positive (0.73) - iPhone 15 launch driving optimism.
        **Risk**: Low volatility, high liquidity. Max position: 15%.
        """,
        "TSLA": """
        **Technical Analysis**: Volatile with high beta (2.1). Resistance at $250.
        **Sentiment**: Mixed (0.45) - Production concerns vs. AI optimism.
        **Risk**: High volatility. Recommend 5% max allocation.
        """,
        "GOOGL": """
        **Technical Analysis**: Consolidating near $140. Volume declining.
        **Sentiment**: Positive (0.68) - AI developments and cloud growth.
        **Risk**: Moderate. Regulatory concerns present.
        """,
    }

    return analyses.get(symbol, "Analysis in progress...")


if __name__ == "__main__":
    main()
