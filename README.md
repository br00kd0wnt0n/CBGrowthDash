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
