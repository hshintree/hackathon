import os
import requests
import pandas as pd
import time
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SECEdgarClient:
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        # Use a configurable User-Agent per SEC guidance
        ua = os.getenv("SEC_USER_AGENT", "Gigadataset Ingestor (contact@example.com)")
        self.headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
        # Be conservative to avoid throttling
        self.rate_limit_delay = 0.5
    
    def _make_request(self, url: str, params=None):
        """Make rate-limited request to SEC API"""
        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error making SEC API request to {url}: {e}")
            raise
    
    def get_company_tickers(self):
        """Get company ticker to CIK mapping (live list from SEC)."""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            time.sleep(self.rate_limit_delay)
            r = requests.get(url, headers=self.headers, timeout=15)
            r.raise_for_status()
            data = r.json()
            # Data is a dict keyed by index -> {cik_str, ticker, title}
            rows = []
            for _, obj in data.items():
                rows.append({
                    'cik': str(obj.get('cik_str')).zfill(10),
                    'ticker': obj.get('ticker'),
                    'title': obj.get('title')
                })
            df = pd.DataFrame(rows)
            # Keep common stock-like tickers (simple filter)
            df = df[df['ticker'].str.match(r'^[A-Z]{1,5}$', na=False)]
            return df
        except Exception as e:
            logger.error(f"Error fetching company tickers: {e}")
            # Fallback small sample to avoid hard failure
            sample_companies = [
                {'cik': '0000320193', 'ticker': 'AAPL', 'title': 'Apple Inc.'},
                {'cik': '0001652044', 'ticker': 'GOOGL', 'title': 'Alphabet Inc.'},
                {'cik': '0000789019', 'ticker': 'MSFT', 'title': 'Microsoft Corporation'},
                {'cik': '0001018724', 'ticker': 'AMZN', 'title': 'Amazon.com, Inc.'},
                {'cik': '0001326801', 'ticker': 'META', 'title': 'Meta Platforms, Inc.'}
            ]
            return pd.DataFrame(sample_companies)
    
    def get_company_facts(self, cik: str):
        """Get company facts for a specific CIK"""
        try:
            cik_padded = str(cik).zfill(10)
            url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik_padded}.json"
            
            data = self._make_request(url)
            
            facts_list = []
            if 'facts' in data:
                for taxonomy, concepts in data['facts'].items():
                    for concept, concept_data in concepts.items():
                        if 'units' in concept_data:
                            for unit, unit_data in concept_data['units'].items():
                                for fact in unit_data:
                                    facts_list.append({
                                        'cik': cik_padded,
                                        'taxonomy': taxonomy,
                                        'concept': concept,
                                        'unit': unit,
                                        'value': fact.get('val'),
                                        'end_date': fact.get('end'),
                                        'start_date': fact.get('start'),
                                        'filed_date': fact.get('filed'),
                                        'form': fact.get('form'),
                                        'frame': fact.get('frame')
                                    })
            
            return pd.DataFrame(facts_list)
            
        except Exception as e:
            logger.error(f"Error fetching company facts for CIK {cik}: {e}")
            raise
    
    def get_company_filings(self, cik_list=None, forms=None, limit: int = 100):
        """Get recent filings for companies"""
        try:
            if cik_list is None:
                tickers_df = self.get_company_tickers()
                cik_list = tickers_df['cik'].head(100).tolist()
            
            if forms is None:
                forms = ['10-K', '10-Q', '8-K']
            
            all_filings = []
            
            for cik in cik_list:
                try:
                    cik_padded = str(cik).zfill(10)
                    url = f"{self.base_url}/submissions/CIK{cik_padded}.json"
                    
                    data = self._make_request(url)
                    
                    if 'filings' in data and 'recent' in data['filings']:
                        recent = data['filings']['recent']
                        
                        for i in range(min(len(recent.get('form', [])), limit)):
                            form = recent['form'][i]
                            if form in forms:
                                filing = {
                                    'cik': cik_padded,
                                    'company_name': data.get('name', ''),
                                    'ticker': data.get('tickers', [''])[0] if data.get('tickers') else '',
                                    'form': form,
                                    'filing_date': recent['filingDate'][i],
                                    'report_date': recent['reportDate'][i],
                                    'accession_number': recent['accessionNumber'][i],
                                    'primary_document': recent['primaryDocument'][i],
                                    'primary_doc_description': recent['primaryDocDescription'][i]
                                }
                                all_filings.append(filing)
                
                except Exception as e:
                    logger.warning(f"Error fetching filings for CIK {cik}: {e}")
                    continue
            
            df = pd.DataFrame(all_filings)
            if not df.empty:
                df['filing_date'] = pd.to_datetime(df['filing_date'])
                df['report_date'] = pd.to_datetime(df['report_date'])
                df = df.sort_values('filing_date', ascending=False)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching company filings: {e}")
            raise
    
    def get_filing_content(self, cik: str, accession_number: str, primary_document: str):
        """Get the content of a specific filing"""
        try:
            accession_clean = accession_number.replace('-', '')
            # Try data.sec.gov first
            url = f"https://data.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/{primary_document}"
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                return r.text
            # Fallback to www.sec.gov
            url2 = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/{primary_document}"
            r2 = requests.get(url2, headers=self.headers)
            r2.raise_for_status()
            return r2.text
        except Exception as e:
            logger.error(f"Error fetching filing content: {e}")
            raise
    
    def search_filings(self, query: str, start_date=None, end_date=None):
        """Search filings by query"""
        try:
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            tickers_df = self.get_company_tickers()
            matching_companies = tickers_df[
                tickers_df['ticker'].str.contains(query, case=False, na=False) |
                tickers_df['title'].str.contains(query, case=False, na=False)
            ]
            
            if matching_companies.empty:
                return pd.DataFrame()
            
            cik_list = matching_companies['cik'].tolist()
            return self.get_company_filings(cik_list)
            
        except Exception as e:
            logger.error(f"Error searching filings: {e}")
            raise
