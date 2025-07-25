"""
Data models for NYC Violations system
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ViolationData(BaseModel):
    """Enhanced violation data structure"""
    
    # Basic violation info
    plate: str
    state: str
    license_type: Optional[str] = None
    summons_number: str
    violation_code: str
    violation_description: str
    
    # Date and time
    issue_date: str
    violation_time: Optional[str] = None
    judgment_entry_date: Optional[str] = None
    
    # Financial details
    fine_amount: float = 0.0
    penalty_amount: float = 0.0
    interest_amount: float = 0.0
    reduction_amount: float = 0.0
    payment_amount: float = 0.0
    amount_due: float = 0.0
    
    # Location and agency
    precinct: Optional[str] = None
    county: Optional[str] = None
    issuing_agency: Optional[str] = None
    
    # Status and documents
    status: str = "UNKNOWN"
    summons_image: Optional[Dict[str, str]] = None
    local_pdf_path: Optional[str] = None
    
    # Enhanced data from web scraping
    hearing_status: Optional[str] = None
    hearing_date: Optional[str] = None
    hearing_location: Optional[str] = None
    payment_history: Optional[List[Dict]] = None
    last_updated: Optional[datetime] = None


class ScrapingResult(BaseModel):
    """Result of web scraping operation"""
    
    summons_number: str
    success: bool = False
    error_message: Optional[str] = None
    
    # Enhanced data
    current_amount_due: Optional[float] = None
    current_status: Optional[str] = None
    hearing_info: Optional[Dict[str, Any]] = None
    pdf_downloaded: bool = False
    pdf_path: Optional[str] = None
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = None


class ScrapingStatus(BaseModel):
    """Status of ongoing scraping operation"""
    
    job_id: str
    status: str = "pending"  # pending, running, completed, failed
    total_violations: int = 0
    processed_violations: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SearchRequest(BaseModel):
    """Request for violation search"""
    
    plate: str = Field(..., min_length=1, max_length=10)
    state: str = Field(..., min_length=2, max_length=2)
    enhance: bool = False
    download_pdfs: bool = False
    max_scrape_count: Optional[int] = 50


class SearchResponse(BaseModel):
    """Response for violation search"""
    
    license_plate: str
    state: str
    violations: List[ViolationData]
    total_violations: int
    enhanced_violations: int = 0
    downloaded_pdfs: int = 0
    
    success: bool = True
    error: Optional[str] = None
    processing_time: float
    
    # API response metadata
    api_response_time: Optional[float] = None
    scraping_time: Optional[float] = None
    
    debug_info: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    """Health check response"""
    
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    # Component status
    api_client: bool = True
    web_scraper: bool = True
    captcha_service: bool = False
    proxy_service: bool = False
    database: bool = False
    
    # Statistics
    total_searches: int = 0
    total_violations_processed: int = 0
    uptime_seconds: float = 0.0


class JobStatus(BaseModel):
    """Background job status"""
    
    job_id: str
    status: str  # queued, running, completed, failed
    progress: float = 0.0  # 0.0 to 1.0
    
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Metadata
    task_type: str = "violation_search"
    parameters: Optional[Dict[str, Any]] = None


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = None