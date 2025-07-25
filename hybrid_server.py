"""
Hybrid NYC Violations Server
FastAPI server providing both API and web scraping capabilities
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from hybrid_service import HybridViolationsService
from models import SearchRequest, SearchResponse, HealthCheck
from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Global service instance
hybrid_service: Optional[HybridViolationsService] = None
server_start_time = datetime.now()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global hybrid_service
    
    # Startup
    logger.info("🚀 Starting NYC Hybrid Violations Server")
    hybrid_service = HybridViolationsService()
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down server")


# Create FastAPI app
app = FastAPI(
    title="NYC Violations Hybrid Scraper",
    description="Combines NYC Open Data API with web scraping for complete violation information",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard"""
    try:
        with open("/project/workspace/nyc-scraper-improved/enhanced_dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html><body>
        <h1>NYC Violations Hybrid Scraper</h1>
        <p>Dashboard loading...</p>
        <h2>API Endpoints:</h2>
        <ul>
            <li>POST /search - Hybrid search with web scraping</li>
            <li>GET /violations/{plate}/{state} - API-only search</li>
            <li>GET /health - System health check</li>
        </ul>
        </body></html>
        """)


@app.post("/search", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest):
    """Perform hybrid search (API + web scraping)"""
    
    if not hybrid_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    logger.info(f"🔍 Hybrid search: {request.plate} ({request.state})")
    
    try:
        result = await hybrid_service.get_complete_violation_data(
            request.plate,
            request.state,
            enhance_with_scraping=request.enhance
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/violations/{plate}/{state}")
async def api_only_search(plate: str, state: str):
    """API-only search (fast, no web scraping)"""
    
    if not hybrid_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    logger.info(f"📊 API search: {plate} ({state})")
    
    try:
        result = await hybrid_service.api_client.search_violations(plate, state)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"❌ API search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-pdf/{summons_number}")
async def download_pdf(summons_number: str):
    """Download PDF for a specific summons"""
    
    pdf_path = f"{settings.PDF_DIR}/{summons_number}.pdf"
    
    try:
        return FileResponse(
            path=pdf_path,
            filename=f"{summons_number}.pdf",
            media_type="application/pdf"
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="PDF not found")


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """System health check"""
    
    uptime = (datetime.now() - server_start_time).total_seconds()
    
    health = HealthCheck(
        status="healthy",
        uptime_seconds=uptime,
        captcha_service=settings.has_captcha_key,
        proxy_service=settings.has_proxies,
        database=settings.has_database
    )
    
    return health


@app.get("/statistics")
async def get_statistics():
    """Get system statistics"""
    
    if not hybrid_service:
        return {"error": "Service not initialized"}
    
    try:
        api_stats = await hybrid_service.api_client.get_statistics()
        
        stats = {
            "server_uptime": (datetime.now() - server_start_time).total_seconds(),
            "api_client": api_stats,
            "configuration": {
                "has_captcha_key": settings.has_captcha_key,
                "has_proxies": settings.has_proxies,
                "max_scrape_violations": settings.MAX_SCRAPE_VIOLATIONS,
                "downloads_directory": settings.DOWNLOADS_DIR
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get statistics: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )