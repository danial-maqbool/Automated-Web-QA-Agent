from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db, AsyncSessionLocal
from backend.models import Project, Environment, QARun
from backend.services.orchestrator import QAOrchestrator
from backend.config import settings

router = APIRouter(prefix="/api/demo", tags=["Demo"])

@router.post("/one-click-demo")
async def trigger_one_click_demo(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Sets up the bundled demo website project and starts an automated QA scan.
    """
    demo_url = f"http://{settings.HOST}:{settings.PORT}/demo/"

    # Check or create demo project
    proj_res = await db.execute(select(Project).where(Project.name == "WebQA Benchmark Demo"))
    project = proj_res.scalar_one_or_none()
    if not project:
        project = Project(
            name="WebQA Benchmark Demo",
            base_url=demo_url,
            description="Bundled reference website containing intentional QA defects for benchmarking.",
            allowed_domains=["localhost", "127.0.0.1"]
        )
        db.add(project)
        await db.flush()

        env = Environment(
            project_id=project.id,
            name="Demo Ground",
            base_url=demo_url,
            is_default=True
        )
        db.add(env)
        await db.commit()
        await db.refresh(project)

    # Create run
    qa_run = QARun(
        project_id=project.id,
        scan_type="QUICK_SCAN",
        status="PENDING",
        trigger="DEMO",
        browser="chromium"
    )
    db.add(qa_run)
    await db.commit()
    await db.refresh(qa_run)

    async def _execute_demo_scan(proj_id: str, r_id: str):
        orchestrator = QAOrchestrator(r_id)
        await orchestrator.execute_scan(proj_id)

    background_tasks.add_task(_execute_demo_scan, project.id, qa_run.id)

    return {
        "message": "One-click demo QA scan initiated",
        "project_id": project.id,
        "run_id": qa_run.id,
        "demo_url": demo_url
    }
