from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum

class DataSource(str, Enum):
    ALPACA = "alpaca"
    SEC_EDGAR = "sec_edgar"
    FRED = "fred"
    BINANCE = "binance"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class MarketDataRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of stock symbols")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    timeframe: str = Field(default="1Day", description="Data timeframe")
    source: DataSource = Field(default=DataSource.ALPACA, description="Data source")

class MarketDataResponse(BaseModel):
    symbol: str
    timestamp: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    source: str

class SECFilingRequest(BaseModel):
    cik_list: Optional[List[str]] = Field(None, description="List of CIK numbers")
    forms: List[str] = Field(default=["10-K", "10-Q"], description="Filing form types")
    limit: int = Field(default=100, description="Maximum number of filings")

class SECFilingResponse(BaseModel):
    cik: str
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    form: str
    filing_date: datetime
    report_date: Optional[datetime] = None
    accession_number: str
    primary_document: Optional[str] = None
    document_description: Optional[str] = None

class MacroDataRequest(BaseModel):
    series_ids: List[str] = Field(..., description="FRED series IDs")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

class MacroDataResponse(BaseModel):
    series_id: str
    date: datetime
    value: float
    series_title: Optional[str] = None
    units: Optional[str] = None

class CryptoDataRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of crypto symbols")
    duration_hours: int = Field(default=24, description="Collection duration in hours")

class CryptoDataResponse(BaseModel):
    symbol: str
    timestamp: datetime
    data_type: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    price_change_percent: Optional[float] = None

class DataIngestionJobRequest(BaseModel):
    job_type: str = Field(..., description="Type of data ingestion job")
    parameters: Dict[str, Any] = Field(..., description="Job parameters")

class DataIngestionJobResponse(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, bool]
    database_connected: bool
    modal_available: bool

class DataSourceStatus(BaseModel):
    source: DataSource
    available: bool
    last_updated: Optional[datetime] = None
    error_message: Optional[str] = None

class DatabaseStats(BaseModel):
    market_data_records: int
    sec_filings_records: int
    macro_data_records: int
    crypto_data_records: int
    total_records: int
    last_updated: datetime

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    data_sources: List[DataSource] = Field(default_factory=list, description="Data sources to search")
    limit: int = Field(default=100, description="Maximum results")
    start_date: Optional[str] = Field(None, description="Start date filter")
    end_date: Optional[str] = Field(None, description="End date filter")

class SearchResult(BaseModel):
    source: DataSource
    title: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    relevance_score: Optional[float] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float

class VectorSearchRequest(BaseModel):
    query_text: str = Field(..., description="Text to search for")
    limit: int = Field(default=10, description="Number of results")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score")

class VectorSearchResult(BaseModel):
    document_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]

class EmbeddingRequest(BaseModel):
    text: str = Field(..., description="Text to embed")
    document_id: str = Field(..., description="Document identifier")
    document_type: str = Field(..., description="Type of document")
    chunk_index: int = Field(default=0, description="Chunk index within document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class EmbeddingResponse(BaseModel):
    document_id: str
    embedding_id: str
    success: bool
    error_message: Optional[str] = None
