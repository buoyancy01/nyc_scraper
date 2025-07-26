"""
Enhanced NYC Open Data API Client
Fetches parking violation data with pagination, rate limiting, and error handling
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

from models import ViolationData
from config import settings

logger = logging.getLogger(__name__)


class NYCViolationsAPI:
    """Enhanced client for NYC Open Data parking violations API"""
    
    def __init__(self):
        self.base_url = settings.NYC_API_BASE_URL
        self.timeout = settings.NYC_API_TIMEOUT
        self.rate_limit = settings.API_RATE_LIMIT
        self.last_request_time = 0
        
        # Performance tracking
        self.request_count = 0
        self.total_response_time = 0
        
    async def search_violations(self, 
                              license_plate: str, 
                              state: str = "NY",
                              limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for parking violations by license plate and state
        
        Args:
            license_plate: License plate number
            state: State abbreviation (2 letters)
            limit: Maximum number of violations to return
            
        Returns:
            Dictionary with violations data and metadata
        """
        
        start_time = time.time()
        plate = license_plate.upper().strip()
        state = state.upper().strip()
        
        logger.info(f"🔍 Searching violations for {plate} ({state})")
        
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Fetch all violations with pagination
            violations_data = await self._fetch_all_violations(plate, state, limit)
            
            # Convert to ViolationData objects
            violations = []
            for item in violations_data:
                try:
                    violation = self._parse_violation(item, plate, state)
                    violations.append(violation)
                except Exception as e:
                    logger.warning(f"Failed to parse violation: {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            # Update performance metrics
            self.request_count += 1
            self.total_response_time += processing_time
            
            result = {
                'plate_number': plate,  # Changed from license_plate
                'state': state,
                'violations': [v.dict() for v in violations],  # Convert to dicts
                'total_violations': len(violations),
                'processing_time': processing_time,
                'success': True,
                'error': None,
                'debug_info': {
                    'api_url': self.base_url,
                    'raw_count': len(violations_data),
                    'parsed_count': len(violations)
                },
                'raw_data': violations_data[:5] if violations_data else []  # Sample for debugging
            }
            
            logger.info(f"✅ Found {len(violations)} violations in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"API search failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                'plate_number': plate,  # Changed from license_plate
                'state': state,
                'violations': [],
                'total_violations': 0,
                'processing_time': processing_time,
                'success': False,
                'error': error_msg,
                'debug_info': {'api_url': self.base_url},
                'raw_data': []
            }
    
    async def _fetch_all_violations(self, 
                                  plate: str, 
                                  state: str, 
                                  limit: Optional[int] = None) -> List[Dict]:
        """Fetch all violations with pagination"""
        
        all_violations = []
        offset = 0
        batch_size = 1000  # API limit per request
        
        logger.info(f"Fetching violations for {plate} ({state}) from {self.base_url}")
        
        while True:
            # Build query parameters
            params = {
                '$where': f"plate='{plate}' AND registration_state='{state}'",
                '$limit': min(batch_size, limit - len(all_violations)) if limit else batch_size,
                '$offset': offset,
                '$order': 'issue_date DESC'
            }
            
            logger.debug(f"API request params: {params}")
            
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.get(self.base_url, params=params) as response:
                        logger.info(f"API response status: {response.status}")
                        
                        if response.status == 200:
                            batch_data = await response.json()
                            logger.info(f"Received {len(batch_data)} violations in this batch")
                            
                            if not batch_data:
                                logger.info("No more data available")
                                break  # No more data
                            
                            # Log sample data for debugging
                            if batch_data:
                                logger.debug(f"Sample violation data: {batch_data[0]}")
                            
                            all_violations.extend(batch_data)
                            
                            # Check if we've reached the limit
                            if limit and len(all_violations) >= limit:
                                all_violations = all_violations[:limit]
                                break
                            
                            # Check if we got less than batch_size (last page)
                            if len(batch_data) < batch_size:
                                break
                            
                            offset += batch_size
                            
                            # Small delay between requests
                            await asyncio.sleep(0.1)
                            
                        else:
                            response_text = await response.text()
                            logger.error(f"API returned status {response.status}: {response_text}")
                            break
                            
            except Exception as e:
                logger.error(f"Error fetching batch at offset {offset}: {e}")
                break
        
        logger.info(f"Fetched {len(all_violations)} total violations")
        return all_violations
    
    def _parse_violation(self, data: Dict[str, Any], plate: str, state: str) -> ViolationData:
        """Parse raw API data into ViolationData object"""
        
        # Helper function to safely get float values
        def safe_float(value) -> float:
            try:
                return float(value) if value else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        # Helper function to safely get string values
        def safe_str(value) -> Optional[str]:
            return str(value).strip() if value else None
        
        # Parse summons image URL
        summons_image = None
        if data.get('summons_number'):
            # Construct the NYCServ PDF URL
            import base64
            search_id = base64.b64encode(data['summons_number'].encode()).decode()
            summons_image = {
                'url': f"http://nycserv.nyc.gov/NYCServWeb/ShowImage?searchID={search_id}&locationName=_____________________",
                'description': 'View Summons'
            }
        
        return ViolationData(
            plate_number=plate,
            state=safe_str(data.get('registration_state', state)),
            license_type=safe_str(data.get('license_type')),
            violation_number=safe_str(data.get('summons_number', '')),  # Use summons_number as violation_number
            summons_number=safe_str(data.get('summons_number', '')),
            violation_code=safe_str(data.get('violation_code', '')),
            violation_description=safe_str(data.get('violation_description', '')),
            
            issue_date=safe_str(data.get('issue_date', '')),
            violation_time=safe_str(data.get('violation_time')),
            judgment_entry_date=safe_str(data.get('judgment_entry_date')),
            
            fine_amount=safe_float(data.get('fine_amount')),
            penalty_amount=safe_float(data.get('penalty_amount')),
            interest_amount=safe_float(data.get('interest_amount')),
            reduction_amount=safe_float(data.get('reduction_amount')),
            payment_amount=safe_float(data.get('payment_amount')),
            amount_due=safe_float(data.get('amount_due')),
            
            violation_location=safe_str(data.get('violation_location') or data.get('street_name') or data.get('house_number')),
            precinct=safe_str(data.get('precinct')),
            county=safe_str(data.get('county')),
            issuing_agency=safe_str(data.get('issuing_agency')),
            
            status=self._determine_status(data),
            pdf_available=bool(data.get('summons_number')),  # PDF available if summons_number exists
            enhanced_by_scraping=False,  # Initially false, will be updated by scraper
            summons_image=summons_image,
            local_pdf_path=None,
            
            last_updated=datetime.now()
        )
    
    def _determine_status(self, data: Dict[str, Any]) -> str:
        """Determine violation status from API data"""
        
        amount_due = float(data.get('amount_due', 0))
        payment_amount = float(data.get('payment_amount', 0))
        fine_amount = float(data.get('fine_amount', 0))
        
        if amount_due <= 0 and payment_amount > 0:
            return "PAID"
        elif amount_due > 0:
            return "OUTSTANDING"
        else:
            return "UNKNOWN"
    
    async def _rate_limit(self):
        """Simple rate limiting to avoid overwhelming the API"""
        
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 60.0 / self.rate_limit  # seconds between requests
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get API client performance statistics"""
        
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            'total_requests': self.request_count,
            'average_response_time': avg_response_time,
            'api_endpoint': self.base_url,
            'rate_limit': self.rate_limit,
            'timeout': self.timeout
        }