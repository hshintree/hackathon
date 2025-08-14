#!/usr/bin/env python3
"""
Data Service Layer for Backend Integration
Handles all database operations for agents, strategies, trades, and system metrics
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database.connection import get_db_session

logger = logging.getLogger(__name__)

class DataService:
    """Service class for handling all database operations"""
    
    def __init__(self):
        self.session = get_db_session()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    # ===== AGENT MANAGEMENT =====
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent status from database"""
        try:
            result = self.session.execute(
                text("SELECT * FROM agents WHERE id = :agent_id"),
                {"agent_id": agent_id}
            ).fetchone()
            
            if result:
                return dict(result._mapping)
            return None
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return None
    
    def update_agent_activity(self, agent_id: str):
        """Update agent last activity timestamp"""
        try:
            self.session.execute(
                text("UPDATE agents SET last_activity = NOW() WHERE id = :agent_id"),
                {"agent_id": agent_id}
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error updating agent activity: {e}")
            self.session.rollback()
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents with their status"""
        try:
            result = self.session.execute(
                text("SELECT * FROM agents ORDER BY last_activity DESC")
            ).fetchall()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting all agents: {e}")
            return []
    
    def add_agent_decision(self, agent_id: str, decision: str, confidence: float, reasoning: str):
        """Add agent decision to database"""
        try:
            self.session.execute(
                text("""
                    INSERT INTO agent_decisions (agent_id, decision, confidence, reasoning)
                    VALUES (:agent_id, :decision, :confidence, :reasoning)
                """),
                {
                    "agent_id": agent_id,
                    "decision": decision,
                    "confidence": confidence,
                    "reasoning": reasoning
                }
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error adding agent decision: {e}")
            self.session.rollback()
    
    def get_agent_decisions(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get agent decision history"""
        try:
            result = self.session.execute(
                text("""
                    SELECT * FROM agent_decisions 
                    WHERE agent_id = :agent_id 
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """),
                {"agent_id": agent_id, "limit": limit}
            ).fetchall()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting agent decisions: {e}")
            return []
    
    # ===== STRATEGY MANAGEMENT =====
    
    def get_strategy_status(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get strategy status from database"""
        try:
            result = self.session.execute(
                text("SELECT * FROM strategies WHERE id = :strategy_id"),
                {"strategy_id": strategy_id}
            ).fetchone()
            
            if result:
                return dict(result._mapping)
            return None
        except Exception as e:
            logger.error(f"Error getting strategy status: {e}")
            return None
    
    def update_strategy_status(self, strategy_id: str, status: str):
        """Update strategy status"""
        try:
            self.session.execute(
                text("UPDATE strategies SET status = :status WHERE id = :strategy_id"),
                {"strategy_id": strategy_id, "status": status}
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error updating strategy status: {e}")
            self.session.rollback()
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """Get all strategies with their status"""
        try:
            result = self.session.execute(
                text("SELECT * FROM strategies ORDER BY updated_at DESC")
            ).fetchall()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting all strategies: {e}")
            return []
    
    def update_strategy_metrics(self, strategy_id: str, pnl: float, sharpe: float, win_rate: float, max_drawdown: float):
        """Update strategy performance metrics"""
        try:
            self.session.execute(
                text("""
                    UPDATE strategies 
                    SET pnl = :pnl, sharpe_ratio = :sharpe, win_rate = :win_rate, max_drawdown = :max_drawdown
                    WHERE id = :strategy_id
                """),
                {
                    "strategy_id": strategy_id,
                    "pnl": pnl,
                    "sharpe": sharpe,
                    "win_rate": win_rate,
                    "max_drawdown": max_drawdown
                }
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error updating strategy metrics: {e}")
            self.session.rollback()
    
    # ===== TRADE MANAGEMENT =====
    
    def add_trade(self, symbol: str, side: str, quantity: int, price: float, strategy_id: Optional[str] = None):
        """Add trade to database"""
        try:
            self.session.execute(
                text("""
                    INSERT INTO trades (symbol, side, quantity, price, strategy_id, filled_at)
                    VALUES (:symbol, :side, :quantity, :price, :strategy_id, NOW())
                """),
                {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "strategy_id": strategy_id
                }
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error adding trade: {e}")
            self.session.rollback()
    
    def get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent trades"""
        try:
            result = self.session.execute(
                text("""
                    SELECT * FROM trades 
                    ORDER BY filled_at DESC 
                    LIMIT :limit
                """),
                {"limit": limit}
            ).fetchall()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    def get_trades_by_strategy(self, strategy_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trades for a specific strategy"""
        try:
            result = self.session.execute(
                text("""
                    SELECT * FROM trades 
                    WHERE strategy_id = :strategy_id 
                    ORDER BY filled_at DESC 
                    LIMIT :limit
                """),
                {"strategy_id": strategy_id, "limit": limit}
            ).fetchall()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting trades by strategy: {e}")
            return []
    
    # ===== PORTFOLIO MANAGEMENT =====
    
    def add_portfolio_snapshot(self, total_value: float, total_pnl: float, unrealized_pnl: float, 
                              realized_pnl: float, daily_change: float, daily_change_percent: float):
        """Add portfolio snapshot to database"""
        try:
            self.session.execute(
                text("""
                    INSERT INTO portfolio_snapshots 
                    (total_value, total_pnl, unrealized_pnl, realized_pnl, daily_change, daily_change_percent)
                    VALUES (:total_value, :total_pnl, :unrealized_pnl, :realized_pnl, :daily_change, :daily_change_percent)
                """),
                {
                    "total_value": total_value,
                    "total_pnl": total_pnl,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": realized_pnl,
                    "daily_change": daily_change,
                    "daily_change_percent": daily_change_percent
                }
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error adding portfolio snapshot: {e}")
            self.session.rollback()
    
    def get_latest_portfolio_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get latest portfolio snapshot"""
        try:
            result = self.session.execute(
                text("""
                    SELECT * FROM portfolio_snapshots 
                    ORDER BY snapshot_at DESC 
                    LIMIT 1
                """)
            ).fetchone()
            
            if result:
                return dict(result._mapping)
            return None
        except Exception as e:
            logger.error(f"Error getting latest portfolio snapshot: {e}")
            return None
    
    # ===== SYSTEM METRICS =====
    
    def add_system_metric(self, metric_name: str, metric_value: float):
        """Add system metric to database"""
        try:
            self.session.execute(
                text("INSERT INTO system_metrics (metric_name, metric_value) VALUES (:name, :value)"),
                {"name": metric_name, "value": metric_value}
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error adding system metric: {e}")
            self.session.rollback()
    
    def get_system_metrics(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system metrics for the last N hours"""
        try:
            result = self.session.execute(
                text("""
                    SELECT * FROM system_metrics 
                    WHERE metric_name = :name 
                    AND timestamp > NOW() - INTERVAL ':hours hours'
                    ORDER BY timestamp DESC
                """),
                {"name": metric_name, "hours": hours}
            ).fetchall()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return []
    
    # ===== MARKET DATA CACHE =====
    
    def cache_market_data(self, symbol: str, data_type: str, data: Dict[str, Any], expires_in_minutes: int = 5):
        """Cache market data with expiration"""
        try:
            expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
            
            self.session.execute(
                text("""
                    INSERT INTO market_data_cache (symbol, data_type, data, expires_at)
                    VALUES (:symbol, :data_type, :data, :expires_at)
                    ON CONFLICT (symbol, data_type) 
                    DO UPDATE SET data = :data, expires_at = :expires_at
                """),
                {
                    "symbol": symbol,
                    "data_type": data_type,
                    "data": json.dumps(data),
                    "expires_at": expires_at
                }
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error caching market data: {e}")
            self.session.rollback()
    
    def get_cached_market_data(self, symbol: str, data_type: str) -> Optional[Dict[str, Any]]:
        """Get cached market data if not expired"""
        try:
            result = self.session.execute(
                text("""
                    SELECT data FROM market_data_cache 
                    WHERE symbol = :symbol 
                    AND data_type = :data_type 
                    AND expires_at > NOW()
                """),
                {"symbol": symbol, "data_type": data_type}
            ).fetchone()
            
            if result:
                return json.loads(result[0])
            return None
        except Exception as e:
            logger.error(f"Error getting cached market data: {e}")
            return None
    
    # ===== NEWS AND ECONOMIC DATA =====
    
    def add_news_article(self, title: str, source: str, sentiment: str, impact: str, 
                        summary: str, url: str, published_at: datetime):
        """Add news article to database"""
        try:
            self.session.execute(
                text("""
                    INSERT INTO news_articles (title, source, sentiment, impact, summary, url, published_at)
                    VALUES (:title, :source, :sentiment, :impact, :summary, :url, :published_at)
                """),
                {
                    "title": title,
                    "source": source,
                    "sentiment": sentiment,
                    "impact": impact,
                    "summary": summary,
                    "url": url,
                    "published_at": published_at
                }
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error adding news article: {e}")
            self.session.rollback()
    
    def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get latest news articles"""
        try:
            result = self.session.execute(
                text("""
                    SELECT * FROM news_articles 
                    ORDER BY published_at DESC 
                    LIMIT :limit
                """),
                {"limit": limit}
            ).fetchall()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting latest news: {e}")
            return []
    
    def update_economic_indicator(self, indicator_name: str, fred_series_id: str, current_value: float, 
                                 previous_value: float, next_release_date: str):
        """Update economic indicator data"""
        try:
            change_value = current_value - previous_value
            
            self.session.execute(
                text("""
                    INSERT INTO economic_indicators 
                    (indicator_name, fred_series_id, current_value, previous_value, change_value, next_release_date)
                    VALUES (:name, :fred_id, :current, :previous, :change, :next_release)
                    ON CONFLICT (indicator_name) 
                    DO UPDATE SET 
                        current_value = :current,
                        previous_value = :previous,
                        change_value = :change,
                        next_release_date = :next_release,
                        last_updated = NOW()
                """),
                {
                    "name": indicator_name,
                    "fred_id": fred_series_id,
                    "current": current_value,
                    "previous": previous_value,
                    "change": change_value,
                    "next_release": next_release_date
                }
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error updating economic indicator: {e}")
            self.session.rollback()
    
    def get_economic_indicators(self) -> List[Dict[str, Any]]:
        """Get all economic indicators"""
        try:
            result = self.session.execute(
                text("SELECT * FROM economic_indicators ORDER BY last_updated DESC")
            ).fetchall()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting economic indicators: {e}")
            return []
    
    # ===== BACKTEST RESULTS =====
    
    def add_backtest_result(self, strategy_name: str, period_start: str, period_end: str,
                           returns: float, sharpe_ratio: float, max_drawdown: float,
                           win_rate: float, total_trades: int, results_data: Dict[str, Any]):
        """Add backtest result to database"""
        try:
            self.session.execute(
                text("""
                    INSERT INTO backtest_results 
                    (strategy_name, period_start, period_end, returns, sharpe_ratio, max_drawdown, 
                     win_rate, total_trades, results_data)
                    VALUES (:name, :start, :end, :returns, :sharpe, :drawdown, :win_rate, :trades, :data)
                """),
                {
                    "name": strategy_name,
                    "start": period_start,
                    "end": period_end,
                    "returns": returns,
                    "sharpe": sharpe_ratio,
                    "drawdown": max_drawdown,
                    "win_rate": win_rate,
                    "trades": total_trades,
                    "data": json.dumps(results_data)
                }
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error adding backtest result: {e}")
            self.session.rollback()
    
    def get_backtest_results(self, strategy_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get backtest results"""
        try:
            if strategy_name:
                result = self.session.execute(
                    text("""
                        SELECT * FROM backtest_results 
                        WHERE strategy_name = :name 
                        ORDER BY created_at DESC
                    """),
                    {"name": strategy_name}
                ).fetchall()
            else:
                result = self.session.execute(
                    text("SELECT * FROM backtest_results ORDER BY created_at DESC")
                ).fetchall()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting backtest results: {e}")
            return []
    
    # ===== UTILITY METHODS =====
    
    def cleanup_expired_cache(self):
        """Clean up expired market data cache"""
        try:
            self.session.execute(text("DELETE FROM market_data_cache WHERE expires_at < NOW()"))
            self.session.commit()
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            self.session.rollback()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            
            # Count records in each table
            tables = ['agents', 'strategies', 'trades', 'portfolio_snapshots', 
                     'news_articles', 'economic_indicators', 'backtest_results']
            
            for table in tables:
                result = self.session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                stats[f"{table}_count"] = result[0] if result else 0
            
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}


# Convenience functions for easy access
def get_data_service():
    """Get a data service instance"""
    return DataService()


def with_data_service(func):
    """Decorator to handle data service lifecycle"""
    def wrapper(*args, **kwargs):
        with DataService() as service:
            return func(service, *args, **kwargs)
    return wrapper 