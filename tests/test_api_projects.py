import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.database import init_db

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "version" in data

@pytest.mark.asyncio
async def test_project_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        create_payload = {
            "name": "Integration Test Site",
            "base_url": "http://localhost:3000",
            "allowed_domains": ["localhost"]
        }
        res = await client.post("/api/projects", json=create_payload)
        assert res.status_code == 201
        project = res.json()
        project_id = project["id"]
        assert project["name"] == "Integration Test Site"
        assert len(project["environments"]) >= 1

        # List
        res = await client.get("/api/projects")
        assert res.status_code == 200
        projects = res.json()
        assert any(p["id"] == project_id for p in projects)

        # Get
        res = await client.get(f"/api/projects/{project_id}")
        assert res.status_code == 200
        assert res.json()["id"] == project_id

        # Delete
        res = await client.delete(f"/api/projects/{project_id}")
        assert res.status_code == 204
