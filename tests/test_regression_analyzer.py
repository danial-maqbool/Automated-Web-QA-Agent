import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.models import Base, Project, QARun, Issue, IssueOccurrence
from backend.services.regression_analyzer import RegressionAnalyzer

@pytest.mark.asyncio
async def test_regression_classification(tmp_path):
    db_path = tmp_path / "test_reg.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Create Project
        proj = Project(name="Regression Test Project", base_url="http://test.com")
        session.add(proj)
        await session.flush()

        # Run 1 (Baseline)
        run1 = QARun(project_id=proj.id, status="COMPLETED")
        session.add(run1)
        await session.flush()

        # Run 2 (Current)
        run2 = QARun(project_id=proj.id, status="RUNNING")
        session.add(run2)
        await session.flush()

        # Issues:
        # Issue A: only in Run 1 -> should be RESOLVED in Run 2
        issue_a = Issue(project_id=proj.id, fingerprint="fp_a", title="Issue A", category="Functional", severity="HIGH", description="A", page_url="http://test.com")
        session.add(issue_a)
        await session.flush()
        session.add(IssueOccurrence(issue_id=issue_a.id, run_id=run1.id, page_url="http://test.com"))

        # Issue B: in both Run 1 and Run 2 -> EXISTING
        issue_b = Issue(project_id=proj.id, fingerprint="fp_b", title="Issue B", category="Functional", severity="HIGH", description="B", page_url="http://test.com")
        session.add(issue_b)
        await session.flush()
        session.add(IssueOccurrence(issue_id=issue_b.id, run_id=run1.id, page_url="http://test.com"))
        session.add(IssueOccurrence(issue_id=issue_b.id, run_id=run2.id, page_url="http://test.com"))

        # Issue C: only in Run 2 -> NEW
        issue_c = Issue(project_id=proj.id, fingerprint="fp_c", title="Issue C", category="Functional", severity="HIGH", description="C", page_url="http://test.com")
        session.add(issue_c)
        await session.flush()
        session.add(IssueOccurrence(issue_id=issue_c.id, run_id=run2.id, page_url="http://test.com"))

        # Issue D: in Run 2, but was status REGRESSION -> REGRESSION
        issue_d = Issue(project_id=proj.id, fingerprint="fp_d", title="Issue D", category="Functional", severity="HIGH", description="D", page_url="http://test.com", status="REGRESSION")
        session.add(issue_d)
        await session.flush()
        session.add(IssueOccurrence(issue_id=issue_d.id, run_id=run2.id, page_url="http://test.com"))

        await session.commit()

        # Analyze
        result = await RegressionAnalyzer.analyze_run_regression(session, proj.id, run2.id, run1.id)
        counts = result["counts"]

        assert counts["resolved"] == 1
        assert counts["existing"] == 1
        assert counts["new"] == 1
        assert counts["regression"] == 1

        assert "Issue A" in result["resolved_issues"]
        assert "Issue B" in result["existing_issues"]
        assert "Issue C" in result["new_issues"]
        assert "Issue D" in result["regression_issues"]

    await engine.dispose()
