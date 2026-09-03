import pytest
from httpx import AsyncClient, ASGITransport
from demo_site.server import app as demo_app

@pytest.mark.asyncio
async def test_demo_home_and_defects():
    transport = ASGITransport(app=demo_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Home page
        res = await client.get("/")
        assert res.status_code == 200
        html = res.text
        assert "broken-img-fixture" in html
        assert "missing-alt-fixture" in html
        assert "btn-trigger-console" in html
        assert "btn-delete-account" in html
        assert "overflowing-banner" in html

        # About page
        res = await client.get("/about")
        assert res.status_code == 200
        assert "About WebQA" in res.text

        # Pricing page
        res = await client.get("/pricing")
        assert res.status_code == 200

        # Contact page with form
        res = await client.get("/contact")
        assert res.status_code == 200
        assert "buggy-contact-form" in res.text

        # Broken link 404
        res = await client.get("/broken-page")
        assert res.status_code == 404

        # API 500
        res = await client.get("/api/simulate-500")
        assert res.status_code == 500
        assert "Database connection refused" in res.json()["error"]

        # API contact submit
        res = await client.post("/api/submit-contact", json={"name": "Test", "email": "bad"})
        assert res.status_code == 200
        assert res.json()["status"] == "received"

        # Visual fixture v1 and v2
        res_v1 = await client.get("/visual-fixture?variant=v1")
        assert res_v1.status_code == 200
        assert "Original Baseline Heading" in res_v1.text

        res_v2 = await client.get("/visual-fixture?variant=v2")
        assert res_v2.status_code == 200
        assert "Altered Regression Heading" in res_v2.text
