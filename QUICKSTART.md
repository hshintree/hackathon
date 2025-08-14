# 🚀 Quick Start Guide - Autonomous Trading Agent

## ✅ Setup Complete!

Your autonomous trading agent environment is now fully set up and ready to use!

## 🎯 What's Installed

### Core Framework
- ✅ **FastAPI** - High-performance API backend
- ✅ **Streamlit** - Interactive dashboard frontend
- ✅ **PostgreSQL + pgvector** - Vector database for embeddings
- ✅ **Modal** - Serverless compute orchestration

### Financial Data APIs
- ✅ **Alpaca** - Paper trading and market data
- ✅ **Finnhub** - Real-time financial data
- ✅ **FRED** - Economic data from Federal Reserve
- ✅ **Yahoo Finance** - Historical market data

### AI/LLM Frameworks
- ✅ **OpenAI** - GPT models integration
- ✅ **Anthropic** - Claude models integration
- ✅ **LangChain** - LLM application framework
- ✅ **ChromaDB** - Vector database for embeddings

### Data Processing
- ✅ **Pandas/NumPy** - Data manipulation
- ✅ **Scikit-learn** - Machine learning
- ✅ **Statsmodels** - Statistical analysis
- ✅ **Backtrader** - Backtesting framework

## 🚀 Starting the Application

### Option 1: Start Both Services (Recommended)
```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Start both FastAPI backend and Streamlit frontend
python start_app.py
```

### Option 2: Start Services Separately
```bash
# Terminal 1 - Start FastAPI backend
uvicorn api:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2 - Start Streamlit frontend
streamlit run app.py --server.port 8501
```

## 🌐 Access Points

Once started, you can access:

- **📊 Dashboard**: http://localhost:8501
- **📡 API**: http://localhost:8080
- **📚 API Documentation**: http://localhost:8080/docs
- **🗄️ PgAdmin**: http://localhost:5050 (admin@admin.com / admin)

## 🔑 API Keys Setup

To use all features, you'll need to add your API keys to the `.env` file:

```bash
# Financial APIs (Required for data ingestion)
FINNHUB_API_KEY=your_actual_finnhub_key
APCA_API_KEY_ID=your_actual_alpaca_key_id
APCA_API_SECRET_KEY=your_actual_alpaca_secret_key
FRED_API_KEY=your_actual_fred_api_key

# AI/LLM APIs (Optional - for agent reasoning)
OPENAI_API_KEY=your_actual_openai_key
ANTHROPIC_API_KEY=your_actual_anthropic_key

# Search API (Optional - for web search)
TAVILY_API_KEY=your_actual_tavily_key
```

### Getting API Keys

1. **Finnhub**: https://finnhub.io/register
2. **Alpaca**: https://alpaca.markets/
3. **FRED**: https://fred.stlouisfed.org/docs/api/api_key.html
4. **OpenAI**: https://platform.openai.com/api-keys
5. **Anthropic**: https://console.anthropic.com/
6. **Tavily**: https://tavily.com/

## 🧪 Testing Your Setup

Run the comprehensive test suite:
```bash
python test_setup.py
```

## 📁 Project Structure

```
hackathon/
├── agents/           # Multi-agent system components
├── data_sources/     # Financial data API clients
├── database/         # Database models and schema
├── api.py           # FastAPI backend
├── app.py           # Streamlit frontend
├── start_app.py     # Application launcher
└── test_setup.py    # Setup verification
```

## 🔧 Key Features

### 🤖 Multi-Agent Architecture
- **Orchestrator**: Coordinates all agents
- **Quant**: Quantitative analysis and backtesting
- **Risk Manager**: Portfolio risk assessment
- **Librarian**: Document processing and embeddings
- **Allocator**: Portfolio allocation decisions

### 📊 Data Ingestion
- Real-time market data from multiple sources
- SEC filings analysis with embeddings
- News sentiment analysis
- Economic indicators from FRED

### 🎯 Trading Capabilities
- Paper trading through Alpaca
- Backtesting with multiple frameworks
- Portfolio optimization
- Risk management

### 🧠 AI-Powered Analysis
- Natural language querying of financial data
- Document analysis and summarization
- Sentiment analysis
- Strategy generation

## 🛠️ Development

### Adding New Data Sources
1. Create a new client in `data_sources/`
2. Add ingestion logic in `ingest.py`
3. Update database schema if needed

### Adding New Agents
1. Create agent class in `agents/`
2. Add tools in corresponding `*_tools.py`
3. Update orchestrator to include new agent

### Customizing Strategies
- Modify `agents/quant_tools.py` for new strategies
- Update `agents/risk_tools.py` for risk models
- Customize `agents/alloc_tools.py` for allocation logic

## 🐛 Troubleshooting

### Database Issues
```bash
# Restart database
docker-compose down
docker-compose up -d

# Reset database
docker-compose down -v
docker-compose up -d
python setup_database.py
```

### Package Issues
```bash
# Reinstall packages
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Port Conflicts
- Change ports in `docker-compose.yaml` for database
- Change ports in `start_app.py` for web services

## 📚 Next Steps

1. **Explore the Dashboard**: Start with the Streamlit interface
2. **Check API Docs**: Review available endpoints
3. **Add API Keys**: Configure your financial data sources
4. **Run Data Ingestion**: Start collecting market data
5. **Test Agents**: Try the multi-agent system
6. **Customize**: Modify strategies and add new features

## 🆘 Support

- Check the main `README.md` for detailed documentation
- Review the test files in `old_tests/` for examples
- Examine the Jupyter notebooks for detailed workflows

---

**Happy Trading! 🚀📈** 