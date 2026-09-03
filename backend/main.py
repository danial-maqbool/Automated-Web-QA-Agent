import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings, DATA_DIR
from backend.database import init_db
from backend.routers import projects, runs, issues, pages, scenarios, baselines, reports, demo
from demo_site.server import app as demo_app

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

# Mount demo site internally for convenient single-server testing
app.mount("/demo", demo_app)

# Register API routers
app.include_router(projects.router)
app.include_router(runs.router)
app.include_router(issues.router)
app.include_router(pages.router)
app.include_router(scenarios.router)
app.include_router(baselines.router)
app.include_router(reports.router)
app.include_router(demo.router)

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
