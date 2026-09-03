from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import Page, PageVisit
from backend.schemas.page import PageResponse, PageVisitResponse

router = APIRouter(prefix="/api/pages", tags=["Pages"])

@router.get("", response_model=List[PageResponse])
async def list_pages(
    project_id: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(Page).order_by(desc(Page.last_tested_at)).limit(limit)
    if project_id:
        query = query.where(Page.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{page_id}", response_model=PageResponse)
async def get_page(page_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@router.get("/{page_id}/visits", response_model=List[PageVisitResponse])
async def get_page_visits(page_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PageVisit)
        .options(
            selectinload(PageVisit.screenshots),
            selectinload(PageVisit.network_requests),
            selectinload(PageVisit.console_messages),
            selectinload(PageVisit.accessibility_findings),
            selectinload(PageVisit.performance_metrics)
        )
        .where(PageVisit.page_id == page_id)
        .order_by(desc(PageVisit.visited_at))
    )
    return result.scalars().all()
