# NYC Parking Violations Hybrid Scraper

A powerful hybrid system that combines the NYC Open Data API with targeted web scraping to provide complete parking violation information including ticket images, detailed status, and full violation data.

## 🚀 Features

- **Hybrid Data Collection**: Fast API calls for bulk data + targeted scraping for missing details
- **Complete Violation Details**: Amount due, violation status, hearing information, payment details
- **PDF Ticket Downloads**: Automatically downloads ticket images/PDFs from NYCServ
- **CAPTCHA Solving**: Integrated 2Captcha service for automatic CAPTCHA handling
- **Proxy Support**: Rotating proxy pools for reliability and rate limiting bypass
- **Production Ready**: FastAPI server with health checks, rate limiting, and error handling
- **Modern UI**: Responsive web interface with real-time search and filtering

## 🏗️ Architecture

The system uses a hybrid approach:

1. **NYC Open Data API**: Fast retrieval of basic violation data (1000s of records in seconds)
2. **Targeted Web Scraping**: Only scrapes violations that need enhanced details (status = "UNKNOWN")
3. **Smart Caching**: Prevents duplicate scraping and improves performance
4. **Proxy Rotation**: Ensures reliability and prevents rate limiting

## 📋 Prerequisites

- Python 3.11+
- 2Captcha API key (for CAPTCHA solving)
- Proxy servers (optional but recommended for production)
- Render account (for deployment)

## 🛠️ Local Development Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd nyc-scraper-improved

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values
nano .env
```

Required environment variables:
- `CAPTCHA_API_KEY`: Your 2Captcha API key
- `PROXY_LIST`: Comma-separated list of proxy servers (optional)

### 3. Run Locally

```bash
# Start the server
uvicorn hybrid_server:app --reload --port 8000

# Access the web interface
open http://localhost:8000
```

## 🌐 Render Deployment

### Method 1: Web Service from Git Repository

1. **Connect Repository to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository and branch

2. **Configure Service**:
   - **Name**: `nyc-scraper-hybrid`
   - **Environment**: `Docker`
   - **Region**: `Oregon` (recommended)
   - **Branch**: `main`
   - **Build Command**: (leave empty - handled by Dockerfile)
   - **Start Command**: `uvicorn hybrid_server:app --host 0.0.0.0 --port $PORT --workers 1`

3. **Set Environment Variables**:
   ```
   CAPTCHA_API_KEY=your_2captcha_api_key_here
   PROXY_LIST=http://proxy1:8080,http://proxy2:8080
   PORT=8000
   HOST=0.0.0.0
   DATABASE_URL=sqlite:///./violations.db
   MAX_CONCURRENT_REQUESTS=3
   SCRAPER_HEADLESS=true
   LOG_LEVEL=INFO
   ```

4. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment to complete (5-10 minutes)
   - Access your app at the provided URL

### Method 2: Using render.yaml (Infrastructure as Code)

1. **Add render.yaml to your repository** (already included)

2. **Connect Repository**:
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

3. **Set Required Environment Variables**:
   - In the Render dashboard, go to your service
   - Navigate to "Environment" tab
   - Add your sensitive variables:
     ```
     CAPTCHA_API_KEY=your_actual_api_key
     PROXY_LIST=your_actual_proxy_list
     ```

### Method 3: Manual Docker Deployment

```bash
# Build the Docker image
docker build -t nyc-scraper .

# Run locally with Docker
docker run -p 8000:8000 \
  -e CAPTCHA_API_KEY=your_key \
  -e PROXY_LIST=your_proxies \
  nyc-scraper

# Push to Render's Docker registry
docker tag nyc-scraper registry.render.com/your-service-id/nyc-scraper
docker push registry.render.com/your-service-id/nyc-scraper
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CAPTCHA_API_KEY` | - | **Required**: 2Captcha API key |
| `PROXY_LIST` | - | Comma-separated proxy URLs |
| `PORT` | 8000 | Server port |
| `HOST` | 0.0.0.0 | Server host |
| `DATABASE_URL` | sqlite:///./violations.db | Database connection |
| `MAX_CONCURRENT_REQUESTS` | 5 | Max concurrent scraping requests |
| `SCRAPER_HEADLESS` | true | Run browser in headless mode |
| `SCRAPER_TIMEOUT` | 60000 | Browser timeout (ms) |
| `LOG_LEVEL` | INFO | Logging level |

### Proxy Configuration

Proxies should be in format:
```
http://username:password@host:port
socks5://username:password@host:port
http://host:port
```

Example:
```
PROXY_LIST=http://user:pass@proxy1.com:8080,socks5://user:pass@proxy2.com:1080
```

## 📡 API Endpoints

### Web Interface
- `GET /` - Main dashboard interface

### API Endpoints
- `POST /search` - Hybrid search (API + scraping)
- `POST /api_search` - API-only search (fast)
- `GET /pdf/{plate}/{violation_number}` - Download ticket PDF
- `GET /health` - Health check endpoint
- `GET /stats` - System statistics

### Example API Usage

```bash
# Hybrid search
curl -X POST "https://your-app.onrender.com/search" \
  -H "Content-Type: application/json" \
  -d '{"plate_number": "AW716M", "state": "NJ"}'

# API-only search
curl -X POST "https://your-app.onrender.com/api_search" \
  -H "Content-Type: application/json" \
  -d '{"plate_number": "AW716M", "state": "NJ"}'
```

## 🧪 Testing

Test with the provided sample data:
- **Plate**: AW716M
- **State**: NJ
- **Expected**: 1,951 violations with 603 requiring enhancement

## 📊 Performance

- **API Search**: ~2-3 seconds for 1000+ violations
- **Hybrid Search**: ~30-60 seconds depending on violations needing enhancement
- **Memory Usage**: ~200-500MB depending on concurrent requests
- **Storage**: PDFs cached locally, ~1-5MB per violation

## 🔍 Monitoring

### Health Check
```bash
curl https://your-app.onrender.com/health
```

### Statistics
```bash
curl https://your-app.onrender.com/stats
```

### Logs
Check Render dashboard logs for real-time monitoring.

## 🛡️ Security Considerations

1. **API Keys**: Store sensitive keys in Render environment variables
2. **Rate Limiting**: Built-in rate limiting prevents abuse
3. **Proxy Rotation**: Reduces IP blocking risk
4. **Input Validation**: All inputs are validated and sanitized
5. **HTTPS**: Render provides free SSL certificates

## 🚨 Troubleshooting

### Common Issues

1. **CAPTCHA Failures**:
   - Verify 2Captcha API key is correct
   - Check 2Captcha account balance
   - Monitor CAPTCHA success rate in logs

2. **Proxy Issues**:
   - Test proxy connectivity manually
   - Verify proxy format and credentials
   - Check proxy provider status

3. **Deployment Failures**:
   - Check Render build logs
   - Verify all environment variables are set
   - Ensure Docker build completes successfully

4. **Performance Issues**:
   - Reduce `MAX_CONCURRENT_REQUESTS`
   - Upgrade Render plan for more resources
   - Optimize proxy selection

### Debug Mode

Enable detailed logging:
```bash
LOG_LEVEL=DEBUG
```

## 📈 Scaling

For high-volume usage:

1. **Upgrade Render Plan**: Move from Starter to Standard/Pro
2. **Database**: Switch from SQLite to PostgreSQL
3. **Caching**: Implement Redis for improved caching
4. **Load Balancing**: Deploy multiple instances
5. **Proxy Pools**: Increase proxy diversity

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect NYC.gov terms of service and rate limits.

## 🆘 Support

For issues:
1. Check the troubleshooting section
2. Review Render deployment logs
3. Test with the provided sample data (AW716M, NJ)
4. Open an issue with detailed error logs

## 🔄 Updates

The system automatically handles:
- API endpoint changes
- Website structure updates (within reason)
- Rate limit adjustments
- CAPTCHA solving improvements

For major NYC website changes, code updates may be required.