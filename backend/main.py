import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings, DATA_DIR
from backend.database import init_db
from backend.routers import projects

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    await init_db()
    yield

app = FastAPI(
    title="WebQA Agent API",
    description="Automated Website Quality-Assurance Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount artifact files (screenshots, traces, reports, baselines)
app.mount("/artifacts", StaticFiles(directory=str(DATA_DIR)), name="artifacts")

# Register API routers
app.include_router(projects.router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "playwright_browser": settings.PLAYWRIGHT_BROWSER,
        "ai_enabled": settings.AI_ENABLED,
        "data_directory": str(DATA_DIR)
    }

# Frontend static serving if built
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
