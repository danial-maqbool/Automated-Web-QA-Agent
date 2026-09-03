import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.models import (
    Base, Project, Environment, QARun, Page, Issue, IssueOccurrence, 
    Screenshot, NetworkRequest, ConsoleMessage, AccessibilityFinding, 
    PerformanceMetric, TestScenario, TestStep, TestSuite, SuiteMember, 
    Baseline, VisualComparison, IgnoreRule, RunEvent, BrowserSession
)

@pytest.mark.asyncio
async def test_database_schema_creation(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # Create Project and Environment
        project = Project(
            name="Demo Project",
            base_url="http://localhost:3000",
            allowed_domains=["localhost"]
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        
        env = Environment(
            project_id=project.id,
            name="Development",
            base_url="http://localhost:3000",
            is_default=True
        )
        session.add(env)
        
        # Create QARun
        run = QARun(
            project_id=project.id,
            environment_id=env.id,
            scan_type="QUICK_SCAN",
            status="COMPLETED",
            qa_score=95.0
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)
        
        # Create Page and Issue
        page = Page(
            project_id=project.id,
            url="http://localhost:3000/",
            path="/"
        )
        session.add(page)
        
        issue = Issue(
            project_id=project.id,
            fingerprint="test_fingerprint_123",
            title="Broken link test",
            category="Navigation",
            severity="HIGH",
            description="404 on /pricing",
            page_url="http://localhost:3000/"
        )
        session.add(issue)
        await session.commit()
        
        assert project.id is not None
        assert run.id is not None
        assert issue.id is not None
        
    await engine.dispose()
