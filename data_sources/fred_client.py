import os
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FREDClient:
    def __init__(self):
        self.api_key = os.getenv("FRED_API_KEY")
        self.base_url = "https://api.stlouisfed.org/fred"
        
        if not self.api_key:
            raise ValueError("FRED API key not found in environment variables")
        
        self.rate_limit_delay = 0.5
    
    def _make_request(self, endpoint: str, params=None):
        """Make rate-limited request to FRED API"""
        try:
            if params is None:
                params = {}
            
            params.update({
                'api_key': self.api_key,
                'file_type': 'json'
            })
            
            time.sleep(self.rate_limit_delay)
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error making FRED API request to {endpoint}: {e}")
            raise
    
    def get_series_data(self, series_ids: list, start_date=None, end_date=None):
        """Get data for multiple economic series"""
        try:
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            all_data = []
            
            for series_id in series_ids:
                try:
                    params = {
                        'series_id': series_id,
                        'observation_start': start_date,
                        'observation_end': end_date,
                        'sort_order': 'asc'
                    }
                    
                    data = self._make_request('series/observations', params)
                    
                    if 'observations' in data:
                        for obs in data['observations']:
                            if obs['value'] != '.':
                                all_data.append({
                                    'series_id': series_id,
                                    'date': obs['date'],
                                    'value': float(obs['value']),
                                    'realtime_start': obs['realtime_start'],
                                    'realtime_end': obs['realtime_end']
                                })
                
                except Exception as e:
                    logger.warning(f"Error fetching data for series {series_id}: {e}")
                    continue
            
            df = pd.DataFrame(all_data)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values(['series_id', 'date'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching series data: {e}")
            raise
    
    def get_series_info(self, series_ids: list):
        """Get metadata for economic series"""
        try:
            all_info = []
            
            for series_id in series_ids:
                try:
                    params = {'series_id': series_id}
                    data = self._make_request('series', params)
                    
                    if 'seriess' in data and data['seriess']:
                        series_info = data['seriess'][0]
                        all_info.append({
                            'series_id': series_info['id'],
                            'title': series_info['title'],
                            'units': series_info['units'],
                            'frequency': series_info['frequency'],
                            'seasonal_adjustment': series_info['seasonal_adjustment'],
                            'last_updated': series_info['last_updated'],
                            'observation_start': series_info['observation_start'],
                            'observation_end': series_info['observation_end'],
                            'notes': series_info.get('notes', '')
                        })
                
                except Exception as e:
                    logger.warning(f"Error fetching info for series {series_id}: {e}")
                    continue
            
            return pd.DataFrame(all_info)
            
        except Exception as e:
            logger.error(f"Error fetching series info: {e}")
            raise
    
    def search_series(self, search_text: str, limit: int = 100):
        """Search for economic series by text"""
        try:
            params = {
                'search_text': search_text,
                'limit': limit,
                'sort_order': 'search_rank'
            }
            
            data = self._make_request('series/search', params)
            
            series_list = []
            if 'seriess' in data:
                for series in data['seriess']:
                    series_list.append({
                        'series_id': series['id'],
                        'title': series['title'],
                        'units': series['units'],
                        'frequency': series['frequency'],
                        'seasonal_adjustment': series['seasonal_adjustment'],
                        'last_updated': series['last_updated'],
                        'popularity': series.get('popularity', 0),
                        'notes': series.get('notes', '')
                    })
            
            return pd.DataFrame(series_list)
            
        except Exception as e:
            logger.error(f"Error searching series: {e}")
            raise
    
    def get_categories(self, category_id: int = 0):
        """Get FRED categories"""
        try:
            params = {'category_id': category_id}
            data = self._make_request('category/children', params)
            
            categories = []
            if 'categories' in data:
                for cat in data['categories']:
                    categories.append({
                        'category_id': cat['id'],
                        'name': cat['name'],
                        'parent_id': cat['parent_id']
                    })
            
            return pd.DataFrame(categories)
            
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            raise
    
    def get_popular_series(self, limit: int = 50):
        """Get popular economic indicators"""
        popular_series = [
            'GDP', 'GDPC1', 'UNRATE', 'CPIAUCSL', 'CPILFESL',
            'FEDFUNDS', 'DGS10', 'DGS3MO', 'DEXUSEU', 'DEXJPUS',
            'PAYEMS', 'HOUST', 'INDPRO', 'RETAILMNSA', 'UMCSENT'
        ]
        
        return self.get_series_data(popular_series[:limit])
