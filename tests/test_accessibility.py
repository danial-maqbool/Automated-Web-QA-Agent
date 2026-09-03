import pytest
from pathlib import Path
from backend.services.accessibility import AccessibilityScanner, AXE_SCRIPT_PATH
from backend.services.browser import BrowserManager

def test_axe_bundled_script_exists():
    assert AXE_SCRIPT_PATH.exists()
    assert AXE_SCRIPT_PATH.stat().st_size > 100000 # ~580KB

@pytest.mark.asyncio
async def test_accessibility_scanner_detects_violations():
    mgr = BrowserManager()
    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()

        # HTML with intentional accessibility defects
        await page.set_content("""
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <title>A11y Test Page</title>
                </head>
                <body>
                    <!-- Defect 1: Image missing alt -->
                    <img id="bad-image" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==">
                    
                    <!-- Defect 2: Empty button without text or aria-label -->
                    <button id="bad-button"></button>

                    <!-- Defect 3: Valid accessible button -->
                    <button id="good-button" aria-label="Submit application">Submit</button>
                </body>
            </html>
        """)

        scanner = AccessibilityScanner()
        findings = await scanner.run_axe_audit(page, "http://test-a11y/")

        rule_ids = [f["rule_id"] for f in findings]
        assert "image-alt" in rule_ids
        assert "button-name" in rule_ids

        # Verify findings format
        for f in findings:
            assert f["category"] == "Accessibility"
            assert f["confidence"] >= 0.9
            assert f["selector"] is not None
            assert len(f["selector"]) > 0

        # Test keyboard navigation
        kb_findings = await scanner.test_keyboard_navigation(page, "http://test-a11y/")
        assert isinstance(kb_findings, list)

        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()
