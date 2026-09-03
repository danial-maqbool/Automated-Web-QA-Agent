import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db, AsyncSessionLocal
from backend.models import QARun, RunEvent, Project
from backend.schemas.run import RunCreate, QARunResponse, RunEventResponse
from backend.services.orchestrator import QAOrchestrator

router = APIRouter(prefix="/api/runs", tags=["Runs"])

active_orchestrators: dict = {}

async def run_scan_background(project_id: str, run_id: str):
    orchestrator = QAOrchestrator(run_id)
    active_orchestrators[run_id] = orchestrator
    try:
        await orchestrator.execute_scan(project_id)
    finally:
        active_orchestrators.pop(run_id, None)

@router.get("", response_model=List[QARunResponse])
async def list_runs(
    project_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    query = select(QARun).order_by(desc(QARun.created_at)).limit(limit)
    if project_id:
        query = query.where(QARun.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=QARunResponse, status_code=status.HTTP_201_CREATED)
async def create_and_start_run(
    payload: RunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Verify project exists
    proj_res = await db.execute(select(Project).where(Project.id == payload.project_id))
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    qa_run = QARun(
        project_id=payload.project_id,
        environment_id=payload.environment_id,
        scan_type=payload.scan_type,
        status="PENDING",
        trigger=payload.trigger,
        browser=payload.browser,
        viewport_width=payload.viewport_width,
        viewport_height=payload.viewport_height
    )
    db.add(qa_run)
    await db.commit()
    await db.refresh(qa_run)

    # Launch background scan
    background_tasks.add_task(run_scan_background, payload.project_id, qa_run.id)

    return qa_run

@router.get("/{run_id}", response_model=QARunResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QARun).where(QARun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.post("/{run_id}/cancel")
async def cancel_run(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QARun).where(QARun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run.status = "CANCELLED"
    await db.commit()

    if run_id in active_orchestrators:
        active_orchestrators[run_id].cancelled = True

    return {"status": "cancelled", "run_id": run_id}

@router.get("/{run_id}/events", response_model=List[RunEventResponse])
async def get_run_events(run_id: str, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RunEvent)
        .where(RunEvent.run_id == run_id)
        .order_by(RunEvent.timestamp.asc())
        .limit(limit)
    )
    return result.scalars().all()
