"""
Hybrid NYC Violations Service
Combines NYC Open Data API with targeted web scraping for complete violation data
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from nyc_api_client import NYCViolationsAPI
from nycserv_scraper import NYCServScraper
from config import settings

logger = logging.getLogger(__name__)


class HybridViolationsService:
    """Service that combines API data with web scraping for comprehensive violation information"""
    
    def __init__(self, 
                 captcha_api_key: Optional[str] = None,
                 proxies: Optional[List[str]] = None):
        
        self.api_client = NYCViolationsAPI()
        self.scraper = NYCServScraper(
            captcha_api_key=captcha_api_key or settings.TWOCAPTCHA_API_KEY,
            proxies=proxies or settings.proxies
        )
        
        # Performance settings
        self.max_scrape_violations = settings.MAX_SCRAPE_VIOLATIONS
        
    async def get_complete_violation_data(self, 
                                        license_plate: str, 
                                        state: str = "NY",
                                        enhance_with_scraping: bool = True) -> Dict[str, Any]:
        """Get complete violation data using hybrid API + scraping approach"""
        
        start_time = datetime.now()
        
        logger.info(f"🚀 Getting complete violation data for {license_plate} ({state})")
        
        result = {
            'license_plate': license_plate.upper(),
            'state': state.upper(),
            'violations': [],
            'total_violations': 0,
            'enhanced_violations': 0,
            'downloaded_pdfs': 0,
            'success': False,
            'error': None,
            'processing_time': 0.0,
            'api_response_time': 0.0,
            'scraping_time': 0.0
        }
        
        try:
            # Step 1: Get basic violation data from API
            logger.info("📊 Fetching basic violation data from NYC API...")
            api_start = datetime.now()
            
            api_result = await self.api_client.search_violations(license_plate, state)
            
            api_end = datetime.now()
            result['api_response_time'] = (api_end - api_start).total_seconds()
            
            if not api_result.get('success'):
                result['error'] = f"API search failed: {api_result.get('error')}"
                return result
            
            violations = api_result.get('violations', [])
            result['violations'] = violations
            result['total_violations'] = len(violations)
            
            logger.info(f"✅ API found {len(violations)} violations")
            
            # Step 2: Enhance with web scraping if requested
            if enhance_with_scraping and violations and settings.has_captcha_key:
                logger.info("🔍 Enhancing violations with web scraping...")
                scraping_start = datetime.now()
                
                # Convert to dict format for scraper
                violation_dicts = [v.dict() for v in violations[:self.max_scrape_violations]]
                
                enhanced_violations = await self.scraper.enhance_violation_data(
                    violation_dicts, license_plate, state
                )
                
                scraping_end = datetime.now()
                result['scraping_time'] = (scraping_end - scraping_start).total_seconds()
                result['enhanced_violations'] = len(enhanced_violations)
                
                # Count downloaded PDFs
                result['downloaded_pdfs'] = sum(1 for v in enhanced_violations if v.get('local_pdf_path'))
                
                logger.info(f"✅ Enhanced {len(enhanced_violations)} violations")
                
                # Update violations with enhanced data
                result['violations'] = enhanced_violations
            
            elif enhance_with_scraping and not settings.has_captcha_key:
                logger.warning("⚠️ Web scraping requested but no 2Captcha API key configured")
            
            # Calculate total processing time
            end_time = datetime.now()
            result['processing_time'] = (end_time - start_time).total_seconds()
            result['success'] = True
            
            logger.info(f"🎉 Complete! Processed {result['total_violations']} violations in {result['processing_time']:.2f}s")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            result['processing_time'] = (end_time - start_time).total_seconds()
            result['error'] = f"Hybrid search failed: {str(e)}"
            logger.error(result['error'])
            
            return result