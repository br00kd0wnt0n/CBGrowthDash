import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import forecast, ai, research, presets
from models.schemas import StatusResponse, VersionResponse
from database import init_db, engine

# Centralized app version
APP_VERSION = os.getenv("APP_VERSION", "1.0.1")

app = FastAPI(
    title="Care Bears Growth Planner API",
    description="Social media growth forecasting API",
    version=APP_VERSION
)

# Configurable CORS via environment
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
allow_origin_regex_env = os.getenv("ALLOW_ORIGIN_REGEX", "").strip()

# Defaults: dev localhost + Railway frontend if not provided
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
prod_default = "https://cbdash-frontend-production.up.railway.app"
if prod_default not in default_origins:
    default_origins.append(prod_default)

allow_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()] or default_origins
allow_origin_regex = allow_origin_regex_env or r"https://.*\.up\.railway\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
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
    return StatusResponse(status="ok", version=APP_VERSION)


@app.get("/health", response_model=StatusResponse)
async def health():
    """Health check endpoint"""
    return StatusResponse(status="ok", version=APP_VERSION)


@app.get("/version", response_model=VersionResponse)
async def version():
    """Return version info and commit SHA for deploy verification"""
    git_sha = os.getenv("GIT_SHA") or os.getenv("RAILWAY_GIT_COMMIT_SHA")
    app_env = os.getenv("APP_ENV", "development")
    return VersionResponse(version=APP_VERSION, git_sha=git_sha, app_env=app_env)


# Gate debug-only routes by environment
APP_ENV = os.getenv("APP_ENV", "development").lower()
if APP_ENV != "production":
    @app.get("/api/debug/openai-status")
    async def openai_status():
        """Debug endpoint to check OpenAI client status (dev only)"""
        api_key = os.getenv("OPENAI_API_KEY")
        key_present = api_key is not None and len(api_key) > 10
        key_prefix = api_key[:10] + "..." if key_present else None

        client = None
        init_error = None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key) if api_key else None
            if client:
                # Light-touch call; list models to validate auth
                _ = client.models.list()
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
