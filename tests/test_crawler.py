import pytest
from backend.services.crawler import normalize_url, is_allowed_domain, matches_ignore_pattern, PageCrawler
from backend.services.browser import BrowserManager

def test_normalize_url():
    base = "https://example.com/blog/"
    
    # Fragments and tracking params
    assert normalize_url("https://example.com/about?utm_source=twitter&id=5#team", base) == "https://example.com/about?id=5"
    
    # Trailing slash normalization
    assert normalize_url("/pricing/", base) == "https://example.com/pricing"
    assert normalize_url("/", base) == "https://example.com/"
    
    # Relative path resolution
    assert normalize_url("../contact", base) == "https://example.com/contact"
    
    # Ignored schemes
    assert normalize_url("mailto:test@example.com", base) is None
    assert normalize_url("tel:123456", base) is None
    assert normalize_url("javascript:void(0)", base) is None
    assert normalize_url("#top", base) is None

def test_is_allowed_domain():
    base = "https://app.mycompany.com"
    allowed = ["staging.mycompany.com", "cdn.example.org"]

    assert is_allowed_domain("https://app.mycompany.com/dashboard", base, allowed) is True
    assert is_allowed_domain("https://staging.mycompany.com/test", base, allowed) is True
    assert is_allowed_domain("https://cdn.example.org/assets", base, allowed) is True
    assert is_allowed_domain("https://attacker.com/malicious", base, allowed) is False

def test_matches_ignore_pattern():
    patterns = [r"/admin/.*", r".*\.pdf$"]
    assert matches_ignore_pattern("https://example.com/admin/settings", patterns) is True
    assert matches_ignore_pattern("https://example.com/docs/file.pdf", patterns) is True
    assert matches_ignore_pattern("https://example.com/pricing", patterns) is False

def test_crawler_limits_and_deduplication():
    crawler = PageCrawler(base_url="https://example.com", max_depth=2, max_pages=3)
    
    # Enqueue root
    crawler.enqueue("https://example.com", depth=0)
    assert len(crawler.queue) == 1
    
    # Duplicate root
    assert crawler.enqueue("https://example.com/#fragment", depth=0) is None
    
    # Child pages
    crawler.enqueue("https://example.com/page1", depth=1)
    crawler.enqueue("https://example.com/page2", depth=2)
    
    # Exceeds max_pages (max_pages=3)
    assert crawler.enqueue("https://example.com/page3", depth=2) is None
    
    # Exceeds max_depth (depth=3 > max_depth=2)
    crawler2 = PageCrawler(base_url="https://example.com", max_depth=1, max_pages=10)
    assert crawler2.enqueue("https://example.com/deep", depth=2) is None

@pytest.mark.asyncio
async def test_spa_push_state_discovery():
    mgr = BrowserManager()
    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()
        crawler = PageCrawler(base_url="https://example.com")
        
        await page.set_content("""
            <html>
                <body>
                    <button id="nav-btn" onclick="history.pushState({}, '', '/dashboard')">Go to Dashboard</button>
                </body>
            </html>
        """)
        await crawler.attach_spa_route_listener(page)
        await page.click("#nav-btn")
        routes = await crawler.collect_spa_routes(page, "https://example.com", 0)
        assert any("dashboard" in r for r in routes)
        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()
