from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import QARun, Project, Issue, IssueOccurrence
from backend.services.reporter import QAReporter

router = APIRouter(prefix="/api/reports", tags=["Reports"])

async def _build_report_dict(run_id: str, db: AsyncSession) -> Dict[str, Any]:
    run_res = await db.execute(select(QARun).where(QARun.id == run_id))
    run = run_res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    proj_res = await db.execute(select(Project).where(Project.id == run.project_id))
    project = proj_res.scalar_one()

    # Get occurrences and issues
    occ_res = await db.execute(
        select(IssueOccurrence, Issue)
        .join(Issue, IssueOccurrence.issue_id == Issue.id)
        .where(IssueOccurrence.run_id == run_id)
    )
    rows = occ_res.all()
    issues_list = []
    seen = set()
    for row in rows:
        if row.Issue.id not in seen:
            seen.add(row.Issue.id)
            issues_list.append({
                "id": row.Issue.id,
                "title": row.Issue.title,
                "category": row.Issue.category,
                "severity": row.Issue.severity,
                "confidence": row.Issue.confidence,
                "status": row.Issue.status,
                "page_url": row.Issue.page_url,
                "selector": row.Issue.selector,
                "description": row.Issue.description,
                "occurrence_count": row.Issue.occurrence_count,
                "reproduction_steps": row.Issue.reproduction_steps,
                "screenshot_path": row.Issue.screenshot_path
            })

    return {
        "run_id": run.id,
        "project_name": project.name,
        "base_url": project.base_url,
        "scan_type": run.scan_type,
        "status": run.status,
        "qa_score": run.qa_score,
        "total_pages_tested": run.pages_tested,
        "total_issues_found": len(issues_list),
        "critical_issues_count": run.critical_issues,
        "high_issues_count": run.high_issues,
        "accessibility_count": len([i for i in issues_list if i["category"] == "Accessibility"]),
        "issues": issues_list,
        "recommendations": [
            "Remediate all CRITICAL and HIGH severity issues before production deployment.",
            "Review accessibility findings to ensure WCAG 2.1 AA compliance.",
            "Establish baseline screenshots for high-priority pages to prevent visual regressions."
        ]
    }

@router.get("/{run_id}/html")
async def get_html_report(run_id: str, db: AsyncSession = Depends(get_db)):
    data = await _build_report_dict(run_id, db)
    html = QAReporter.generate_html_report(data)
    return Response(content=html, media_type="text/html")

@router.get("/{run_id}/json")
async def get_json_report(run_id: str, db: AsyncSession = Depends(get_db)):
    data = await _build_report_dict(run_id, db)
    return data

@router.get("/{run_id}/csv")
async def get_csv_report(run_id: str, db: AsyncSession = Depends(get_db)):
    data = await _build_report_dict(run_id, db)
    csv_text = QAReporter.generate_csv_report(data["issues"])
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=webqa_report_{run_id[:8]}.csv"}
    )
