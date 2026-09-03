import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.database import init_db

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_full_api_routers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create project
        p_res = await client.post("/api/projects", json={
            "name": "API Suite Test",
            "base_url": "http://localhost:8000/demo",
            "allowed_domains": ["localhost"]
        })
        assert p_res.status_code == 201
        project = p_res.json()
        project_id = project["id"]

        # 2. Test Runs endpoint
        run_res = await client.post("/api/runs", json={
            "project_id": project_id,
            "scan_type": "QUICK_SCAN"
        })
        assert run_res.status_code == 201
        run = run_res.json()
        run_id = run["id"]

        get_run = await client.get(f"/api/runs/{run_id}")
        assert get_run.status_code == 200

        # Cancel run
        cancel_res = await client.post(f"/api/runs/{run_id}/cancel")
        assert cancel_res.status_code == 200

        # 3. Test Issues listing
        issues_res = await client.get(f"/api/issues?project_id={project_id}")
        assert issues_res.status_code == 200

        # 4. Test Scenarios CRUD
        scen_res = await client.post(f"/api/scenarios?project_id={project_id}", json={
            "name": "Smoke Login",
            "steps": [
                {"action_type": "navigate", "target": "http://test/login"},
                {"action_type": "fill", "target": "#user", "value": "testuser"},
                {"action_type": "assert_text", "expected_value": "testuser"}
            ]
        })
        assert scen_res.status_code == 201
        scenario = scen_res.json()
        scen_id = scenario["id"]

        export_res = await client.get(f"/api/scenarios/{scen_id}/export-playwright")
        assert export_res.status_code == 200
        assert "Smoke Login" in export_res.text

        # 5. Test Baselines endpoint
        base_res = await client.post(
            f"/api/baselines?project_id={project_id}&page_url=http://test/&screenshot_path=screenshots/test.png"
        )
        assert base_res.status_code == 201
        baseline = base_res.json()

        list_bases = await client.get(f"/api/baselines?project_id={project_id}")
        assert list_bases.status_code == 200
        assert len(list_bases.json()) >= 1

        # 6. Test Reports endpoints
        json_rep = await client.get(f"/api/reports/{run_id}/json")
        assert json_rep.status_code == 200

        html_rep = await client.get(f"/api/reports/{run_id}/html")
        assert html_rep.status_code == 200
        assert "WebQA Audit Report" in html_rep.text

        csv_rep = await client.get(f"/api/reports/{run_id}/csv")
        assert csv_rep.status_code == 200

        # 7. Test One-Click Demo
        demo_trigger = await client.post("/api/demo/one-click-demo")
        assert demo_trigger.status_code == 200
        assert "run_id" in demo_trigger.json()
