# 🚀 Render Deployment Guide

This guide will help you deploy the NYC Scraper to Render in under 10 minutes.

## 📋 Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Push this code to your GitHub repo
3. **2Captcha Account**: Get API key from [2captcha.com](https://2captcha.com)
4. **Proxies** (optional): List of proxy servers for production

## 🎯 Quick Deploy (5 minutes)

### Step 1: Push Code to GitHub

```bash
# Initialize git repo (if not already done)
git init
git add .
git commit -m "Initial commit - NYC Scraper"

# Push to GitHub
git remote add origin https://github.com/yourusername/nyc-scraper.git
git push -u origin main
```

### Step 2: Create Render Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect a repository"**
4. Select your GitHub repository
5. Configure the service:

   **Basic Settings:**
   - **Name**: `nyc-scraper-hybrid`
   - **Environment**: `Docker`
   - **Region**: `Oregon` (recommended)
   - **Branch**: `main`

   **Build & Deploy:**
   - **Build Command**: (leave empty)
   - **Start Command**: `uvicorn hybrid_server:app --host 0.0.0.0 --port $PORT --workers 1`

### Step 3: Set Environment Variables

In the Render dashboard, go to your service → **Environment** tab and add:

**Required:**
```
CAPTCHA_API_KEY=your_2captcha_api_key_here
```

**Recommended:**
```
PROXY_LIST=http://proxy1:8080,http://proxy2:8080,socks5://proxy3:1080
PORT=8000
HOST=0.0.0.0
MAX_CONCURRENT_REQUESTS=3
SCRAPER_HEADLESS=true
LOG_LEVEL=INFO
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for build to complete
3. Access your app at: `https://your-service-name.onrender.com`

## 🧪 Test Your Deployment

Once deployed, test with:
- **Plate**: AW716M
- **State**: NJ
- **Expected**: 1,951 violations

## 📊 Monitor Your App

### Health Check
```
https://your-app.onrender.com/health
```

### View Logs
1. Go to Render Dashboard
2. Select your service
3. Click "Logs" tab for real-time monitoring

## ⚙️ Configuration Options

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CAPTCHA_API_KEY` | ✅ | - | 2Captcha API key |
| `PROXY_LIST` | ⚠️ | - | Comma-separated proxy URLs |
| `PORT` | ❌ | 8000 | Server port |
| `HOST` | ❌ | 0.0.0.0 | Server host |
| `MAX_CONCURRENT_REQUESTS` | ❌ | 5 | Max scraping threads |
| `SCRAPER_HEADLESS` | ❌ | true | Headless browser mode |
| `SCRAPER_TIMEOUT` | ❌ | 60000 | Browser timeout (ms) |
| `LOG_LEVEL` | ❌ | INFO | Logging level |

### Proxy Format Examples

```bash
# HTTP proxy with auth
http://username:password@proxy.example.com:8080

# SOCKS5 proxy
socks5://username:password@proxy.example.com:1080

# HTTP proxy without auth
http://proxy.example.com:8080

# Multiple proxies (comma-separated)
PROXY_LIST=http://proxy1:8080,socks5://user:pass@proxy2:1080,http://proxy3:3128
```

## 🔧 Troubleshooting

### Common Issues

**1. Build Fails**
- Check that all files are in the repository
- Verify Dockerfile syntax
- Review build logs in Render dashboard

**2. Service Won't Start**
- Check environment variables are set
- Verify CAPTCHA_API_KEY is valid
- Review startup logs

**3. Slow Performance**
- Reduce MAX_CONCURRENT_REQUESTS to 2-3
- Upgrade Render plan (Starter → Standard)
- Add quality proxy servers

**4. CAPTCHA Errors**
- Verify 2Captcha account has sufficient balance
- Check API key format
- Monitor captcha success rate in logs

### Debug Steps

1. **Check Health Endpoint**:
   ```
   curl https://your-app.onrender.com/health
   ```

2. **View Real-time Logs**:
   - Render Dashboard → Your Service → Logs

3. **Test API Directly**:
   ```bash
   curl -X POST https://your-app.onrender.com/api_search \
     -H "Content-Type: application/json" \
     -d '{"plate_number": "AW716M", "state": "NJ"}'
   ```

## 🚀 Performance Optimization

### For High Volume Usage

1. **Upgrade Render Plan**:
   - Starter: 0.5 CPU, 512 MB RAM
   - Standard: 1 CPU, 2 GB RAM
   - Pro: 2 CPU, 4 GB RAM

2. **Optimize Settings**:
   ```bash
   MAX_CONCURRENT_REQUESTS=2  # For Starter plan
   MAX_CONCURRENT_REQUESTS=5  # For Standard plan
   MAX_CONCURRENT_REQUESTS=8  # For Pro plan
   ```

3. **Database Upgrade**:
   - For production, consider PostgreSQL addon
   - Update DATABASE_URL environment variable

4. **Add Redis Caching**:
   - Install Redis addon in Render
   - Implement Redis caching in the code

## 💰 Cost Estimation

**Render Costs:**
- Starter Plan: $7/month (good for testing)
- Standard Plan: $25/month (recommended for production)
- Pro Plan: $85/month (high volume)

**Additional Costs:**
- 2Captcha: ~$1-3 per 1000 captchas solved
- Proxies: $10-50/month depending on quality/quantity

## 🔄 Updates and Maintenance

### Deploy Updates
1. Push changes to GitHub
2. Render auto-deploys from main branch
3. Monitor deployment in dashboard

### Backup Important Data
- Download violation data periodically
- Export configuration settings
- Keep proxy lists updated

## 📞 Support

If you encounter issues:

1. **Check Logs**: Render Dashboard → Logs
2. **Test Components**: Run test_setup.py locally
3. **Verify Config**: Compare with .env.example
4. **Monitor Resources**: Check CPU/memory usage in Render

## 🎉 Success Checklist

- ✅ Service builds successfully
- ✅ Health check returns 200 OK
- ✅ Web interface loads
- ✅ API search works with test data
- ✅ Environment variables configured
- ✅ Logs show no critical errors

Your NYC Scraper is now live and ready to handle parking violation searches! 🚗💨