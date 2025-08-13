# Autonomous Trading Agent 🤖📈

An autonomous trading research & execution agent that can ingest and reason over massive, uncompressed financial contexts — far beyond any single LLM context window — and adapt strategies in near-real-time. 

## 🚀 Key Features

- **Gigacontext Layer**: Continuous ingestion of live price feeds, alternative data, SEC filings, and analyst reports
- **Agentic Reasoning**: Multi-role agent architecture (Macro Analyst, Quant Research, Risk Manager, Execution Agent)
- **High-Performance Compute**: Modal orchestration for large batch inference and distributed backtesting
- **Real-time Dashboard**: Live agent conversations, strategy performance, and natural language querying

## 🛠️ Quick Setup

### Prerequisites
- Python 3.12+ (recommended)
- Git

### 1. Clone and Navigate
```bash
git clone <your-repo-url>
cd hackathon
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note**: If you encounter any installation issues, see the [Troubleshooting](#troubleshooting) section below.

### 3. Set Up Environment Variables
Create your API keys file:
```bash
cp .env.example .env  # If you have an example file, or create manually
```

Add your API keys to `.env`:
```bash
# Financial API Keys
FINNHUB_API_KEY=your_finnhub_key_here
APCA_API_KEY_ID=your_alpaca_key_id
APCA_API_SECRET_KEY=your_alpaca_secret_key
APCA_API_BASE_URL=https://paper-api.alpaca.markets
APCA_DATA_URL=https://data.alpaca.markets
FRED_API_KEY=your_fred_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### 4. Set Up Direnv (Optional but Recommended)
If you have direnv installed:
```bash
direnv allow
```

### 5. Test Installation
```bash
python test_simulation_tools.py
```

You should see all components testing successfully! ✅

## 📦 What's Included

### Core Framework
- **Modal**: Serverless compute orchestration
- **FastAPI**: High-performance API framework
- **LangChain**: LLM application framework
- **OpenAI/Anthropic**: LLM integrations

### Financial Data APIs
- **Alpaca**: Paper trading and market data
- **Finnhub**: Real-time financial data
- **FRED**: Economic data from Federal Reserve
- **Yahoo Finance**: Historical market data
- **Tavily**: AI-powered search

### Advanced Backtesting & Simulation
- **VectorBT**: High-performance vectorized backtesting
- **Zipline-Reloaded**: Algorithmic trading library
- **PyFolio-Reloaded**: Portfolio performance analysis
- **QuantStats**: Portfolio analytics and risk metrics

### Machine Learning & Optimization
- **PyTorch**: Deep learning framework
- **Stable Baselines3**: Reinforcement learning algorithms
- **Gymnasium**: RL environment framework
- **CVXPY**: Convex optimization
- **RiskFolio-Lib**: Portfolio optimization

### Data Processing & Visualization
- **Pandas/NumPy**: Data manipulation
- **Streamlit**: Interactive dashboards
- **Plotly**: Advanced visualizations

## 🔧 Troubleshooting

### Common Installation Issues

#### 1. Package Conflicts
If you see dependency conflicts during installation:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### 2. WebSocket Version Issues
If you encounter websocket-related errors:
```bash
pip install --upgrade websockets
```

#### 3. FinRL Import Errors
FinRL has complex dependencies. If it fails to import:
```bash
pip install alpaca-trade-api
```

#### 4. Compilation Errors (TA-Lib, QuantLib)
Some packages require compilation. If they fail:
- These are optional and the core functionality will work without them
- On Ubuntu/Debian: `sudo apt-get install build-essential`
- On macOS: Install Xcode command line tools

#### 5. CUDA/PyTorch Issues
If you don't have CUDA or want CPU-only PyTorch:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Environment Variables Not Loading
1. Make sure `.env` file is in the project root
2. If using direnv: run `direnv allow` in the project directory
3. Alternatively, manually source: `source .env` (though this won't work with the format we use)

### API Key Issues
- Ensure all API keys are valid and have proper permissions
- For Alpaca: Make sure you're using paper trading URLs for development
- For FRED: Register at https://fred.stlouisfed.org/docs/api/api_key.html

## 🧪 Testing Your Setup

Run the comprehensive test suite:
```bash
python test_simulation_tools.py
```

This will verify:
- ✅ Financial data API connections
- ✅ Backtesting frameworks
- ✅ Machine learning libraries
- ✅ Portfolio optimization tools
- ✅ Environment variable loading

## 🚀 Getting Started

1. **Explore the test file**: `test_simulation_tools.py` shows examples of using each component
2. **Check the environment**: All your API keys should be loaded automatically
3. **Start building**: The environment is ready for your autonomous trading agent!

## 📚 Key Libraries Documentation

- [Modal](https://modal.com/docs) - Serverless compute
- [VectorBT](https://vectorbt.dev/) - Backtesting framework
- [Stable Baselines3](https://stable-baselines3.readthedocs.io/) - RL algorithms
- [RiskFolio](https://riskfolio-lib.readthedocs.io/) - Portfolio optimization
- [LangChain](https://python.langchain.com/) - LLM applications

## 🤝 Contributing

This is a hackathon project! Feel free to:
- Add new data sources
- Implement additional strategies
- Improve the agent architecture
- Enhance the dashboard

## ⚠️ Important Notes

- This uses **paper trading** by default - no real money at risk
- Some packages may have version conflicts - the core functionality will still work
- The `.env` file contains sensitive API keys - never commit it to version control
- For production use, implement proper secret management

---

**Happy Trading! 🚀📊**
