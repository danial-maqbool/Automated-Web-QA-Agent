import pytest
from pathlib import Path
from backend.services.evidence import EvidenceCollector
from backend.services.browser import BrowserManager
from backend.config import DATA_DIR

@pytest.mark.asyncio
async def test_evidence_collector_screenshots():
    mgr = BrowserManager()
    run_id = "test_run_evidence_123"
    collector = EvidenceCollector(run_id)

    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()

        await page.set_content("""
            <!DOCTYPE html>
            <html>
                <body style="min-height: 1500px; background: #fafafa;">
                    <div id="target-defect-card" style="margin: 50px; padding: 20px; background: white; border: 1px solid #ccc;">
                        <h2>Target Defect Card</h2>
                        <p>This element has a defect that needs screenshot highlighting.</p>
                    </div>
                </body>
            </html>
        """)

        # 1. Viewport screenshot
        vp_path = await collector.capture_viewport_screenshot(page, "vp_test")
        assert vp_path.startswith(f"screenshots/{run_id}/")
        assert (DATA_DIR / vp_path).exists()
        assert (DATA_DIR / vp_path).stat().st_size > 0

        # 2. Fullpage screenshot
        fp_path = await collector.capture_fullpage_screenshot(page, "fp_test")
        assert fp_path.startswith(f"screenshots/{run_id}/")
        assert (DATA_DIR / fp_path).exists()
        assert (DATA_DIR / fp_path).stat().st_size > 0

        # 3. Element highlighted screenshot
        el_path = await collector.capture_element_screenshot(page, "#target-defect-card", "el_test", highlight=True)
        assert el_path.startswith(f"screenshots/{run_id}/")
        assert (DATA_DIR / el_path).exists()
        assert (DATA_DIR / el_path).stat().st_size > 0

        # 4. Trace path
        trace_p = collector.get_trace_path()
        assert trace_p.name == f"{run_id}.zip"

        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()
        # Clean up test artifacts
        import shutil
        run_folder = DATA_DIR / "screenshots" / run_id
        if run_folder.exists():
            shutil.rmtree(run_folder, ignore_errors=True)
