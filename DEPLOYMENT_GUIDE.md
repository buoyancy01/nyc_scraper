# 🚀 DEPLOYMENT CHECKLIST - NYC Hybrid Scraper

## ✅ REQUIRED CHANGES TO DEPLOY

### 1. **Add Your 2Captcha API Key** (REQUIRED for web scraping)

**File to change:** Create `.env` file in `/project/workspace/nyc-scraper-improved/`

```bash
# Create this file: .env
TWOCAPTCHA_API_KEY=your_actual_2captcha_api_key_here
PROXY_LIST=http://proxy1:port,http://proxy2:port  # Optional
MONGODB_URL=mongodb://localhost:27017            # Optional
```

**How to get 2Captcha API key:**
1. Sign up at https://2captcha.com
2. Go to your dashboard
3. Copy the API key
4. Replace `your_actual_2captcha_api_key_here` with your real key

### 2. **Install Missing Dependencies** (if not done)

```bash
cd /project/workspace/nyc-scraper-improved
pip install fastapi uvicorn pydantic motor
python -m playwright install chromium
```

### 3. **Start the Server**

```bash
cd /project/workspace/nyc-scraper-improved
python hybrid_server.py
```

**Server will run on:** `http://localhost:8000`

---

## 🎯 OPTIONAL CONFIGURATIONS

### **Add Proxies** (Recommended for production)

**File to modify:** `.env` (same file as above)

```bash
# Add proxy list (comma-separated)
PROXY_LIST=http://user:pass@proxy1.com:8080,http://user:pass@proxy2.com:3128
```

### **Database Setup** (Optional - for storing results)

```bash
# Install MongoDB (optional)
docker run -d --name mongodb -p 27017:27017 mongo:latest

# Add to .env file
MONGODB_URL=mongodb://localhost:27017
```

---

## 🧪 TEST YOUR DEPLOYMENT

### **Test 1: Basic API Search**
```bash
curl -X POST "http://localhost:8000/violations/AW716M/NJ" 
```

### **Test 2: Enhanced Search** (with web scraping)
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"plate": "AW716M", "state": "NJ", "enhance": true}'
```

### **Test 3: Web Interface**
Open browser: `http://localhost:8000`

---

## 📁 FILES YOU **DON'T** NEED TO CHANGE

These files are already optimized and ready:

✅ `hybrid_server.py` - Main server (ready)  
✅ `hybrid_service.py` - Core logic (ready)  
✅ `nyc_api_client.py` - API client (ready)  
✅ `nycserv_scraper.py` - Web scraper (ready)  
✅ `enhanced_captcha_client.py` - CAPTCHA solver (ready)  
✅ `proxy_manager.py` - Proxy rotation (ready)  
✅ `enhanced_dashboard.html` - Web interface (ready)  
✅ `requirements.txt` - Dependencies (ready)  

---

## ⚡ QUICK START (3 Steps)

### **Step 1:** Create `.env` file
```bash
cd /project/workspace/nyc-scraper-improved
echo "TWOCAPTCHA_API_KEY=your_key_here" > .env
```

### **Step 2:** Install dependencies  
```bash
pip install fastapi uvicorn pydantic motor
```

### **Step 3:** Start server
```bash
python hybrid_server.py
```

**Done!** 🎉 Visit `http://localhost:8000` to use your scraper.

---

## 🎯 USAGE EXAMPLES

### **API-Only Search** (Fast - 1-2 seconds)
```bash
curl "http://localhost:8000/violations/AW716M/NJ"
```

### **Enhanced Search** (API + Web Scraping - 30-60 seconds)
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"plate": "AW716M", "state": "NJ", "enhance": true}'
```

### **Download PDF**
```bash
curl "http://localhost:8000/download-pdf/5601100445" --output ticket.pdf
```

---

## 🚨 TROUBLESHOOTING

### **Error: "No module named 'fastapi'"**
```bash
pip install fastapi uvicorn
```

### **Error: "2Captcha API key required"**
- Add your real API key to `.env` file
- Make sure file is in the correct directory

### **Error: "Playwright browser not found"**
```bash
python -m playwright install chromium
```

### **Error: "Port 8000 already in use"**
```bash
# Kill existing server
pkill -f "python.*server"
# Or change port in hybrid_server.py (line with uvicorn.run)
```

---

## 📊 EXPECTED PERFORMANCE

- **API Search**: 1-3 seconds for any number of violations
- **Enhanced Search**: +2-5 seconds per violation needing details
- **CAPTCHA Solving**: 10-30 seconds when required
- **PDF Download**: 1-2 seconds per PDF

**For AW716M specifically:**
- **API search**: ~2 seconds (1,951 violations)
- **Enhanced search**: ~20-30 minutes (603 violations need scraping)
- **PDF downloads**: ~65 minutes (1,951 PDFs)

---

## ✨ SUMMARY

**ONLY 1 FILE TO CREATE:**
1. **.env** - Add your 2Captcha API key

**COMMANDS TO RUN:**
1. `pip install fastapi uvicorn pydantic motor`
2. `python hybrid_server.py`

**That's it!** Your hybrid scraper is ready! 🚀