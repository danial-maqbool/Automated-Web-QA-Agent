import pytest
from pathlib import Path
from backend.services.browser import BrowserManager

@pytest.mark.asyncio
async def test_browser_manager_chromium_context(tmp_path):
    mgr = BrowserManager()
    try:
        # Create context
        context = await mgr.create_context(
            browser_name="chromium",
            headless=True,
            viewport_width=1280,
            viewport_height=720,
            enable_tracing=True
        )
        assert context is not None

        # Open page and test basic interaction
        page = await context.new_page()
        await page.set_content("<html><body><h1>WebQA Playwright Test</h1></body></html>")
        
        h1_text = await page.text_content("h1")
        assert h1_text == "WebQA Playwright Test"

        # Test screenshot
        screenshot_path = tmp_path / "test_screenshot.png"
        await page.screenshot(path=str(screenshot_path))
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 0

        # Close page & context with trace
        trace_path = tmp_path / "test_trace.zip"
        await page.close()
        await mgr.close_context(context, trace_save_path=trace_path)
        assert trace_path.exists()
        assert trace_path.stat().st_size > 0

    finally:
        await mgr.shutdown()

@pytest.mark.asyncio
async def test_browser_manager_multi_browser():
    mgr = BrowserManager()
    try:
        # Test Firefox
        ctx_ff = await mgr.create_context(browser_name="firefox", headless=True)
        page_ff = await ctx_ff.new_page()
        await page_ff.set_content("<title>Firefox Test</title>")
        assert await page_ff.title() == "Firefox Test"
        await page_ff.close()
        await mgr.close_context(ctx_ff)

        # Test WebKit
        ctx_wk = await mgr.create_context(browser_name="webkit", headless=True)
        page_wk = await ctx_wk.new_page()
        await page_wk.set_content("<title>WebKit Test</title>")
        assert await page_wk.title() == "WebKit Test"
        await page_wk.close()
        await mgr.close_context(ctx_wk)
    finally:
        await mgr.shutdown()
