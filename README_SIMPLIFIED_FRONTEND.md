# Simplified Query Frontend

This directory contains a simplified frontend interface for the Autonomous Trading Agent that focuses on query input and result visualization.

## Features

- **Clean Query Interface**: Simple textarea for entering natural language queries
- **Real-time Results**: Displays results from the autonomous trading agent
- **Multiple Result Types**: Handles search, backtest, risk analysis, and portfolio optimization results
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: Graceful error display and loading states

## Architecture

The frontend connects to the existing FastAPI backend at `http://localhost:8080` and uses the `/agent/chat` endpoint to execute queries through the LangGraph agent system.

### Query Flow
1. User enters query in frontend
2. Frontend sends POST to `/agent/chat`
3. Backend routes through LangGraph agent
4. Agent determines intent and executes appropriate tools
5. Results flow back to frontend for visualization

## Setup

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running FastAPI backend on port 8080

### Installation
```bash
cd simple-query-app
npm install
```

### Environment Variables
Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### Development
```bash
npm run dev
```
Access at: http://localhost:3000

### Production Build
```bash
npm run build
npm start
```

## Usage Examples

### Search Queries
- "search for recent Apple stock analysis"
- "find information about Tesla earnings"
- "get market sentiment for tech stocks"

### Backtest Queries  
- "run backtest on AAPL with moving average strategy"
- "backtest momentum strategy on SPY"
- "test mean reversion on QQQ"

### Risk Analysis Queries
- "compute VaR for my portfolio"
- "stress test portfolio against market crash"
- "analyze portfolio risk metrics"

### Portfolio Optimization Queries
- "optimize portfolio allocation"
- "rebalance portfolio for maximum Sharpe ratio"
- "optimize allocation for tech stocks"

## Components

### QueryInterface.tsx
Main component handling:
- Query input form
- API communication
- Result rendering
- Error handling
- Loading states

### API Client (lib/api.ts)
- Handles communication with FastAPI backend
- Type-safe request/response interfaces
- Error handling and retries

## Styling

Based on the existing my-app design system:
- **Dark theme**: `bg-neutral-950` background
- **Emerald accents**: `text-emerald-400` for highlights
- **Consistent spacing**: Tailwind CSS utilities
- **Responsive design**: Mobile-first approach

## Integration

The frontend integrates with:
- **FastAPI Backend**: Main API server
- **LangGraph Agent**: Query orchestration
- **MCP Services**: Specialized agent tools
- **Modal Functions**: Cloud compute for intensive operations

## Development Notes

- Built with Next.js 14 and TypeScript
- Uses Tailwind CSS for styling
- Lucide React for icons
- No external UI library dependencies
- Follows the existing codebase patterns
