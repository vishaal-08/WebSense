import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(
    title="WebSense Semantic Risk Analysis API",
    description="Autonomous real-time legal risk analysis engine for WebSense Chrome Extension",
    version="1.0.0"
)

# Enable CORS for browser extension and local demo pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits Chrome extension chrome-extension:// origins & localhost
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
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
