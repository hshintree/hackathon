# Autonomous Trading Agent - Next.js Frontend Setup

This project now uses a modern Next.js frontend instead of Streamlit for a better user experience and more advanced features.

## 🚀 Quick Start

### Option 1: Use the Launch Script (Recommended)
```bash
./launch_next.sh
```

### Option 2: Manual Launch
1. **Start the FastAPI Backend:**
   ```bash
   source venv/bin/activate
   python api.py
   ```

2. **Start the Next.js Frontend (in a new terminal):**
   ```bash
   cd my-app
   npm run dev
   ```

## 🌐 Access Points

- **Next.js Dashboard:** http://localhost:3000
- **FastAPI Backend:** http://localhost:8080
- **API Documentation:** http://localhost:8080/docs

## 📁 Project Structure

```
hackathon/
├── api.py                 # FastAPI backend
├── my-app/               # Next.js frontend
│   ├── app/
│   │   ├── page.tsx      # Main dashboard
│   │   ├── trading-dashboard/
│   │   ├── agent-network/
│   │   ├── strategy-operations/
│   │   ├── market-intelligence/
│   │   └── system-health/
│   ├── components/       # UI components
│   └── package.json
├── launch_next.sh        # Launch script
└── start_app.py          # Old Streamlit launcher
```

## 🔧 API Endpoints

The Next.js frontend connects to these FastAPI endpoints:

- `GET /api/system/status` - Overall system health and metrics
- `GET /api/portfolio/pnl` - Real-time P&L calculations
- `GET /api/agents/status` - Active agent count and status
- `GET /api/strategies/active` - Running strategy count
- `GET /api/market/status` - Market hours and trading status

## 🎨 Features

### Modern UI Components
- **Responsive Design:** Works on desktop and mobile
- **Dark Theme:** Professional trading interface
- **Real-time Updates:** Live data from the backend
- **Interactive Charts:** Advanced visualization capabilities

### Dashboard Sections
1. **Trading Dashboard** - Portfolio overview and positions
2. **AI Agents** - Agent status and management
3. **Strategies** - Active trading strategies
4. **Market Intelligence** - Market data and analysis
5. **System Health** - System monitoring and alerts

## 🔄 Migration from Streamlit

The old Streamlit frontend (`app.py`) is still available but no longer the default. To use it:

```bash
streamlit run app.py
```

## 🛠️ Development

### Frontend Development
```bash
cd my-app
npm run dev          # Development server
npm run build        # Production build
npm run lint         # Code linting
```

### Backend Development
```bash
source venv/bin/activate
python api.py        # Development server
```

## 📦 Dependencies

### Backend (Python)
- FastAPI
- Uvicorn
- LangGraph
- Alpaca-py
- And more (see requirements.txt)

### Frontend (Node.js)
- Next.js 15
- React 19
- Tailwind CSS
- Radix UI
- Lucide React

## 🔍 Troubleshooting

### Common Issues

1. **Port 3000 already in use:**
   ```bash
   lsof -ti:3000 | xargs kill -9
   ```

2. **Port 8080 already in use:**
   ```bash
   lsof -ti:8080 | xargs kill -9
   ```

3. **Node modules missing:**
   ```bash
   cd my-app
   npm install
   ```

4. **Python dependencies missing:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Environment Variables
Make sure you have the required API keys set:
- `FINNHUB_API_KEY`
- `APCA_API_KEY_ID`
- `FRED_API_KEY`
- `TAVILY_API_KEY`

## 🎯 Next Steps

1. **Connect Real Data:** Replace mock data with real API calls
2. **Add WebSocket Support:** Real-time updates
3. **Implement Authentication:** User login system
4. **Add More Charts:** Advanced trading visualizations
5. **Mobile App:** React Native version

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation at http://localhost:8080/docs
3. Check the browser console for frontend errors 