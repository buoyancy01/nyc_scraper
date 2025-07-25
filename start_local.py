#!/usr/bin/env python3
"""
Local development startup script for NYC Scraper
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import uvicorn
        import fastapi
        import playwright
        print("✅ All Python requirements found")
        return True
    except ImportError as e:
        print(f"❌ Missing requirement: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_playwright():
    """Check if Playwright browsers are installed"""
    try:
        result = subprocess.run(['playwright', 'list'], 
                              capture_output=True, text=True, check=True)
        if 'chromium' in result.stdout:
            print("✅ Playwright browsers installed")
            return True
        else:
            print("❌ Chromium browser not found")
            print("Run: playwright install chromium")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Playwright not found or browsers not installed")
        print("Run: playwright install chromium")
        return False

def check_env_file():
    """Check if .env file exists"""
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found")
        print("Copy .env.example to .env and configure your settings")
        return False

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting NYC Scraper server...")
    print("📝 Access the web interface at: http://localhost:8000")
    print("📊 Health check at: http://localhost:8000/health")
    print("🔍 Test with plate: AW716M, state: NJ")
    print("\n🛑 Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'hybrid_server:app', 
            '--reload', 
            '--host', '0.0.0.0',
            '--port', '8000'
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")

def main():
    print("🔍 NYC Parking Violations Hybrid Scraper - Local Setup")
    print("=" * 60)
    
    # Check all requirements
    checks_passed = 0
    total_checks = 3
    
    if check_requirements():
        checks_passed += 1
    
    if check_playwright():
        checks_passed += 1
        
    if check_env_file():
        checks_passed += 1
    
    print(f"\n📊 Setup Status: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("✅ All checks passed! Starting server...")
        start_server()
    else:
        print("❌ Some requirements missing. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()