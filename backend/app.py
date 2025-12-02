from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import forecast, ai
from models.schemas import StatusResponse

app = FastAPI(
    title="Care Bears Growth Planner API",
    description="Social media growth forecasting API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(forecast.router)
app.include_router(ai.router)


@app.get("/", response_model=StatusResponse)
async def root():
    """Health check endpoint"""
    return StatusResponse(status="ok", version="1.0.0")


@app.get("/health", response_model=StatusResponse)
async def health():
    """Health check endpoint"""
    return StatusResponse(status="ok", version="1.0.0")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
