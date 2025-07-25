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
        with open("enhanced_dashboard.html", "r") as f:
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
    
    logger.info(f"🔍 Hybrid search: {request.plate_number} ({request.state})")
    
    try:
        result = await hybrid_service.search_hybrid(request.dict())
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api_search", response_model=SearchResponse)
async def api_only_search(request: SearchRequest):
    """API-only search (fast, no web scraping)"""
    
    if not hybrid_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    logger.info(f"📊 API search: {request.plate_number} ({request.state})")
    
    try:
        result = await hybrid_service.search_api_only(request.dict())
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ API search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pdf/{plate_number}/{violation_number}")
async def download_pdf(plate_number: str, violation_number: str):
    """Download PDF for a specific violation"""
    
    pdf_path = f"pdfs/{plate_number}_{violation_number}.pdf"
    
    try:
        return FileResponse(
            path=pdf_path,
            filename=f"{plate_number}_{violation_number}.pdf",
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


@app.get("/csb-sw.js")
async def service_worker():
    """Service worker file (empty)"""
    return HTMLResponse(
        content="// Service Worker\nconsole.log('Service worker loaded');",
        media_type="application/javascript"
    )


@app.get("/stats")
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