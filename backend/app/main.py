import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(
    title="WebSense Semantic Risk Analysis API",
    description="Autonomous real-time legal risk analysis engine for WebSense Chrome Extension",
    version="1.0.0"
)

# Environment configuration
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

# Enable CORS for browser extension and local demo pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": "WebSense API Engine",
        "status": "online",
        "environment": ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=(ENVIRONMENT == "development"))
