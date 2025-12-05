# Railway Deployment — Streamlit Service

This repository already has `frontend/` (React) and `backend/` (FastAPI) services. The Streamlit dashboard lives in `CareBearsdashboard/` and should be deployed as a separate Railway service.

## Service config
- Root Directory: `CareBearsdashboard`
- Build: Nixpacks (auto)
- Install: `pip install -r requirements.txt`
- Start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

A `Procfile` is included so Railway can auto-detect the command.

## Steps
1. Railway → New Service → From GitHub → select `CBGrowthDash` repo
2. In service settings, set Root Directory to `CareBearsdashboard`
3. Deploy
4. Open the service URL; the dashboard loads with AI Insights auto-generated

## Notes
- This Streamlit service is independent from the existing `frontend/` React app.
- If you want a link between them, add a button in the React app that opens the Streamlit service URL in a new tab.
