# Railway Frontend Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- Railway CLI installed (`npm i -g @railway/cli`)
- Backend service already deployed at: https://cbgrowthdash-production.up.railway.app

## Deployment Steps

### Option 1: Via Railway Dashboard (Recommended)

1. **Create New Service**
   - Go to your Railway project dashboard
   - Click "+ New Service"
   - Select "GitHub Repo"
   - Choose the `CBGrowthDash` repository
   - Railway will auto-detect it as a monorepo

2. **Configure Service Settings**
   - Service Name: `frontend` (or `carebears-frontend`)
   - Root Directory: `/frontend`
   - Build Command: `npm run build` (auto-detected)
   - Start Command: `npx serve -s dist -l $PORT` (from nixpacks.toml)

3. **Set Environment Variables**
   - Go to service "Variables" tab
   - Add: `VITE_API_BASE` = `https://cbgrowthdash-production.up.railway.app`
   - This tells the frontend where the backend API is located

4. **Deploy**
   - Click "Deploy" or push to GitHub main branch
   - Railway will automatically build and deploy
   - Get your frontend URL from the "Settings" → "Domains" section

### Option 2: Via Railway CLI

```bash
# Navigate to frontend directory
cd frontend

# Login to Railway
railway login

# Link to your existing project
railway link

# Create a new service
railway service create frontend

# Set environment variable
railway variables set VITE_API_BASE=https://cbgrowthdash-production.up.railway.app

# Deploy
railway up
```

## Post-Deployment

### Update Backend CORS

Once you get your frontend URL (e.g., `https://carebears-frontend-production.up.railway.app`), update the backend CORS settings:

1. Go to backend service on Railway
2. Add environment variable:
   - `FRONTEND_URL` = `https://your-frontend-url.up.railway.app`

3. Update `backend/app.py` CORS middleware:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Verify Deployment

1. Visit your frontend URL
2. Check that the API status badge shows "Connected"
3. Navigate to "Historical Data" tab - should load charts
4. Try running a forecast from the "Forecast" tab

## Troubleshooting

### Build Fails
- Check that `serve` package is in package.json dependencies
- Verify nixpacks.toml is in the frontend directory
- Check Railway build logs for specific errors

### API Connection Issues
- Verify `VITE_API_BASE` environment variable is set correctly
- Check browser console for CORS errors
- Ensure backend CORS allows your frontend domain

### 404 Errors on Page Refresh
- `serve -s` should handle SPA routing automatically
- If issues persist, add a `vercel.json` or `_redirects` file

## Architecture

```
Railway Project: CBGrowthDash
├── Service 1: backend (Python/FastAPI)
│   ├── URL: https://cbgrowthdash-production.up.railway.app
│   └── Root: /backend
└── Service 2: frontend (React/Vite)
    ├── URL: https://[your-frontend-url].up.railway.app
    └── Root: /frontend
```
