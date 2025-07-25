"""
Enhanced CAPTCHA Solver using 2Captcha service
Specifically designed for NYCServ website CAPTCHA challenges
"""

import asyncio
import aiohttp
import base64
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import time

from config import settings

logger = logging.getLogger(__name__)


class TwoCaptchaClient:
    """2Captcha service client for solving CAPTCHAs"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TWOCAPTCHA_API_KEY
        self.base_url = "https://2captcha.com"
        self.timeout = settings.CAPTCHA_TIMEOUT
        self.poll_interval = 5  # Check every 5 seconds
        
        # Statistics
        self.total_solved = 0
        self.total_failed = 0
        self.total_cost = 0.0
        
    async def solve_recaptcha_v2(self, site_key: str, page_url: str, proxy: Optional[Dict] = None) -> Optional[str]:
        """
        Solve reCAPTCHA v2 challenge
        
        Args:
            site_key: The site key from the reCAPTCHA
            page_url: The URL where the reCAPTCHA is located
            proxy: Optional proxy configuration
            
        Returns:
            The solved reCAPTCHA token or None if failed
        """
        logger.info(f"🔐 Solving reCAPTCHA v2 for {page_url}")
        
        if not self.api_key:
            logger.error("❌ No 2Captcha API key provided")
            return None
        
        try:
            # Submit CAPTCHA for solving
            task_id = await self._submit_recaptcha_v2(site_key, page_url, proxy)
            if not task_id:
                return None
            
            # Poll for result
            result = await self._get_result(task_id)
            
            if result:
                logger.info("✅ reCAPTCHA v2 solved successfully")
                self.total_solved += 1
                self.total_cost += 0.002  # Approximate cost
                return result
            else:
                logger.error("❌ Failed to solve reCAPTCHA v2")
                self.total_failed += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ reCAPTCHA solving error: {e}")
            self.total_failed += 1
            return None
    
    async def solve_image_captcha(self, image_data: bytes) -> Optional[str]:
        """
        Solve image-based CAPTCHA
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            The solved text or None if failed
        """
        logger.info("🖼️ Solving image CAPTCHA")
        
        if not self.api_key:
            logger.error("❌ No 2Captcha API key provided")
            return None
        
        try:
            # Submit image CAPTCHA for solving
            task_id = await self._submit_image_captcha(image_data)
            if not task_id:
                return None
            
            # Poll for result
            result = await self._get_result(task_id)
            
            if result:
                logger.info("✅ Image CAPTCHA solved successfully")
                self.total_solved += 1
                self.total_cost += 0.001  # Approximate cost
                return result
            else:
                logger.error("❌ Failed to solve image CAPTCHA")
                self.total_failed += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ Image CAPTCHA solving error: {e}")
            self.total_failed += 1
            return None
    
    async def _submit_recaptcha_v2(self, site_key: str, page_url: str, proxy: Optional[Dict] = None) -> Optional[str]:
        """Submit reCAPTCHA v2 to 2Captcha for solving"""
        
        data = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1
        }
        
        # Add proxy if provided
        if proxy:
            data.update({
                'proxy': f"{proxy.get('username')}:{proxy.get('password')}@{proxy.get('host')}:{proxy.get('port')}",
                'proxytype': proxy.get('type', 'HTTP')
            })
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/in.php", data=data) as response:
                    result = await response.json()
                    
                    if result.get('status') == 1:
                        task_id = result.get('request')
                        logger.debug(f"reCAPTCHA submitted with task ID: {task_id}")
                        return task_id
                    else:
                        logger.error(f"Failed to submit reCAPTCHA: {result.get('error_text')}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error submitting reCAPTCHA: {e}")
            return None
    
    async def _submit_image_captcha(self, image_data: bytes) -> Optional[str]:
        """Submit image CAPTCHA to 2Captcha for solving"""
        
        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        data = {
            'key': self.api_key,
            'method': 'base64',
            'body': image_base64,
            'json': 1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/in.php", data=data) as response:
                    result = await response.json()
                    
                    if result.get('status') == 1:
                        task_id = result.get('request')
                        logger.debug(f"Image CAPTCHA submitted with task ID: {task_id}")
                        return task_id
                    else:
                        logger.error(f"Failed to submit image CAPTCHA: {result.get('error_text')}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error submitting image CAPTCHA: {e}")
            return None
    
    async def _get_result(self, task_id: str) -> Optional[str]:
        """Poll 2Captcha for CAPTCHA solution"""
        
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                params = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': task_id,
                    'json': 1
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/res.php", params=params) as response:
                        result = await response.json()
                        
                        if result.get('status') == 1:
                            # CAPTCHA solved
                            solution = result.get('request')
                            logger.debug(f"CAPTCHA solved: {solution[:20]}...")
                            return solution
                        elif result.get('error_text') == 'CAPCHA_NOT_READY':
                            # Still processing, wait and try again
                            await asyncio.sleep(self.poll_interval)
                            continue
                        else:
                            # Error occurred
                            logger.error(f"CAPTCHA solving error: {result.get('error_text')}")
                            return None
                            
            except Exception as e:
                logger.error(f"Error polling for CAPTCHA result: {e}")
                await asyncio.sleep(self.poll_interval)
                continue
        
        logger.error("CAPTCHA solving timeout")
        return None
    
    async def get_balance(self) -> Optional[float]:
        """Get 2Captcha account balance"""
        
        if not self.api_key:
            return None
        
        try:
            params = {
                'key': self.api_key,
                'action': 'getbalance',
                'json': 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/res.php", params=params) as response:
                    result = await response.json()
                    
                    if result.get('status') == 1:
                        balance = float(result.get('request', 0))
                        logger.info(f"💰 2Captcha balance: ${balance:.3f}")
                        return balance
                    else:
                        logger.error(f"Failed to get balance: {result.get('error_text')}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None
    
    async def report_good(self, task_id: str) -> bool:
        """Report that CAPTCHA was solved correctly"""
        
        try:
            params = {
                'key': self.api_key,
                'action': 'reportgood',
                'id': task_id,
                'json': 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/res.php", params=params) as response:
                    result = await response.json()
                    return result.get('status') == 1
                    
        except Exception as e:
            logger.error(f"Error reporting good CAPTCHA: {e}")
            return False
    
    async def report_bad(self, task_id: str) -> bool:
        """Report that CAPTCHA was solved incorrectly"""
        
        try:
            params = {
                'key': self.api_key,
                'action': 'reportbad',
                'id': task_id,
                'json': 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/res.php", params=params) as response:
                    result = await response.json()
                    return result.get('status') == 1
                    
        except Exception as e:
            logger.error(f"Error reporting bad CAPTCHA: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get CAPTCHA solving statistics"""
        
        total_attempts = self.total_solved + self.total_failed
        success_rate = (self.total_solved / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            'total_solved': self.total_solved,
            'total_failed': self.total_failed,
            'success_rate': f"{success_rate:.1f}%",
            'total_cost': f"${self.total_cost:.3f}",
            'has_api_key': bool(self.api_key),
            'service_url': self.base_url
        }