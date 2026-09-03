import pytest
from backend.services.responsive import ResponsiveTester
from backend.services.browser import BrowserManager

@pytest.mark.asyncio
async def test_horizontal_overflow_detection():
    mgr = BrowserManager()
    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()

        # HTML with an element intentionally wider than mobile viewports (900px)
        await page.set_content("""
            <!DOCTYPE html>
            <html>
                <head>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { margin: 0; padding: 0; }
                        #wide-box {
                            width: 900px;
                            height: 100px;
                            background: red;
                        }
                    </style>
                </head>
                <body>
                    <div id="wide-box">Wide Box</div>
                </body>
            </html>
        """)

        tester = ResponsiveTester()
        
        # Test mobile viewport 375x812 (should flag overflow)
        mobile_vp = {"name": "Mobile", "width": 375, "height": 812}
        await page.set_viewport_size({"width": 375, "height": 812})
        findings_mobile = await tester.detect_horizontal_overflow(page, "http://test-overflow/", mobile_vp)
        assert len(findings_mobile) >= 1
        assert findings_mobile[0]["rule_id"] == "LAYOUT_HORIZ_OVERFLOW"
        assert "375x812" in findings_mobile[0]["viewport"]

        # Test desktop viewport 1920x1080 (should NOT flag overflow)
        desktop_vp = {"name": "Desktop", "width": 1920, "height": 1080}
        await page.set_viewport_size({"width": 1920, "height": 1080})
        findings_desktop = await tester.detect_horizontal_overflow(page, "http://test-overflow/", desktop_vp)
        assert len(findings_desktop) == 0

        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()

@pytest.mark.asyncio
async def test_element_overlap_detection():
    mgr = BrowserManager()
    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()

        # HTML with two intentionally colliding/overlapping buttons
        await page.set_content("""
            <!DOCTYPE html>
            <html>
                <body>
                    <div style="position: relative; width: 300px; height: 100px;">
                        <button id="btn1" style="position: absolute; left: 10px; top: 10px; width: 100px; height: 40px;">Button 1</button>
                        <button id="btn2" style="position: absolute; left: 20px; top: 15px; width: 100px; height: 40px;">Button 2</button>
                    </div>
                </body>
            </html>
        """)

        tester = ResponsiveTester()
        vp = {"name": "Desktop", "width": 1280, "height": 720}
        findings = await tester.detect_element_overlaps(page, "http://test-overlap/", vp)
        assert len(findings) >= 1
        assert findings[0]["rule_id"] == "LAYOUT_ELEMENT_OVERLAP"

        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()
