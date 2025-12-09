from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import forecast, ai, research, presets
from models.schemas import StatusResponse
from database import init_db, engine

app = FastAPI(
    title="Care Bears Growth Planner API",
    description="Social media growth forecasting API",
    version="1.0.0"
)

# CORS middleware - allow Railway subdomains and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cbdash-frontend-production.up.railway.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\.up\.railway\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(forecast.router)
app.include_router(ai.router)
app.include_router(research.router)
app.include_router(presets.router)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    if engine is not None:
        init_db()


@app.get("/", response_model=StatusResponse)
async def root():
    """Health check endpoint"""
    return StatusResponse(status="ok", version="1.0.0")


@app.get("/health", response_model=StatusResponse)
async def health():
    """Health check endpoint"""
    return StatusResponse(status="ok", version="1.0.0")


@app.get("/api/debug/openai-status")
async def openai_status():
    """Debug endpoint to check OpenAI client status"""
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    key_present = api_key is not None and len(api_key) > 10
    key_prefix = api_key[:10] + "..." if key_present else None

    # Try to initialize client and capture any error
    client = None
    init_error = None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key) if api_key else None
        # Test it works
        if client:
            models = client.models.list()
            init_error = None
    except Exception as e:
        init_error = str(e)

    return {
        "key_present": key_present,
        "key_prefix": key_prefix,
        "client_initialized": client is not None,
        "init_error": init_error
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
