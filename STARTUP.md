# MillionX App Startup Guide 🚀

Quick commands to launch the complete MillionX demo application.

---

## 📋 Prerequisites

- Docker Desktop running
- Node.js installed (v18+)
- PowerShell/Terminal open

---

## 🔧 One-Time Setup (First Time Only)

```powershell
# Navigate to project root
cd G:\MillionX-mvp

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## 🚀 Start Both Ends (Quick Launch)

### Open 2 Terminal Windows:

### **Terminal 1: Backend (FastAPI + Redis)**

```powershell
cd G:\MillionX-mvp

# Start Docker containers (FastAPI + Redis)
docker-compose up -d

# Wait 10 seconds for services to start
Start-Sleep -Seconds 10

# Verify backend is running
curl http://localhost:8000/health
```

**Expected Output:**

```json
{ "status": "healthy", "service": "COD Shield", "redis": "connected" }
```

---

### **Terminal 2: Frontend (Vite Dev Server)**

```powershell
cd G:\MillionX-mvp\frontend

# Start Vite dev server
npm run dev
```

**Expected Output:**

```
VITE v7.3.0  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

## ✅ Verification Checklist

### 1. Backend Health Check

```powershell
# API responding?
Invoke-RestMethod http://localhost:8000/health

# Forecasts endpoint working?
Invoke-RestMethod "http://localhost:8000/api/v1/inventory/forecast?limit=1"
```

### 2. Frontend Access

- Open browser: **http://localhost:5173**
- Should see MillionX onboarding screen with QR code
- Click "Skip & Explore Dashboard" → See 46 product cards

### 3. Docker Containers Running

```powershell
docker ps

# Should show:
# - millionx-fastapi (port 8000)
# - millionx-redis (port 6379)
```

---

## 🛑 Shutdown Commands

### Stop Everything:

```powershell
# Stop frontend (in Terminal 2)
Ctrl+C

# Stop backend containers (in Terminal 1)
cd G:\MillionX-mvp
docker-compose down
```

### Quick Restart:

```powershell
# Restart just the backend
docker-compose restart fastapi

# Frontend auto-restarts (just save any file)
```

---

## 🔥 Full Clean Restart (if issues)

```powershell
# Stop all containers
docker-compose down

# Remove old database
Remove-Item ai-core\millionx_ai.db -ErrorAction SilentlyContinue

# Rebuild containers
docker-compose up -d --build

# Clear browser cache (Ctrl+Shift+Delete)

# Restart frontend
cd frontend
npm run dev
```

---

## 📊 Service URLs

| Service          | URL                          | Purpose           |
| ---------------- | ---------------------------- | ----------------- |
| **Frontend**     | http://localhost:5173        | React UI (Vite)   |
| **Backend API**  | http://localhost:8000        | FastAPI (Docker)  |
| **API Docs**     | http://localhost:8000/docs   | Swagger UI        |
| **Health Check** | http://localhost:8000/health | Status endpoint   |
| **Redis**        | localhost:6379               | Blacklist storage |

---

## 🐛 Troubleshooting

### Problem: "Port 8000 already in use"

```powershell
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Or use different port
$env:PORT=8001
docker-compose up -d
```

### Problem: "Failed to load forecasts"

```powershell
# Check if backend is running
docker logs millionx-fastapi --tail 20

# Restart backend
docker-compose restart fastapi
```

### Problem: Frontend shows blank page

```powershell
# Clear node_modules and reinstall
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
npm run dev
```

### Problem: Database empty (no products)

```powershell
# Regenerate database
cd ai-core
python -c "from forecasting import DemandForecaster; print('DB exists')"

# If error, run setup script from HOW-TO-ADD-MORE-PRODUCTS.md
```

### Problem: CORS errors in browser

- Check backend logs: `docker logs millionx-fastapi`
- Verify CORS is enabled for `http://localhost:5173`
- Restart backend: `docker-compose restart fastapi`

---

## 🎯 Quick Test After Startup

Run this 30-second smoke test:

```powershell
# 1. Backend responding?
curl http://localhost:8000/health

# 2. Can fetch products?
Invoke-RestMethod "http://localhost:8000/api/v1/inventory/forecast?limit=1"

# 3. Frontend running?
# Open http://localhost:5173 in browser
# Should see onboarding screen ✅

# 4. Click through demo:
# - Skip onboarding
# - See product cards with images
# - Click any card → modal with graph
# - Click Bhai-Bot → chat opens
# - Test COD Shield with phone number
```

**If all ✅ → Ready to demo! 🎉**

---

## 📝 Environment Variables (Optional)

Create `.env` files if needed:

**Backend:** `ai-core/.env`

```env
DATABASE_URL=sqlite:///millionx_ai.db
REDIS_HOST=localhost
REDIS_PORT=6379
FORECAST_DAYS=7
```

**Frontend:** `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
```

---

## 🚀 Production Deployment (Future)

For production deployment:

```powershell
# Build frontend
cd frontend
npm run build

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d

# Use nginx/caddy as reverse proxy
```

---

## 💡 Quick Reference

**Most Common Commands:**

```powershell
# Start everything
docker-compose up -d && cd frontend && npm run dev

# Stop everything
Ctrl+C (frontend) && docker-compose down

# Restart backend only
docker-compose restart fastapi

# View backend logs
docker logs millionx-fastapi --follow

# Check running containers
docker ps

# Open app
start http://localhost:5173
```

---

## 🎓 First Time User Guide

**Never used this before? Follow these exact steps:**

1. Open PowerShell as Administrator
2. Navigate: `cd G:\MillionX-mvp`
3. Start backend: `docker-compose up -d`
4. Wait 10 seconds
5. Open NEW PowerShell window
6. Navigate: `cd G:\MillionX-mvp\frontend`
7. Start frontend: `npm run dev`
8. Open browser: `http://localhost:5173`
9. **Done!** 🎉

---

**Need help?** Check [FRONTEND-TESTING-CHECKLIST.md](FRONTEND-TESTING-CHECKLIST.md) for feature testing guide.
