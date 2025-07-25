"""
Proxy Management System for Web Scraping
Handles proxy rotation, health checking, and failover
"""

import asyncio
import aiohttp
import random
import logging
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
import time
from urllib.parse import urlparse

from config import settings

logger = logging.getLogger(__name__)


class ProxyPool:
    """Manages a pool of proxies with health checking and rotation"""
    
    def __init__(self, proxies: Optional[List[Union[str, Dict]]] = None, check_interval: int = 60):
        """
        Initialize proxy pool
        
        Args:
            proxies: List of proxy URLs or dictionaries with proxy config
            check_interval: How often to check proxy health (seconds)
        """
        self.proxies: List[Dict] = []
        self.healthy_proxies: List[Dict] = []
        self.unhealthy_proxies: List[Dict] = []
        self.check_interval = check_interval
        self.last_check = datetime.min
        self.current_index = 0
        
        # Initialize with provided proxies or from settings
        proxy_list = proxies or settings.proxies
        
        # Parse and initialize proxies
        for proxy in proxy_list:
            if isinstance(proxy, str):
                self.proxies.append(self._parse_proxy_url(proxy))
            elif isinstance(proxy, dict):
                self.proxies.append(proxy)
        
        logger.info(f"🔗 Initialized proxy pool with {len(self.proxies)} proxies")
    
    def _parse_proxy_url(self, proxy_url: str) -> Dict:
        """Parse proxy URL into components"""
        
        # Handle different proxy URL formats
        # http://username:password@host:port
        # http://host:port
        # host:port
        
        if not proxy_url.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
            proxy_url = f"http://{proxy_url}"
        
        parsed = urlparse(proxy_url)
        
        proxy_dict = {
            'url': proxy_url,
            'scheme': parsed.scheme,
            'host': parsed.hostname,
            'port': parsed.port,
            'username': parsed.username,
            'password': parsed.password,
            'healthy': True,
            'last_used': datetime.min,
            'last_check': datetime.min,
            'failures': 0,
            'response_time': 0.0,
            'success_count': 0
        }
        
        return proxy_dict
    
    async def get_proxy(self) -> Optional[Dict]:
        """Get the next healthy proxy in rotation"""
        
        # Check proxy health if needed
        if datetime.now() - self.last_check > timedelta(seconds=self.check_interval):
            await self._check_proxy_health()
        
        if not self.healthy_proxies:
            logger.warning("⚠️ No healthy proxies available")
            return None
        
        # Round-robin selection
        proxy = self.healthy_proxies[self.current_index % len(self.healthy_proxies)]
        self.current_index = (self.current_index + 1) % len(self.healthy_proxies)
        
        proxy['last_used'] = datetime.now()
        logger.debug(f"🔗 Using proxy: {proxy['host']}:{proxy['port']}")
        
        return proxy
    
    async def get_random_proxy(self) -> Optional[Dict]:
        """Get a random healthy proxy"""
        
        if datetime.now() - self.last_check > timedelta(seconds=self.check_interval):
            await self._check_proxy_health()
        
        if not self.healthy_proxies:
            return None
        
        proxy = random.choice(self.healthy_proxies)
        proxy['last_used'] = datetime.now()
        
        return proxy
    
    async def report_proxy_failure(self, proxy: Dict, error: str = ""):
        """Report that a proxy failed"""
        
        proxy['failures'] += 1
        logger.warning(f"⚠️ Proxy failure: {proxy['host']}:{proxy['port']} ({proxy['failures']} failures) - {error}")
        
        # Mark as unhealthy if too many failures
        if proxy['failures'] >= 3:
            proxy['healthy'] = False
            if proxy in self.healthy_proxies:
                self.healthy_proxies.remove(proxy)
            if proxy not in self.unhealthy_proxies:
                self.unhealthy_proxies.append(proxy)
            
            logger.error(f"❌ Marked proxy as unhealthy: {proxy['host']}:{proxy['port']}")
    
    async def _check_proxy_health(self):
        """Check health of all proxies"""
        
        logger.info("🔍 Checking proxy health...")
        
        tasks = []
        for proxy in self.proxies:
            tasks.append(self._check_single_proxy(proxy))
        
        # Run health checks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update healthy/unhealthy lists
        self.healthy_proxies = [p for p in self.proxies if p['healthy']]
        self.unhealthy_proxies = [p for p in self.proxies if not p['healthy']]
        
        self.last_check = datetime.now()
        
        logger.info(f"✅ Health check complete: {len(self.healthy_proxies)} healthy, {len(self.unhealthy_proxies)} unhealthy")
    
    async def _check_single_proxy(self, proxy: Dict):
        """Check health of a single proxy"""
        
        start_time = time.time()
        
        try:
            # Test URL - use a simple, fast endpoint
            test_url = "http://httpbin.org/ip"
            
            # Configure proxy for aiohttp
            proxy_url = proxy['url']
            
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(test_url, proxy=proxy_url) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        
                        # Proxy is healthy
                        proxy['healthy'] = True
                        proxy['last_check'] = datetime.now()
                        proxy['response_time'] = response_time
                        proxy['success_count'] += 1
                        proxy['failures'] = max(0, proxy['failures'] - 1)  # Reduce failure count on success
                        
                        logger.debug(f"✅ Proxy {proxy['host']}:{proxy['port']} healthy ({response_time:.2f}s)")
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            # Proxy is unhealthy
            proxy['healthy'] = False
            proxy['last_check'] = datetime.now()
            proxy['failures'] += 1
            
            logger.debug(f"❌ Proxy {proxy['host']}:{proxy['port']} unhealthy: {e}")
    
    def get_proxy_for_playwright(self, proxy_dict: Dict) -> Optional[Dict]:
        """Convert proxy dict to Playwright format"""
        
        if not proxy_dict:
            return None
        
        playwright_proxy = {
            'server': f"{proxy_dict['scheme']}://{proxy_dict['host']}:{proxy_dict['port']}"
        }
        
        if proxy_dict['username'] and proxy_dict['password']:
            playwright_proxy['username'] = proxy_dict['username']
            playwright_proxy['password'] = proxy_dict['password']
        
        return playwright_proxy
    
    def get_proxy_for_aiohttp(self, proxy_dict: Dict) -> Optional[str]:
        """Convert proxy dict to aiohttp format"""
        
        if not proxy_dict:
            return None
        
        return proxy_dict['url']
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get proxy pool statistics"""
        
        if not self.proxies:
            return {
                'total_proxies': 0,
                'healthy_proxies': 0,
                'unhealthy_proxies': 0,
                'average_response_time': 0.0,
                'last_health_check': None
            }
        
        # Calculate average response time for healthy proxies
        healthy_response_times = [p['response_time'] for p in self.healthy_proxies if p['response_time'] > 0]
        avg_response_time = sum(healthy_response_times) / len(healthy_response_times) if healthy_response_times else 0.0
        
        # Get best and worst performing proxies
        best_proxy = min(self.healthy_proxies, key=lambda x: x['response_time']) if self.healthy_proxies else None
        worst_proxy = max(self.healthy_proxies, key=lambda x: x['response_time']) if self.healthy_proxies else None
        
        return {
            'total_proxies': len(self.proxies),
            'healthy_proxies': len(self.healthy_proxies),
            'unhealthy_proxies': len(self.unhealthy_proxies),
            'average_response_time': f"{avg_response_time:.2f}s",
            'last_health_check': self.last_check.isoformat() if self.last_check != datetime.min else None,
            'best_proxy': f"{best_proxy['host']}:{best_proxy['port']} ({best_proxy['response_time']:.2f}s)" if best_proxy else None,
            'worst_proxy': f"{worst_proxy['host']}:{worst_proxy['port']} ({worst_proxy['response_time']:.2f}s)" if worst_proxy else None,
            'check_interval': self.check_interval
        }
    
    def has_healthy_proxies(self) -> bool:
        """Check if there are any healthy proxies available"""
        return len(self.healthy_proxies) > 0