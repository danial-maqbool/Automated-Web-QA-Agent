from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import Issue, IssueOccurrence
from backend.schemas.issue import IssueResponse, IssueUpdate, IssueOccurrenceResponse
from backend.services.reporter import format_issue_markdown

router = APIRouter(prefix="/api/issues", tags=["Issues"])

@router.get("", response_model=List[IssueResponse])
async def list_issues(
    project_id: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(Issue).order_by(desc(Issue.last_detected_at)).limit(limit)

    if project_id:
        query = query.where(Issue.project_id == project_id)
    if severity:
        query = query.where(Issue.severity == severity.upper())
    if category:
        query = query.where(Issue.category == category)
    if status:
        query = query.where(Issue.status == status.upper())
    if search:
        query = query.where(Issue.title.ilike(f"%{search}%") | Issue.description.ilike(f"%{search}%"))

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(issue_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.occurrences))
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue

@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(issue_id: str, payload: IssueUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if payload.status:
        issue.status = payload.status.upper()
    if payload.severity:
        issue.severity = payload.severity.upper()
    if payload.notes is not None:
        issue.notes = payload.notes

    await db.commit()
    await db.refresh(issue)
    return issue

@router.get("/{issue_id}/export-markdown")
async def export_issue_markdown(issue_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    md = format_issue_markdown(issue.__dict__)
    return Response(content=md, media_type="text/markdown")
