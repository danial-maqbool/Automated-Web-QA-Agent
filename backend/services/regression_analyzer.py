from typing import Dict, Any, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.models import QARun, Issue, IssueOccurrence

class RegressionAnalyzer:
    """
    Compares test runs against established baselines to classify defects as
    NEW, EXISTING, RESOLVED, or REGRESSION.
    """
    @staticmethod
    async def analyze_run_regression(
        db: AsyncSession,
        project_id: str,
        current_run_id: str,
        baseline_run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Fetch current run occurrences
        curr_occ_res = await db.execute(
            select(IssueOccurrence, Issue)
            .join(Issue, IssueOccurrence.issue_id == Issue.id)
            .where(IssueOccurrence.run_id == current_run_id)
        )
        curr_rows = curr_occ_res.all()
        curr_issues_by_fp = {row.Issue.fingerprint: row.Issue for row in curr_rows}
        curr_fps = set(curr_issues_by_fp.keys())

        # 2. Determine baseline run
        if not baseline_run_id:
            # Find the most recent previous completed run
            prev_run_res = await db.execute(
                select(QARun)
                .where(
                    and_(
                        QARun.project_id == project_id,
                        QARun.id != current_run_id,
                        QARun.status == "COMPLETED"
                    )
                )
                .order_by(QARun.completed_at.desc(), QARun.created_at.desc())
            )
            baseline_run = prev_run_res.scalars().first()
            baseline_run_id = baseline_run.id if baseline_run else None

        base_issues_by_fp = {}
        base_fps = set()

        if baseline_run_id:
            base_occ_res = await db.execute(
                select(IssueOccurrence, Issue)
                .join(Issue, IssueOccurrence.issue_id == Issue.id)
                .where(IssueOccurrence.run_id == baseline_run_id)
            )
            base_rows = base_occ_res.all()
            base_issues_by_fp = {row.Issue.fingerprint: row.Issue for row in base_rows}
            base_fps = set(base_issues_by_fp.keys())

        # 3. Categorize
        existing_fps = curr_fps & base_fps
        resolved_fps = base_fps - curr_fps
        remaining_curr_fps = curr_fps - base_fps

        new_fps = set()
        regression_fps = set()

        for fp in remaining_curr_fps:
            issue = curr_issues_by_fp[fp]
            if issue.status == "REGRESSION" or issue.occurrence_count > 1:
                regression_fps.add(fp)
            else:
                new_fps.add(fp)

        # 4. Update current run model
        curr_run_res = await db.execute(select(QARun).where(QARun.id == current_run_id))
        curr_run = curr_run_res.scalar_one_or_none()
        if curr_run:
            curr_run.new_issues_count = len(new_fps)
            curr_run.existing_issues_count = len(existing_fps)
            curr_run.resolved_issues_count = len(resolved_fps)
            curr_run.regression_issues_count = len(regression_fps)
            await db.flush()

        return {
            "baseline_run_id": baseline_run_id,
            "counts": {
                "new": len(new_fps),
                "existing": len(existing_fps),
                "resolved": len(resolved_fps),
                "regression": len(regression_fps)
            },
            "new_issues": [curr_issues_by_fp[fp].title for fp in new_fps],
            "existing_issues": [curr_issues_by_fp[fp].title for fp in existing_fps],
            "resolved_issues": [base_issues_by_fp[fp].title for fp in resolved_fps],
            "regression_issues": [curr_issues_by_fp[fp].title for fp in regression_fps]
        }
