from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import TestScenario, TestStep, Project
from backend.schemas.scenario import TestScenarioCreate, TestScenarioResponse
from backend.services.browser import browser_manager
from backend.services.scenario_runner import ScenarioRunner, export_scenario_to_playwright_ts

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])

@router.get("", response_model=List[TestScenarioResponse])
async def list_scenarios(project_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(TestScenario).options(selectinload(TestScenario.steps)).order_by(desc(TestScenario.created_at))
    if project_id:
        query = query.where(TestScenario.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=TestScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    project_id: str,
    payload: TestScenarioCreate,
    db: AsyncSession = Depends(get_db)
):
    scenario = TestScenario(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        tags=payload.tags or []
    )
    db.add(scenario)
    await db.flush()

    for idx, s in enumerate(payload.steps):
        step = TestStep(
            scenario_id=scenario.id,
            order_index=s.order_index or idx,
            action_type=s.action_type,
            target=s.target,
            value=s.value,
            expected_value=s.expected_value,
            is_optional=s.is_optional
        )
        db.add(step)

    await db.commit()

    # Reload with steps
    res = await db.execute(
        select(TestScenario)
        .options(selectinload(TestScenario.steps))
        .where(TestScenario.id == scenario.id)
    )
    return res.scalar_one()

@router.get("/{scenario_id}", response_model=TestScenarioResponse)
async def get_scenario(scenario_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(TestScenario)
        .options(selectinload(TestScenario.steps))
        .where(TestScenario.id == scenario_id)
    )
    scenario = res.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@router.post("/{scenario_id}/execute")
async def execute_scenario(scenario_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(TestScenario)
        .options(selectinload(TestScenario.steps))
        .where(TestScenario.id == scenario_id)
    )
    scenario = res.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    context = await browser_manager.create_context(headless=True)
    page = await context.new_page()
    try:
        runner = ScenarioRunner(page)
        steps_dict = [
            {
                "action_type": s.action_type,
                "target": s.target,
                "value": s.value,
                "expected_value": s.expected_value,
                "is_optional": s.is_optional
            }
            for s in scenario.steps
        ]
        execution_report = await runner.run_scenario(steps_dict)
        return execution_report
    finally:
        await page.close()
        await browser_manager.close_context(context)

@router.get("/{scenario_id}/export-playwright")
async def export_scenario_playwright(scenario_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(TestScenario)
        .options(selectinload(TestScenario.steps))
        .where(TestScenario.id == scenario_id)
    )
    scenario = res.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    steps_dict = [
        {
            "action_type": s.action_type,
            "target": s.target,
            "value": s.value,
            "expected_value": s.expected_value
        }
        for s in scenario.steps
    ]
    code = export_scenario_to_playwright_ts(scenario.name, steps_dict)
    return Response(content=code, media_type="text/plain")
