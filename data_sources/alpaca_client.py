import os
import pandas as pd
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
import logging

logger = logging.getLogger(__name__)

class AlpacaClient:
    def __init__(self):
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
        self.data_url = os.getenv("APCA_DATA_URL", "https://data.alpaca.markets")
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not found in environment variables")
        
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
    
    def get_historical_data(self, symbols: list, start_date, end_date, timeframe: str = "1Day"):
        """Get historical market data for given symbols"""
        try:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
            
            timeframe_map = {
                "1Min": TimeFrame.Minute,
                "5Min": TimeFrame(5, "Min"),
                "15Min": TimeFrame(15, "Min"),
                "1Hour": TimeFrame.Hour,
                "1Day": TimeFrame.Day
            }
            
            tf = timeframe_map.get(timeframe, TimeFrame.Day)
            
            request_params = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=tf,
                start=start_date,
                end=end_date
            )
            
            bars = self.data_client.get_stock_bars(request_params)
            
            data_list = []
            for symbol, bar_data in bars.data.items():
                for bar in bar_data:
                    data_list.append({
                        'symbol': symbol,
                        'timestamp': bar.timestamp,
                        'open': float(bar.open),
                        'high': float(bar.high),
                        'low': float(bar.low),
                        'close': float(bar.close),
                        'volume': int(bar.volume),
                        'trade_count': getattr(bar, 'trade_count', None),
                        'vwap': getattr(bar, 'vwap', None)
                    })
            
            df = pd.DataFrame(data_list)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values(['symbol', 'timestamp'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise
    
    def get_latest_quotes(self, symbols: list):
        """Get latest quotes for given symbols"""
        try:
            from alpaca.data.requests import StockLatestQuoteRequest
            
            request_params = StockLatestQuoteRequest(symbol_or_symbols=symbols)
            quotes = self.data_client.get_stock_latest_quote(request_params)
            
            data_list = []
            for symbol, quote in quotes.data.items():
                data_list.append({
                    'symbol': symbol,
                    'timestamp': quote.timestamp,
                    'bid_price': float(quote.bid_price),
                    'ask_price': float(quote.ask_price),
                    'bid_size': int(quote.bid_size),
                    'ask_size': int(quote.ask_size)
                })
            
            return pd.DataFrame(data_list)
            
        except Exception as e:
            logger.error(f"Error fetching latest quotes: {e}")
            raise
    
    def get_assets(self, asset_class: str = "us_equity", status: str = "active"):
        """Get tradeable assets"""
        try:
            request_params = GetAssetsRequest(
                asset_class=asset_class,
                status=status
            )
            
            assets = self.trading_client.get_all_assets(request_params)
            
            data_list = []
            for asset in assets:
                data_list.append({
                    'symbol': asset.symbol,
                    'name': asset.name,
                    'asset_class': asset.asset_class,
                    'exchange': asset.exchange,
                    'status': asset.status,
                    'tradable': asset.tradable,
                    'marginable': asset.marginable,
                    'shortable': asset.shortable,
                    'easy_to_borrow': asset.easy_to_borrow
                })
            
            return pd.DataFrame(data_list)
            
        except Exception as e:
            logger.error(f"Error fetching assets: {e}")
            raise
    
    def get_market_data_for_symbol(self, symbol: str, period: str = "1mo"):
        """Get market data for a single symbol (yfinance replacement)"""
        try:
            end_date = datetime.now()
            
            period_map = {
                "1d": timedelta(days=1),
                "5d": timedelta(days=5),
                "1mo": timedelta(days=30),
                "3mo": timedelta(days=90),
                "6mo": timedelta(days=180),
                "1y": timedelta(days=365),
                "2y": timedelta(days=730),
                "5y": timedelta(days=1825),
                "10y": timedelta(days=3650)
            }
            
            start_date = end_date - period_map.get(period, timedelta(days=30))
            
            return self.get_historical_data([symbol], start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            raise
