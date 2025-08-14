-- Database Schema Updates for Backend Integration
-- Run these SQL commands to add the new tables needed for real backend functionality

-- Agent management table
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'inactive',
    last_activity TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Strategy management table
CREATE TABLE IF NOT EXISTS strategies (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'stopped',
    allocation DECIMAL(15,2) DEFAULT 0,
    pnl DECIMAL(15,2) DEFAULT 0,
    sharpe_ratio DECIMAL(10,4) DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    max_drawdown DECIMAL(10,4) DEFAULT 0,
    trades_count INTEGER DEFAULT 0,
    last_trade_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent decisions table
CREATE TABLE IF NOT EXISTS agent_decisions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) REFERENCES agents(id),
    decision TEXT NOT NULL,
    confidence DECIMAL(3,2),
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- System metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15,4),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Trade history table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    filled_at TIMESTAMP,
    strategy_id VARCHAR(50) REFERENCES strategies(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Portfolio snapshots table
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    total_value DECIMAL(15,2),
    total_pnl DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2),
    realized_pnl DECIMAL(15,2),
    daily_change DECIMAL(15,2),
    daily_change_percent DECIMAL(10,4),
    snapshot_at TIMESTAMP DEFAULT NOW()
);

-- Market data cache table
CREATE TABLE IF NOT EXISTS market_data_cache (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    data_type VARCHAR(20) NOT NULL,
    data JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, data_type)
);

-- News articles table
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source VARCHAR(100),
    sentiment VARCHAR(20),
    impact VARCHAR(20),
    summary TEXT,
    url TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Economic indicators table
CREATE TABLE IF NOT EXISTS economic_indicators (
    id SERIAL PRIMARY KEY,
    indicator_name VARCHAR(100) NOT NULL UNIQUE,
    fred_series_id VARCHAR(20),
    current_value DECIMAL(15,4),
    previous_value DECIMAL(15,4),
    change_value DECIMAL(15,4),
    next_release_date DATE,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Backtest results table
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    period_start DATE,
    period_end DATE,
    returns DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    win_rate DECIMAL(5,2),
    total_trades INTEGER,
    status VARCHAR(20) DEFAULT 'completed',
    results_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_agent_id ON agent_decisions(agent_id);
CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_cache_symbol ON market_data_cache(symbol);
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles(published_at);
CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON backtest_results(strategy_name);

-- Insert initial data for agents
INSERT INTO agents (id, name, status, last_activity) VALUES
('macro-analyst', 'Macro Analyst', 'active', NOW()),
('quant-research', 'Quant Research', 'active', NOW()),
('risk-manager', 'Risk Manager', 'active', NOW()),
('execution-agent', 'Execution Agent', 'active', NOW())
ON CONFLICT (id) DO NOTHING;

-- Insert initial data for strategies
INSERT INTO strategies (id, name, status, allocation, pnl, sharpe_ratio, win_rate, max_drawdown, trades_count) VALUES
('strategy_1', 'Momentum Trading', 'active', 35000, 450.25, 1.85, 68, -5.2, 47),
('strategy_2', 'Mean Reversion', 'active', 25000, 800.50, 2.1, 72, -3.8, 34)
ON CONFLICT (id) DO NOTHING;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres; 