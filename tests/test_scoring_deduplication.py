import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.models import Base, Project, QARun, Issue, IssueOccurrence
from backend.services.scoring_deduplication import (
    calculate_qa_score, generate_issue_fingerprint,
    normalize_text_for_fingerprint, IssueManager
)

def test_calculate_qa_score_formula():
    assert calculate_qa_score(critical=0, high=0, medium=0, low=0) == 100.0
    assert calculate_qa_score(critical=1, high=0, medium=0, low=0) == 75.0
    assert calculate_qa_score(critical=0, high=2, medium=1, low=2) == 74.0 # 100 - (20 + 4 + 2) = 74.0
    assert calculate_qa_score(critical=10, high=10, medium=10, low=10) == 0.0 # Bounded at 0

def test_issue_fingerprint_normalization():
    # Errors with ephemeral memory addresses or line numbers generate the same fingerprint
    err1 = "Uncaught TypeError: Cannot read properties of undefined at app.js:105:22"
    err2 = "Uncaught TypeError: Cannot read properties of undefined at app.js:240:15"
    
    fp1 = generate_issue_fingerprint("Console", "CONSOLE_UNCAUGHT_ERR", err1)
    fp2 = generate_issue_fingerprint("Console", "CONSOLE_UNCAUGHT_ERR", err2)
    assert fp1 == fp2

@pytest.mark.asyncio
async def test_issue_deduplication_and_regression(tmp_path):
    db_path = tmp_path / "test_dedup.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Create Project and Run
        proj = Project(name="Dedup Test", base_url="http://test.com")
        session.add(proj)
        await session.flush()

        run = QARun(project_id=proj.id)
        session.add(run)
        await session.commit()

        finding1 = {
            "category": "Navigation",
            "rule_id": "LINK_HTTP_404",
            "title": "Broken Link 404",
            "page_url": "http://test.com/page1",
            "target_url": "http://test.com/missing",
            "severity": "HIGH",
            "confidence": 1.0,
            "description": "404 on /missing"
        }

        # First occurrence on /page1
        issue1, is_new1 = await IssueManager.record_finding(session, proj.id, run.id, finding1)
        await session.commit()
        assert is_new1 is True
        assert issue1.occurrence_count == 1
        assert issue1.affected_pages_count == 1

        # Second occurrence of identical defect on /page2
        finding2 = dict(finding1)
        finding2["page_url"] = "http://test.com/page2"
        issue2, is_new2 = await IssueManager.record_finding(session, proj.id, run.id, finding2)
        await session.commit()
        assert is_new2 is False # Deduplicated!
        assert issue2.id == issue1.id
        assert issue2.occurrence_count == 2
        assert issue2.affected_pages_count == 2
        assert "http://test.com/page2" in issue2.affected_pages

        # Test Regression status change: mark FIXED, then record again
        issue2.status = "FIXED"
        await session.commit()

        finding3 = dict(finding1)
        finding3["page_url"] = "http://test.com/page3"
        issue3, is_new3 = await IssueManager.record_finding(session, proj.id, run.id, finding3)
        await session.commit()
        assert issue3.status == "REGRESSION"

    await engine.dispose()
