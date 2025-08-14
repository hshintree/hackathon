# Enhanced Direct Tool Integration Guide

## Overview

The autonomous trading agent system has been enhanced to use direct tool function calls instead of separate MCP services, providing sophisticated financial analytics with simplified architecture while maintaining Modal deployments for compute-intensive operations.

## System Architecture

### Components
- **Docker Database**: PostgreSQL with pgvector for data storage
- **Direct Tool Functions**: search_text, get_prices, backtest, VaR, portfolio optimization
- **Modal Functions**: Compute-intensive operations (grid_scan, VaR, portfolio optimization)
- **FastAPI Backend**: Enhanced langgraph_agent.py with direct tool integration
- **Next.js Frontend**: Clean interface with real-time query processing

### Key Enhancements
- Direct database access through tool functions (no HTTP overhead)
- Modal web endpoint integration for sophisticated analytics
- Improved intent detection for proper query routing
- USE_MODAL environment variable for flexible deployment
- Simplified architecture without separate MCP services
- Eliminated port conflicts and service management complexity

## Quick Start

### 1. Start Database
```bash
cd ~/repos/hackathon
docker-compose up -d
```

### 2. Initialize Database Schema
```bash
python database/connection.py
```

### 3. Set Environment Variables
```bash
export PYTHONPATH=/home/ubuntu/repos/hackathon:$PYTHONPATH
export USE_MODAL=1
```

### 4. Start Backend
```bash
python -m uvicorn api:app --port 8080 --host 0.0.0.0 &
```

### 5. Start Frontend
```bash
cd simple-query-app
npm run dev
```

### 6. Access System
- Frontend: Port 3000
- Backend API with Direct Tool Integration: Port 8080

## Modal Integration

### Deployed Functions
- **Grid Scan**: `https://hshindy--trading-agent-data-run-grid-scan.modal.run`
- **VaR Computation**: `https://hshindy--trading-agent-data-run-var.modal.run`
- **Portfolio Optimization**: `https://hshindy--trading-agent-data-run-optimize.modal.run`
- **Graph Query**: `https://hshindy--trading-agent-data-query-graph.modal.run`

### Usage Control
Set `USE_MODAL=1` in environment to enable Modal functions for compute-intensive operations. When disabled, system uses direct tool function calls.

## Query Types Supported

### Grid Scan
```
"run grid scan on AAPL with different moving average parameters"
```
- Routes to: quant_node → Modal grid_scan endpoint (or direct backtest function)
- Returns: Parameter optimization results

### Risk Analysis
```
"compute VaR for AAPL and GOOGL portfolio"
```
- Routes to: risk_node → Modal VaR endpoint (or direct VaR function)
- Returns: Value at Risk calculations

### Portfolio Optimization
```
"optimize portfolio allocation for tech stocks"
```
- Routes to: alloc_node → Modal optimization endpoint (or direct optimization function)
- Returns: Optimal weight allocations

### Search Queries
```
"search for recent Apple stock analysis"
```
- Routes to: librarian_node → Direct search_text function
- Returns: Relevant document chunks

## Database Schema

### Key Tables
- `market_data`: Price and volume data
- `text_chunks`: Document embeddings with pgvector
- `sec_filings`: SEC filing data with embeddings
- `news_articles`: News data with sentiment analysis
- `options_contracts`: Options chain data

### Connection Details
- Host: localhost:5432
- Database: trading_agent
- User: postgres
- Password: Y2RUH53T (configured in .env)

## Testing

### Database Connectivity
```bash
python test_db_connection.py
```

### Direct Tool Functions
Direct tool functions are called internally by the backend - no separate services needed.

### Modal Functions
```bash
curl -X POST "https://hshindy--trading-agent-data-run-grid-scan.modal.run" \
  -H "Content-Type: application/json" \
  -d '{"param_grid": {"ma_short": [10, 20], "ma_long": [30, 50]}}'
```

### End-to-End System
```bash
curl -X POST "http://localhost:8080/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "run grid scan on AAPL with different moving average parameters"}'
```

## Environment Variables

### Required
- `USE_MODAL=1`: Enable Modal function integration
- `DB_HOST=localhost`: Database host
- `DB_PORT=5432`: Database port
- `DB_NAME=trading_agent`: Database name
- `DB_USER=postgres`: Database user
- `DB_PASSWORD=Y2RUH53T`: Database password

### Optional
- `OPENAI_API_KEY`: For LLM-based intent detection
- `MCP_*_URL`: Override MCP service URLs

## Troubleshooting

### Database Issues
- Ensure Docker containers are running: `docker-compose ps`
- Check database connectivity: `python test_db_connection.py`
- Verify tables exist: Check output shows all required tables

### Direct Tool Issues
- Verify PYTHONPATH is set correctly
- Check backend logs for tool function errors
- Ensure database connectivity is working

### Modal Issues
- Verify Modal functions are deployed and accessible
- Check Modal app status in Modal dashboard
- Test endpoints directly with curl

### Frontend Issues
- Ensure backend is running on port 8080
- Check browser console for API errors
- Verify query processing shows correct intent classification

## Performance Notes

- Modal functions handle compute-intensive operations efficiently
- Database queries are optimized with proper indexing
- Direct tool calls eliminate HTTP overhead for local operations
- System gracefully degrades when Modal services unavailable

## Security

- Database credentials configured via environment variables
- Modal functions use secure HTTPS endpoints
- No sensitive data logged or exposed in responses
- Proper error handling prevents information leakage
