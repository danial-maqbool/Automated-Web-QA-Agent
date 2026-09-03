from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.database import get_db
from backend.models import Baseline, VisualComparison, Page
from backend.schemas.baseline import BaselineResponse, VisualComparisonResponse
from backend.services.visual_regression import compare_screenshots
from backend.config import DATA_DIR

router = APIRouter(prefix="/api/baselines", tags=["Baselines"])

@router.get("", response_model=List[BaselineResponse])
async def list_baselines(project_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Baseline).order_by(desc(Baseline.created_at))
    if project_id:
        query = query.where(Baseline.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=BaselineResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_baseline(
    project_id: str,
    page_url: str,
    screenshot_path: str,
    viewport: str = "1920x1080",
    browser: str = "chromium",
    db: AsyncSession = Depends(get_db)
):
    # Check existing baseline
    res = await db.execute(
        select(Baseline).where(
            Baseline.project_id == project_id,
            Baseline.page_url == page_url,
            Baseline.viewport == viewport,
            Baseline.browser == browser
        )
    )
    existing = res.scalar_one_or_none()
    if existing:
        existing.screenshot_path = screenshot_path
        existing.is_active = True
        await db.commit()
        await db.refresh(existing)
        return existing

    baseline = Baseline(
        project_id=project_id,
        page_url=page_url,
        screenshot_path=screenshot_path,
        viewport=viewport,
        browser=browser
    )
    db.add(baseline)
    await db.commit()
    await db.refresh(baseline)
    return baseline

@router.delete("/{baseline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_baseline(baseline_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Baseline).where(Baseline.id == baseline_id))
    b = res.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Baseline not found")
    await db.delete(b)
    await db.commit()
    return None

@router.post("/compare")
async def compare_visual(
    baseline_id: str,
    current_screenshot_path: str,
    run_id: str,
    threshold_pct: float = 0.5,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Baseline).where(Baseline.id == baseline_id))
    baseline = res.scalar_one_or_none()
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    base_abs = DATA_DIR / baseline.screenshot_path
    curr_abs = DATA_DIR / current_screenshot_path
    diff_filename = f"diff_{baseline_id[:8]}_{Path(current_screenshot_path).name}"
    diff_rel = f"screenshots/{run_id}/{diff_filename}"
    diff_abs = DATA_DIR / diff_rel

    passed, count, pct = compare_screenshots(
        baseline_path=base_abs,
        current_path=curr_abs,
        diff_output_path=diff_abs,
        pixel_threshold_pct=threshold_pct
    )

    comp = VisualComparison(
        run_id=run_id,
        baseline_id=baseline.id,
        page_url=baseline.page_url,
        current_screenshot_path=current_screenshot_path,
        diff_screenshot_path=diff_rel,
        diff_pixel_count=count,
        diff_percentage=pct,
        passed=passed
    )
    db.add(comp)
    await db.commit()

    return {
        "passed": passed,
        "diff_pixel_count": count,
        "diff_percentage": pct,
        "baseline_screenshot": baseline.screenshot_path,
        "current_screenshot": current_screenshot_path,
        "diff_screenshot": diff_rel
    }
