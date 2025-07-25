#!/usr/bin/env python3
"""
Test script to verify NYC Scraper setup
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_api_client():
    """Test NYC API client"""
    print("🧪 Testing NYC API client...")
    try:
        from nyc_api_client import NYCViolationsAPIClient
        
        client = NYCViolationsAPIClient()
        result = await client.search_violations("AW716M", "NJ", limit=5)
        
        if result:
            print(f"✅ API client working - found {len(result)} violations")
            return True
        else:
            print("⚠️  API client returned no results")
            return False
    except Exception as e:
        print(f"❌ API client failed: {e}")
        return False

async def test_captcha_client():
    """Test 2Captcha client"""
    print("🧪 Testing 2Captcha client...")
    try:
        from enhanced_captcha_client import Enhanced2CaptchaClient
        
        api_key = os.getenv('CAPTCHA_API_KEY')
        if not api_key:
            print("⚠️  CAPTCHA_API_KEY not set - skipping test")
            return False
            
        client = Enhanced2CaptchaClient(api_key)
        
        # Test balance check (doesn't solve a captcha)
        balance = await client.get_balance()
        if balance >= 0:
            print(f"✅ 2Captcha client working - balance: ${balance:.2f}")
            return True
        else:
            print("❌ 2Captcha client failed to get balance")
            return False
    except Exception as e:
        print(f"❌ 2Captcha client failed: {e}")
        return False

async def test_proxy_manager():
    """Test proxy manager"""
    print("🧪 Testing proxy manager...")
    try:
        from proxy_manager import ProxyPool
        
        proxy_list = os.getenv('PROXY_LIST', '').split(',')
        proxy_list = [p.strip() for p in proxy_list if p.strip()]
        
        if not proxy_list:
            print("⚠️  No proxies configured - skipping test")
            return False
            
        pool = ProxyPool(proxy_list)
        proxy = await pool.get_proxy()
        
        if proxy:
            print(f"✅ Proxy manager working - got proxy: {proxy['url']}")
            return True
        else:
            print("❌ No working proxies found")
            return False
    except Exception as e:
        print(f"❌ Proxy manager failed: {e}")
        return False

async def test_scraper():
    """Test web scraper (basic initialization)"""
    print("🧪 Testing web scraper initialization...")
    try:
        from nycserv_scraper import NYCServScraper
        
        scraper = NYCServScraper()
        # Just test initialization, not actual scraping
        print("✅ Web scraper initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Web scraper failed to initialize: {e}")
        return False

async def test_hybrid_service():
    """Test hybrid service"""
    print("🧪 Testing hybrid service...")
    try:
        from hybrid_service import HybridViolationsService
        
        service = HybridViolationsService()
        print("✅ Hybrid service initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Hybrid service failed: {e}")
        return False

def test_environment():
    """Test environment variables"""
    print("🧪 Testing environment configuration...")
    
    required_vars = ['CAPTCHA_API_KEY']
    optional_vars = ['PROXY_LIST', 'DATABASE_URL', 'LOG_LEVEL']
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_required:
        print(f"❌ Missing required variables: {', '.join(missing_required)}")
        return False
    else:
        print("✅ Required environment variables found")
        if missing_optional:
            print(f"⚠️  Optional variables not set: {', '.join(missing_optional)}")
        return True

async def run_full_test():
    """Run a limited end-to-end test"""
    print("🧪 Running limited end-to-end test...")
    try:
        from hybrid_service import HybridViolationsService
        
        service = HybridViolationsService()
        
        # Test API-only search (safe and fast)
        print("Testing API-only search...")
        request_data = {
            "plate_number": "AW716M", 
            "state": "NJ"
        }
        
        result = await service.search_api_only(request_data)
        
        if result and result.violations:
            print(f"✅ End-to-end test passed - found {len(result.violations)} violations")
            print(f"   Sample violation: {result.violations[0].violation_code}")
            return True
        else:
            print("❌ End-to-end test failed - no violations found")
            return False
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return False

async def main():
    print("🔬 NYC Scraper Setup Test Suite")
    print("=" * 50)
    
    # Environment test (synchronous)
    env_ok = test_environment()
    
    # Component tests (asynchronous)
    tests = [
        ("API Client", test_api_client),
        ("2Captcha Client", test_captcha_client),
        ("Proxy Manager", test_proxy_manager),
        ("Web Scraper", test_scraper),
        ("Hybrid Service", test_hybrid_service),
        ("End-to-End", run_full_test),
    ]
    
    passed = 1 if env_ok else 0
    total = len(tests) + 1
    
    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("🚀 Run 'python start_local.py' to start the server")
    elif passed >= total - 2:
        print("⚠️  Most tests passed. You can probably run the server with limited functionality.")
    else:
        print("❌ Multiple tests failed. Check your configuration.")
        
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())