# Render Deployment Guide - TUSHI Chess Bot

Complete step-by-step guide to deploy both frontend and backend on Render.

## Prerequisites

- GitHub repository: `https://github.com/uchihaitachilz/Ai-chess-bot.git`
- Render account (free tier works)
- OpenAI API key (optional, for enhanced commentary)

---

## Part 1: Backend Deployment (FastAPI)

### Step 1: Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `uchihaitachilz/Ai-chess-bot`

### Step 2: Configure Backend Service

**Basic Settings:**
- **Name:** `tushi-chess-bot-backend` (or any name you prefer)
- **Region:** Choose closest to you (Oregon, Frankfurt, etc.)
- **Branch:** `main`
- **Root Directory:** `server`
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add Environment Variables (Backend)

Click **"Advanced"** → **"Add Environment Variable"** and add:

```
ENGINE_PATH=/usr/bin/stockfish
ENGINE_DEPTH=12
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
PORT=10000
```

**Important Notes:**
- `ENGINE_PATH` might need to be `/usr/games/stockfish` on some systems
- `OPENAI_API_KEY` is optional - if not provided, uses rule-based commentary
- `PORT` is automatically set by Render, but we include it for reference

### Step 4: Install Stockfish (Important!)

Render doesn't have Stockfish pre-installed. You need to add it to your build:

**Option A: Add to requirements.txt (Recommended)**
Add this to `server/requirements.txt`:
```
# Stockfish will be installed via system package
```

**Option B: Use Build Script**
Create `server/render-build.sh`:
```bash
#!/bin/bash
sudo apt-get update
sudo apt-get install -y stockfish
```

Then update Build Command to:
```bash
chmod +x render-build.sh && ./render-build.sh && pip install -r requirements.txt
```

**Option C: Use Python Stockfish Package**
Update `server/requirements.txt`:
```
stockfish==3.28.0
```

And update `server/engine/stockfish.py` to use the Python package instead.

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Copy the service URL (e.g., `https://tushi-chess-bot-backend.onrender.com`)

---

## Part 2: Frontend Deployment (React/Vite)

### Step 1: Create New Static Site

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Static Site"**
3. Connect your GitHub repository: `uchihaitachilz/Ai-chess-bot`

### Step 2: Configure Frontend

**Basic Settings:**
- **Name:** `tushi-chess-bot-frontend` (or any name)
- **Branch:** `main`
- **Root Directory:** `client`
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `dist`

### Step 3: Add Environment Variables (Frontend)

Click **"Environment"** → **"Add Environment Variable"**:

```
VITE_API_URL=https://tushi-chess-bot-backend.onrender.com
```

**Important:** Replace `tushi-chess-bot-backend.onrender.com` with your actual backend URL from Part 1!

### Step 4: Deploy

1. Click **"Create Static Site"**
2. Wait for deployment (2-5 minutes)
3. Your frontend will be live!

---

## Part 3: CORS Configuration

The backend needs to allow requests from your frontend domain.

### Update Backend CORS

In `server/main.py`, update the CORS origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://tushi-chess-bot-frontend.onrender.com",  # Add your frontend URL
        "https://*.onrender.com",  # Allow all Render subdomains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then commit and push:
```bash
git add server/main.py
git commit -m "Update CORS for Render deployment"
git push origin main
```

---

## Environment Variables Summary

### Backend (Web Service)
```
ENGINE_PATH=/usr/bin/stockfish
ENGINE_DEPTH=12
OPENAI_API_KEY=your_key_here (optional)
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

### Frontend (Static Site)
```
VITE_API_URL=https://your-backend-url.onrender.com
```

---

## Troubleshooting

### Backend Issues

1. **Stockfish not found:**
   - Try `ENGINE_PATH=/usr/games/stockfish`
   - Or use Python stockfish package (see Option C above)

2. **Build fails:**
   - Check build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`

3. **Timeout errors:**
   - Increase timeout in start command: `--timeout 180`
   - Reduce `ENGINE_DEPTH` to 8-10

### Frontend Issues

1. **API calls failing:**
   - Verify `VITE_API_URL` is correct
   - Check browser console for CORS errors
   - Ensure backend CORS includes frontend URL

2. **Build fails:**
   - Check Node version (should be 18+)
   - Clear build cache in Render dashboard

---

## Testing After Deployment

1. **Test Backend:**
   ```
   curl https://your-backend-url.onrender.com/
   ```
   Should return: `{"status":"ok","message":"Chess Bot API is running"}`

2. **Test Frontend:**
   - Open your frontend URL
   - Make a chess move
   - Check if commentary appears

---

## Free Tier Limitations

- **Web Services:** Sleep after 15 minutes of inactivity
- **Static Sites:** Always on (no sleep)
- **First request after sleep:** May take 30-60 seconds to wake up

**Solution:** Use a service like UptimeRobot to ping your backend every 5 minutes to keep it awake.

---

## Next Steps

1. Deploy backend first
2. Get backend URL
3. Deploy frontend with backend URL in `VITE_API_URL`
4. Update backend CORS with frontend URL
5. Test everything!

Good luck! 🚀

