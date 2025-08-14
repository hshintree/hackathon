# Autonomous Trading Agent - Query Execution Guide

## Overview

This document provides the exact steps for how a user query flows through the autonomous trading agent system, from frontend input to backend processing through MCP agents and Modal functions.

## System Architecture

```
User Query → Frontend → FastAPI Backend → LangGraph Agent → MCP Services → Modal Functions → Results
```

## Detailed Query Execution Flow

### 1. Frontend Query Submission

**Location**: `simple-query-app/components/QueryInterface.tsx`

```typescript
// User enters query in textarea and submits form
const response = await apiClient.chat({ query: userInput })
```

**API Call**: 
- **Method**: POST
- **Endpoint**: `http://localhost:8080/agent/chat`
- **Payload**: `{"query": "user input string"}`

### 2. FastAPI Backend Processing

**Location**: `api.py` lines 121-127

```python
@app.post("/agent/chat")
async def agent_chat(request: AgentChatRequest):
    try:
        state = await graph.ainvoke({"query": request.query})
        return {"state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Process**:
1. Receives POST request with query
2. Calls LangGraph agent with `graph.ainvoke({"query": request.query})`
3. Returns the complete agent state including results

### 3. LangGraph Agent Orchestration

**Location**: `agents/langgraph_agent.py`

The LangGraph agent follows this flow:

#### Step 3.1: Planning Node
**Function**: `plan_node()` (lines 29-50)

```python
def plan_node(state: AgentState) -> AgentState:
    system = (
        "You orchestrate financial tasks by choosing: search_corpus, get_chunk, run_backtest, "
        "grid_scan, compute_var, stress_test, optimize_portfolio. Return a JSON with 'intent' and 'payload'."
    )
    user = f"User: {state['query']}\nReturn a JSON with 'intent' and 'payload'."
    out = chat([{"role":"system","content":system}, {"role":"user","content":user}])
    # Parse LLM response to extract intent and payload
```

**Process**:
1. Sends query to LLM with system prompt
2. LLM determines the intent (search_corpus, run_backtest, etc.)
3. LLM generates payload with parameters for the chosen tool

#### Step 3.2: Routing Node
**Function**: `route_node()` (lines 53-60)

```python
def route_node(state: AgentState) -> AgentState:
    intent = state.get("intent","search_corpus")
    payload = state.get("result",{}).get("payload", {})
    # Prepares state for execution
```

#### Step 3.3: Conditional Routing
**Function**: `choose_next()` (lines 109-119)

Routes to appropriate agent based on intent:
- `search_corpus`, `get_chunk` → **Librarian Agent**
- `run_backtest`, `grid_scan` → **Quant Agent**
- `compute_var`, `stress_test` → **Risk Agent**
- `optimize_portfolio` → **Allocation Agent**

### 4. MCP Agent Execution

Each MCP agent can run as either:
1. **Separate HTTP servers** (ports 8001-8005)
2. **Local fallback** through `agents/orchestrator.py`

#### 4.1: Librarian Agent (Search & Retrieval)
**Location**: `agents/mcp_librarian.py` or local fallback

**Tools**:
- `search_corpus`: Search through financial documents
- `get_chunk`: Retrieve specific document chunks

**Example Query**: "search for recent Apple stock analysis"

#### 4.2: Quant Agent (Backtesting & Analysis)
**Location**: `agents/mcp_quant.py`

**Tools**:
- `run_backtest`: Execute trading strategy backtests
- `grid_scan`: Parameter optimization (can use Modal for scale)

**Example Query**: "run backtest on AAPL with moving average strategy"

**Modal Integration**: 
```python
# If USE_MODAL=1, delegates to Modal function
f = modal.Function.from_name("trading-agent-data", "grid_scan_parent")
job = f.remote(req.param_grid, payload)
```

#### 4.3: Risk Agent (Risk Analysis)
**Location**: `agents/mcp_risk.py`

**Tools**:
- `compute_var`: Value at Risk calculations
- `stress_test`: Portfolio stress testing

**Example Query**: "compute VaR for my portfolio"

#### 4.4: Allocation Agent (Portfolio Optimization)
**Location**: `agents/mcp_alloc.py`

**Tools**:
- `optimize_portfolio`: Portfolio optimization algorithms

**Example Query**: "optimize portfolio allocation for tech stocks"

### 5. Modal Function Execution

**Location**: `modal_app.py`

Modal functions provide scalable compute for intensive operations:

#### Available Functions:
- `ingest_market_data`: Data ingestion from Alpaca
- `ingest_sec_filings`: SEC filing processing
- `grid_scan_parent`: Distributed backtesting
- `optimize_portfolio_advanced`: Advanced portfolio optimization
- `build_graph_index`: Knowledge graph construction
- `query_graph_index`: Graph-based search

**Deployment Status**: 
```bash
modal app list | grep trading
# Shows: trading-agent-data (deployed)
```

### 6. Result Processing and Return

#### 6.1: Agent Result Formatting
Each agent returns structured results:

```python
# Backtest results
{"metrics": {"total_return": 0.15, "sharpe": 1.2, "max_drawdown": -0.08}}

# Search results  
{"results": [{"content": "...", "score": 0.95}, ...]}

# Risk analysis
{"var_95": 0.05, "expected_shortfall": 0.08}
```

#### 6.2: Frontend Visualization
**Location**: `simple-query-app/components/QueryInterface.tsx`

Results are rendered based on intent:
- **Search results**: List of relevant documents with scores
- **Backtest results**: Metrics grid with performance indicators
- **Risk analysis**: Risk metrics and visualizations
- **Portfolio optimization**: Allocation recommendations

## Environment Setup

### Required Environment Variables

```bash
# Financial APIs
FINNHUB_API_KEY=your_key
APCA_API_KEY_ID=your_key  
APCA_API_SECRET_KEY=your_key
FRED_API_KEY=your_key
TAVILY_API_KEY=your_key

# LLM APIs (choose one)
OPENAI_API_KEY=your_key
# OR
ANTHROPIC_API_KEY=your_key

# Modal (for cloud compute)
MODAL_TOKEN_ID=your_token
MODAL_TOKEN_SECRET=your_secret

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_agent
DB_USER=postgres
DB_PASSWORD=postgres
```

### MCP Server Configuration

MCP servers can be started individually:

```bash
# Librarian (port 8001)
cd agents && python -m uvicorn mcp_librarian:app --port 8001

# Data (port 8002)  
cd agents && python -m uvicorn mcp_data:app --port 8002

# Quant (port 8003)
cd agents && python -m uvicorn mcp_quant:app --port 8003

# Risk (port 8004)
cd agents && python -m uvicorn mcp_risk:app --port 8004

# Allocation (port 8005)
cd agents && python -m uvicorn mcp_alloc:app --port 8005
```

**Environment Variables for MCP URLs**:
```bash
MCP_LIBRARIAN_URL=http://localhost:8001
MCP_DATA_URL=http://localhost:8002  
MCP_QUANT_URL=http://localhost:8003
MCP_RISK_URL=http://localhost:8004
MCP_ALLOC_URL=http://localhost:8005
```

## Running the Complete System

### Option 1: Automated Startup
```bash
cd ~/repos/hackathon
chmod +x start_system.sh
./start_system.sh
```

### Option 2: Manual Startup
```bash
# Terminal 1: Backend
cd ~/repos/hackathon
python api.py

# Terminal 2: Frontend  
cd ~/repos/hackathon/simple-query-app
npm install
npm run dev
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## Example Query Flows

### 1. Search Query
```
Input: "search for recent Apple stock analysis"
→ Intent: search_corpus
→ Agent: Librarian
→ Tool: search_corpus
→ Output: List of relevant documents with relevance scores
```

### 2. Backtest Query
```
Input: "run backtest on AAPL with moving average strategy"  
→ Intent: run_backtest
→ Agent: Quant
→ Tool: run_backtest (may use Modal for scale)
→ Output: Performance metrics (return, Sharpe, drawdown)
```

### 3. Risk Query
```
Input: "compute VaR for my portfolio"
→ Intent: compute_var  
→ Agent: Risk
→ Tool: compute_var
→ Output: Risk metrics and analysis
```

### 4. Optimization Query
```
Input: "optimize portfolio allocation"
→ Intent: optimize_portfolio
→ Agent: Allocation  
→ Tool: optimize_portfolio
→ Output: Recommended asset allocations
```

## MCP vs Direct LLM Integration

### Current Architecture: MCP Services
**Pros**:
- Modular and scalable
- Each agent can be deployed independently
- Clear separation of concerns
- Can handle different compute requirements

**Cons**:
- More complex deployment
- Network overhead between services
- Requires managing multiple processes

### Alternative: Direct LLM Tool Calls
**Pros**:
- Simpler deployment (single process)
- Lower latency
- Easier debugging

**Cons**:
- Less scalable for compute-intensive operations
- Harder to distribute across different machines
- All tools must run in same process

### Recommendation
The current MCP architecture provides the best flexibility:
- Use **local fallback** for development and simple deployments
- Use **separate MCP servers** for production and scale
- Use **Modal functions** for compute-intensive operations

The system automatically falls back to local execution if MCP servers are not available, providing the best of both approaches.
