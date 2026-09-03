import asyncio
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import uvicorn
import httpx
from playwright.async_api import async_playwright

DOCS_SCREENSHOTS = Path("docs/screenshots")
DOCS_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

def start_server():
    config = uvicorn.Config("backend.main:app", host="127.0.0.1", port=8000, log_level="error")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    return server

async def main():
    print("Starting WebQA server...")
    server = start_server()
    await asyncio.sleep(2.0)

    # 1. Trigger One-Click Demo QA scan to populate benchmark findings
    print("Triggering One-Click Demo QA...")
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=60.0) as client:
        demo_res = await client.post("/api/demo/one-click-demo")
        print("Demo response:", demo_res.status_code, demo_res.json())
        run_id = demo_res.json()["run_id"]

        # Wait for run to complete
        for _ in range(30):
            await asyncio.sleep(1.0)
            status_res = await client.get(f"/api/runs/{run_id}")
            st = status_res.json().get("status")
            print(f"Run {run_id} status: {st}")
            if st in ("COMPLETED", "FAILED", "CANCELLED"):
                break

    # 2. Launch browser and capture screenshots
    print("Launching Chromium for portfolio captures...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Capture 1: Dashboard with issues found
        print("Capturing Dashboard...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(DOCS_SCREENSHOTS / "dashboard.png"), full_page=False)
        print("Saved dashboard.png")

        # Capture 2: Issue Detail Modal showing evidence
        print("Capturing Issue Detail View...")
        await page.click("button:has-text('Issues Explorer')")
        await page.wait_for_timeout(600)
        # Click first issue row
        await page.locator("tbody tr").first.click()
        await page.wait_for_timeout(600)
        await page.screenshot(path=str(DOCS_SCREENSHOTS / "issue_detail.png"), full_page=False)
        print("Saved issue_detail.png")

        # Close modal
        await page.locator(".fixed button").first.click()
        await page.wait_for_timeout(500)

        # Capture 3: Discovered Pages View
        print("Capturing Discovered Pages...")
        await page.click("button:has-text('Discovered Pages')")
        await page.wait_for_timeout(600)
        await page.screenshot(path=str(DOCS_SCREENSHOTS / "page_explorer.png"), full_page=False)
        print("Saved page_explorer.png")

        # Capture 4: Visual Regression View
        print("Capturing Visual Regression...")
        await page.click("button:has-text('Visual Regression')")
        await page.wait_for_timeout(600)
        await page.screenshot(path=str(DOCS_SCREENSHOTS / "visual_regression.png"), full_page=False)
        print("Saved visual_regression.png")

        # Capture 5: Executive Report View
        print("Capturing Executive Report...")
        await page.goto(f"http://127.0.0.1:8000/api/reports/{run_id}/html", wait_until="networkidle")
        await page.wait_for_timeout(600)
        await page.screenshot(path=str(DOCS_SCREENSHOTS / "executive_report.png"), full_page=False)
        print("Saved executive_report.png")

        await browser.close()

    print("Portfolio screenshots captured successfully in docs/screenshots/!")

if __name__ == "__main__":
    asyncio.run(main())
