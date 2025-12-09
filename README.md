# Care Bears Growth Dashboard

Social media growth forecasting dashboard with React frontend and FastAPI backend.

## Architecture

- **Frontend**: React + TypeScript + Vite
- **Backend**: Python FastAPI
- **Styling**: Pulse dashboard-inspired dark theme
- **Deployment**: Railway

## Project Structure

```
/
├── backend/                 # FastAPI backend
│   ├── app.py              # Main FastAPI app
│   ├── routes/             # API routes
│   ├── services/           # Business logic
│   ├── models/             # Pydantic schemas
│   ├── data/               # Historical CSV data
│   └── requirements.txt
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.tsx        # Main app component
│   │   ├── services/      # API client
│   │   ├── components/    # React components
│   │   └── pages/         # Page components
│   ├── package.json
│   └── vite.config.ts
│
└── railway.json           # Railway deployment config
```

## Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on `http://localhost:3000` and proxy API requests to backend on port 8000.

## Deployment on Railway

1. **Connect GitHub repo**: Link https://github.com/br00kd0wnt0n/CBGrowthDash
2. **Create two services**:
   - **Backend**: Root directory `backend/`, start command: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
   - **Frontend**: Root directory `frontend/`, build command: `npm install && npm run build`
3. **Set environment variables**:
   - Backend: `PORT=8000`
   - Frontend: `VITE_API_BASE=https://your-backend.railway.app`

## Environment Configuration

- Backend
  - `APP_ENV`: `production` or `development`. In `production`, debug-only endpoints are disabled.
  - `APP_VERSION`: Optional app version override (defaults to `1.0.1`).
  - `ALLOWED_ORIGINS`: Comma-separated list of allowed origins for CORS. Example: `https://your-frontend.up.railway.app,http://localhost:5173`.
  - `ALLOW_ORIGIN_REGEX`: Optional regex for allowed origins (defaults to Railway `https://*.up.railway.app`).
  - `OPENAI_API_KEY`: Enables AI endpoints with OpenAI; if unset, backend returns fallback recommendations.
  - `DATABASE_URL`: Postgres connection string for user presets. If unset, presets routes are unavailable; use `/api/user-presets/health/db` to check status.
  - `GIT_SHA`: Optional commit SHA to surface via `/version` (Railway also provides `RAILWAY_GIT_COMMIT_SHA`).

- Frontend
  - `VITE_API_BASE`: Base URL for API. In dev, defaults to `http://localhost:8000` if unset; in production you must set this to your backend URL.

Notes
- The backend caches historical CSVs in-memory and refreshes automatically when source files change.
- CORS defaults allow localhost ports for dev and the Railway frontend URL. Override via env for stricter control in production.

## Version Endpoint

- `GET /version` returns `{ version, git_sha, app_env }` to verify live deploys.
- Set `GIT_SHA` (or rely on `RAILWAY_GIT_COMMIT_SHA` if provided by Railway) to display the current commit.

## API Endpoints

- `GET /health` - Health check
- `GET /api/historical` - Get historical data (mentions, sentiment, tags)
- `POST /api/forecast` - Run growth forecast simulation

## Features

- Historical data visualization (mentions, sentiment, engagement)
- Multi-platform growth forecasting (Instagram, TikTok, YouTube, Facebook)
- Content mix optimization
- Strategy presets (Conservative, Balanced, Ambitious)
- Dark theme UI matching Pulse dashboard style
