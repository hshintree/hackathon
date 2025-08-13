import os
import asyncio
import websockets
import json
import pandas as pd
from datetime import datetime, timedelta
import logging
import aiohttp

logger = logging.getLogger(__name__)

class BinanceClient:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.secret_key = os.getenv("BINANCE_SECRET_KEY")
        self.base_url = "https://api.binance.com"
        self.ws_url = "wss://stream.binance.com:9443/ws"
        
        self.rate_limit_delay = 0.1
    
    async def _make_request(self, endpoint: str, params=None):
        """Make async request to Binance API"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Error making Binance API request to {endpoint}: {e}")
            raise
    
    async def get_historical_klines(self, symbol: str, interval: str = "1d", limit: int = 1000):
        """Get historical kline/candlestick data"""
        try:
            params = {
                'symbol': symbol.upper(),
                'interval': interval,
                'limit': limit
            }
            
            data = await self._make_request('/api/v3/klines', params)
            
            klines = []
            for kline in data:
                klines.append({
                    'symbol': symbol.upper(),
                    'timestamp': pd.to_datetime(kline[0], unit='ms'),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': pd.to_datetime(kline[6], unit='ms'),
                    'quote_volume': float(kline[7]),
                    'trade_count': int(kline[8]),
                    'taker_buy_base_volume': float(kline[9]),
                    'taker_buy_quote_volume': float(kline[10])
                })
            
            return pd.DataFrame(klines)
            
        except Exception as e:
            logger.error(f"Error fetching historical klines for {symbol}: {e}")
            raise
    
    async def get_24hr_ticker(self, symbol=None):
        """Get 24hr ticker price change statistics"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol.upper()
            
            data = await self._make_request('/api/v3/ticker/24hr', params)
            
            if isinstance(data, list):
                tickers = []
                for ticker in data:
                    tickers.append({
                        'symbol': ticker['symbol'],
                        'price_change': float(ticker['priceChange']),
                        'price_change_percent': float(ticker['priceChangePercent']),
                        'weighted_avg_price': float(ticker['weightedAvgPrice']),
                        'prev_close_price': float(ticker['prevClosePrice']),
                        'last_price': float(ticker['lastPrice']),
                        'bid_price': float(ticker['bidPrice']),
                        'ask_price': float(ticker['askPrice']),
                        'open_price': float(ticker['openPrice']),
                        'high_price': float(ticker['highPrice']),
                        'low_price': float(ticker['lowPrice']),
                        'volume': float(ticker['volume']),
                        'quote_volume': float(ticker['quoteVolume']),
                        'open_time': pd.to_datetime(ticker['openTime'], unit='ms'),
                        'close_time': pd.to_datetime(ticker['closeTime'], unit='ms'),
                        'trade_count': int(ticker['count'])
                    })
                return pd.DataFrame(tickers)
            else:
                return pd.DataFrame([{
                    'symbol': data['symbol'],
                    'price_change': float(data['priceChange']),
                    'price_change_percent': float(data['priceChangePercent']),
                    'last_price': float(data['lastPrice']),
                    'volume': float(data['volume'])
                }])
                
        except Exception as e:
            logger.error(f"Error fetching 24hr ticker: {e}")
            raise
    
    async def collect_websocket_data(self, symbols: list, duration_hours: int = 1):
        """Collect real-time data via websockets"""
        try:
            streams = []
            for symbol in symbols:
                symbol_lower = symbol.lower()
                streams.extend([
                    f"{symbol_lower}@ticker",
                    f"{symbol_lower}@kline_1m",
                    f"{symbol_lower}@depth5"
                ])
            
            stream_names = "/".join(streams)
            ws_url = f"{self.ws_url}/{stream_names}"
            
            collected_data = []
            end_time = datetime.now() + timedelta(hours=duration_hours)
            
            async with websockets.connect(ws_url) as websocket:
                while datetime.now() < end_time:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        data = json.loads(message)
                        
                        if 'stream' in data and 'data' in data:
                            stream = data['stream']
                            stream_data = data['data']
                            
                            if '@ticker' in stream:
                                collected_data.append({
                                    'type': 'ticker',
                                    'symbol': stream_data['s'],
                                    'timestamp': pd.to_datetime(stream_data['E'], unit='ms'),
                                    'price': float(stream_data['c']),
                                    'volume': float(stream_data['v']),
                                    'price_change': float(stream_data['P']),
                                    'high': float(stream_data['h']),
                                    'low': float(stream_data['l'])
                                })
                            elif '@kline' in stream:
                                kline = stream_data['k']
                                collected_data.append({
                                    'type': 'kline',
                                    'symbol': kline['s'],
                                    'timestamp': pd.to_datetime(kline['t'], unit='ms'),
                                    'open': float(kline['o']),
                                    'high': float(kline['h']),
                                    'low': float(kline['l']),
                                    'close': float(kline['c']),
                                    'volume': float(kline['v']),
                                    'is_closed': kline['x']
                                })
                            elif '@depth' in stream:
                                collected_data.append({
                                    'type': 'depth',
                                    'symbol': stream.split('@')[0].upper(),
                                    'timestamp': pd.to_datetime(datetime.now()),
                                    'bids': stream_data['bids'][:5],
                                    'asks': stream_data['asks'][:5]
                                })
                    
                    except asyncio.TimeoutError:
                        await websocket.ping()
                        continue
                    except Exception as e:
                        logger.warning(f"Error processing websocket message: {e}")
                        continue
            
            return pd.DataFrame(collected_data)
            
        except Exception as e:
            logger.error(f"Error collecting websocket data: {e}")
            raise
    
    async def get_exchange_info(self):
        """Get exchange trading rules and symbol information"""
        try:
            data = await self._make_request('/api/v3/exchangeInfo')
            
            symbols = []
            for symbol_info in data.get('symbols', []):
                if symbol_info['status'] == 'TRADING':
                    symbols.append({
                        'symbol': symbol_info['symbol'],
                        'base_asset': symbol_info['baseAsset'],
                        'quote_asset': symbol_info['quoteAsset'],
                        'status': symbol_info['status'],
                        'is_spot_trading_allowed': symbol_info.get('isSpotTradingAllowed', False),
                        'is_margin_trading_allowed': symbol_info.get('isMarginTradingAllowed', False)
                    })
            
            return pd.DataFrame(symbols)
            
        except Exception as e:
            logger.error(f"Error fetching exchange info: {e}")
            raise
