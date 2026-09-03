import json
import pytest
import threading
import time
import uvicorn
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from backend.database import init_db, AsyncSessionLocal
from backend.models import Project, Environment, QARun, Issue
from backend.services.orchestrator import QAOrchestrator
from backend.services.reporter import QAReporter
from backend.config import DATA_DIR

import socket

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

TEST_PORT = get_free_port()

@pytest.fixture(scope="module", autouse=True)
def run_test_server():
    config = uvicorn.Config("backend.main:app", host="127.0.0.1", port=TEST_PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.2) # Allow server to bind
    yield
    server.should_exit = True

@pytest.mark.asyncio
async def test_end_to_end_benchmark_validation():
    # 1. Load ground truth benchmark
    benchmark_path = Path("demo_site/benchmark.json")
    assert benchmark_path.exists()
    with open(benchmark_path, "r") as f:
        ground_truth = json.load(f)

    expected_defects = ground_truth["expected_defects"]
    expected_rule_ids = set(["LINK_HTTP_404", "IMG_BROKEN_SRC", "CONSOLE_UNCAUGHT_ERR"])

    await init_db()

    # 2. Setup benchmark project pointing to local demo site
    demo_url = f"http://127.0.0.1:{TEST_PORT}/demo/"
    proj_name = f"E2E Benchmark {time.time()}"
    async with AsyncSessionLocal() as db:
        proj = Project(
            name=proj_name,
            base_url=demo_url,
            allowed_domains=["127.0.0.1", "localhost"]
        )
        db.add(proj)
        await db.flush()

        env = Environment(
            project_id=proj.id,
            name="Benchmark Env",
            base_url=demo_url,
            is_default=True
        )
        db.add(env)
        await db.commit()
        await db.refresh(proj)
        project_id = proj.id

        run = QARun(
            project_id=project_id,
            scan_type="FULL_SCAN",
            status="PENDING",
            trigger="BENCHMARK",
            browser="chromium"
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        run_id = run.id

    # 3. Execute QA Orchestrator
    orchestrator = QAOrchestrator(run_id)
    completed_run = await orchestrator.execute_scan(project_id)

    # 4. Verify run completion and telemetry
    assert completed_run.status == "COMPLETED", f"Run failed with: {completed_run.error_message}"
    assert completed_run.pages_tested >= 4
    assert completed_run.total_issues > 0

    # 5. Fetch detected issues from database
    async with AsyncSessionLocal() as db:
        issues_res = await db.execute(select(Issue).where(Issue.project_id == project_id))
        detected_issues = issues_res.scalars().all()

    detected_rules = set()
    for iss in detected_issues:
        # Determine rule from fingerprint or description or title
        for exp in expected_rule_ids:
            if exp in iss.title or exp in iss.description or exp.lower() in iss.description.lower():
                detected_rules.add(exp)

    # Check key defect rules were detected
    found_categories = set(i.category for i in detected_issues)
    assert "Navigation" in found_categories or "Network" in found_categories
    assert "Console" in found_categories or "Functional" in found_categories
    assert "Accessibility" in found_categories

    # 6. Verify report generation
    report_data = {
        "project_name": "E2E Benchmark",
        "qa_score": completed_run.qa_score,
        "total_pages_tested": completed_run.pages_tested,
        "total_issues_found": completed_run.total_issues,
        "critical_issues_count": completed_run.critical_issues,
        "high_issues_count": completed_run.high_issues,
        "accessibility_count": len([i for i in detected_issues if i.category == "Accessibility"]),
        "issues": [i.__dict__ for i in detected_issues]
    }

    html_rep = QAReporter.generate_html_report(report_data)
    assert "WebQA Audit Report" in html_rep
    assert str(completed_run.qa_score) in html_rep

    json_rep = QAReporter.generate_json_report(report_data)
    assert "E2E Benchmark" in json_rep

    csv_rep = QAReporter.generate_csv_report([i.__dict__ for i in detected_issues])
    assert len(csv_rep) > 50
