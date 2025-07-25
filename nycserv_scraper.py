"""
NYCServ Web Scraper - Enhanced Data Extraction
Scrapes additional violation data not available via API
"""

import asyncio
import os
import aiofiles
from datetime import datetime
from playwright.async_api import async_playwright
from typing import Dict, List, Optional, Any
import logging
import time

from enhanced_captcha_client import TwoCaptchaClient
from proxy_manager import ProxyPool
from config import settings

logger = logging.getLogger(__name__)


class NYCServScraper:
    """Enhanced scraper for NYCServ website to get missing violation data"""
    
    def __init__(self, 
                 captcha_api_key: Optional[str] = None,
                 proxies: Optional[List[str]] = None,
                 downloads_dir: Optional[str] = None):
        
        self.base_url = "https://nycserv.nyc.gov/NYCServWeb/PVO_Search.jsp"
        self.captcha_client = TwoCaptchaClient(captcha_api_key) if captcha_api_key else None
        self.proxy_pool = ProxyPool(proxies) if proxies else None
        self.downloads_dir = downloads_dir or settings.DOWNLOADS_DIR
        
        # Create downloads directory
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(os.path.join(self.downloads_dir, "pdfs"), exist_ok=True)
    
    async def enhance_violation_data(self, violations: List[Dict], license_plate: str, state: str) -> List[Dict]:
        """Enhance violation data with web scraping"""
        
        if not violations:
            return violations
        
        logger.info(f"🔍 Enhancing {len(violations)} violations for {license_plate} ({state})")
        
        try:
            async with async_playwright() as p:
                # Launch browser with proxy if available
                browser_args = {'headless': True}
                
                if self.proxy_pool and self.proxy_pool.has_healthy_proxies():
                    proxy = await self.proxy_pool.get_proxy()
                    if proxy:
                        browser_args['proxy'] = self.proxy_pool.get_proxy_for_playwright(proxy)
                
                browser = await p.chromium.launch(**browser_args)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Navigate to NYCServ
                await page.goto(self.base_url)
                
                # Search for violations
                await self._search_plate(page, license_plate, state)
                
                # Enhance each violation
                enhanced_violations = []
                for violation in violations[:settings.MAX_SCRAPE_VIOLATIONS]:
                    enhanced = await self._enhance_single_violation(page, violation)
                    enhanced_violations.append(enhanced)
                
                await browser.close()
                
                return enhanced_violations
                
        except Exception as e:
            logger.error(f"❌ Web scraping failed: {e}")
            return violations
    
    async def _search_plate(self, page, license_plate: str, state: str):
        """Search for a license plate on NYCServ"""
        
        try:
            # Fill search form
            await page.fill('input[name="plateNumber"]', license_plate)
            await page.select_option('select[name="registrationState"]', state)
            
            # Handle CAPTCHA if present
            if await self._solve_captcha_if_present(page):
                # Submit search
                await page.click('input[type="submit"]')
                await page.wait_for_load_state('networkidle')
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
    
    async def _solve_captcha_if_present(self, page) -> bool:
        """Solve CAPTCHA if present on the page"""
        
        try:
            # Check for reCAPTCHA
            recaptcha = await page.query_selector('.g-recaptcha')
            if recaptcha and self.captcha_client:
                site_key = await recaptcha.get_attribute('data-sitekey')
                if site_key:
                    solution = await self.captcha_client.solve_recaptcha_v2(
                        site_key, page.url
                    )
                    if solution:
                        await page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML="{solution}";')
                        return True
            
            # Check for image CAPTCHA
            captcha_img = await page.query_selector('img[alt*="captcha"]')
            if captcha_img and self.captcha_client:
                img_data = await captcha_img.screenshot()
                solution = await self.captcha_client.solve_image_captcha(img_data)
                if solution:
                    await page.fill('input[name="captcha"]', solution)
                    return True
            
            return True  # No CAPTCHA found
            
        except Exception as e:
            logger.error(f"❌ CAPTCHA solving failed: {e}")
            return False
    
    async def _enhance_single_violation(self, page, violation: Dict) -> Dict:
        """Enhance a single violation with detailed data"""
        
        try:
            # Click details button for this violation
            summons_number = violation.get('summons_number')
            details_link = await page.query_selector(f'a[href*="{summons_number}"]')
            
            if details_link:
                await details_link.click()
                await page.wait_for_load_state('networkidle')
                
                # Extract enhanced data
                enhanced_data = await self._extract_detailed_data(page)
                violation.update(enhanced_data)
                
                # Download PDF if available
                pdf_path = await self._download_pdf(page, summons_number)
                if pdf_path:
                    violation['local_pdf_path'] = pdf_path
                
                # Go back to list
                await page.go_back()
                await page.wait_for_load_state('networkidle')
            
            return violation
            
        except Exception as e:
            logger.error(f"❌ Failed to enhance violation {violation.get('summons_number')}: {e}")
            return violation
    
    async def _extract_detailed_data(self, page) -> Dict:
        """Extract detailed violation data from details page"""
        
        try:
            enhanced_data = {}
            
            # Extract current amount due
            amount_due_elem = await page.query_selector('td:has-text("Amount Due")')
            if amount_due_elem:
                amount_text = await amount_due_elem.text_content()
                # Parse amount from text
                import re
                amount_match = re.search(r'\$?(\d+\.?\d*)', amount_text)
                if amount_match:
                    enhanced_data['current_amount_due'] = float(amount_match.group(1))
            
            # Extract hearing status
            status_elem = await page.query_selector('td:has-text("Status")')
            if status_elem:
                enhanced_data['hearing_status'] = await status_elem.text_content()
            
            # Extract hearing date if present
            hearing_elem = await page.query_selector('td:has-text("Hearing")')
            if hearing_elem:
                enhanced_data['hearing_date'] = await hearing_elem.text_content()
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ Failed to extract detailed data: {e}")
            return {}
    
    async def _download_pdf(self, page, summons_number: str) -> Optional[str]:
        """Download PDF for a violation"""
        
        try:
            # Look for PDF download link
            pdf_link = await page.query_selector('a[href*="ShowImage"]')
            if not pdf_link:
                return None
            
            # Get PDF URL
            pdf_url = await pdf_link.get_attribute('href')
            if not pdf_url:
                return None
            
            # Download PDF
            response = await page.goto(pdf_url)
            if response and response.status == 200:
                pdf_data = await response.body()
                
                # Save PDF
                pdf_filename = f"{summons_number}.pdf"
                pdf_path = os.path.join(self.downloads_dir, "pdfs", pdf_filename)
                
                async with aiofiles.open(pdf_path, 'wb') as f:
                    await f.write(pdf_data)
                
                logger.info(f"✅ Downloaded PDF: {pdf_filename}")
                return pdf_path
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to download PDF for {summons_number}: {e}")
            return None