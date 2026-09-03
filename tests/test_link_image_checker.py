import pytest
from backend.services.link_image_checker import LinkChecker, ImageChecker
from backend.services.browser import BrowserManager

def test_link_classification():
    checker = LinkChecker(base_url="https://example.com")
    assert checker.classify_link("mailto:hello@example.com") == "Mail Link"
    assert checker.classify_link("tel:+123456789") == "Telephone Link"
    assert checker.classify_link("#features") == "Anchor Link"
    assert checker.classify_link("/files/report.pdf") == "Download Link"
    assert checker.classify_link("/about") == "Internal Link"
    assert checker.classify_link("https://otherdomain.com/docs") == "External Link"

@pytest.mark.asyncio
async def test_image_checker_broken_and_missing_alt():
    mgr = BrowserManager()
    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()
        
        await page.set_content("""
            <html>
                <body>
                    <!-- Valid Image -->
                    <img id="valid-img" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==" alt="Valid pixel">
                    
                    <!-- Broken Image -->
                    <img id="broken-img" src="/non-existent-image-path.jpg" alt="Broken">
                    
                    <!-- Missing Alt -->
                    <img id="missing-alt-img" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==">
                </body>
            </html>
        """)

        # Wait for image load attempts to settle
        await page.wait_for_timeout(300)

        checker = ImageChecker()
        findings = await checker.inspect_images(page, "http://test/")
        
        rule_ids = [f["rule_id"] for f in findings]
        assert "IMG_BROKEN_SRC" in rule_ids
        assert "IMG_MISSING_ALT" in rule_ids

        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()
