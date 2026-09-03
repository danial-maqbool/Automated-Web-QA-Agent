import re
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse
from typing import Set, List, Optional, Dict, Any
from bs4 import BeautifulSoup
import httpx
from playwright.async_api import Page

# Tracking and analytics query parameters to strip
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid", "_ga", "ref", "source"
}

def normalize_url(raw_url: str, base_url: str) -> Optional[str]:
    """
    Normalizes a URL by resolving against base_url, stripping fragments,
    removing tracking query parameters, and normalizing trailing slashes.
    Returns None if URL is invalid, non-HTTP, or mailto/tel.
    """
    if not raw_url or raw_url.strip().startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
        return None

    try:
        joined = urljoin(base_url, raw_url.strip())
        parsed = urlparse(joined)

        if parsed.scheme not in ("http", "https"):
            return None

        # Filter out tracking query params
        clean_query = []
        if parsed.query:
            qs = parse_qs(parsed.query, keep_blank_values=False)
            for k, v in qs.items():
                if k.lower() not in TRACKING_PARAMS:
                    for val in v:
                        clean_query.append((k, val))
        clean_query.sort()
        encoded_query = urlencode(clean_query)

        # Normalize path
        path = parsed.path
        if not path:
            path = "/"
        elif path != "/" and path.endswith("/"):
            path = path[:-1]

        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",
            encoded_query,
            "" # Fragment removed
        ))
        return normalized
    except Exception:
        return None

def is_allowed_domain(url: str, base_url: str, allowed_domains: Optional[List[str]] = None) -> bool:
    """
    Checks whether a URL is on the base domain or in the allowed_domains list.
    """
    try:
        target_host = urlparse(url).netloc.lower()
        base_host = urlparse(base_url).netloc.lower()

        if target_host == base_host:
            return True

        if allowed_domains:
            for domain in allowed_domains:
                d = domain.lower().strip()
                if target_host == d or target_host.endswith("." + d):
                    return True

        return False
    except Exception:
        return False

def matches_ignore_pattern(url: str, ignore_patterns: Optional[List[str]]) -> bool:
    """
    Checks if a URL matches any configured regex or wildcard ignore pattern.
    """
    if not ignore_patterns:
        return False

    for pattern in ignore_patterns:
        try:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        except re.error:
            continue
    return False

class PageCrawler:
    """
    Intelligent page discovery engine supporting MPAs and SPAs.
    """
    def __init__(
        self,
        base_url: str,
        allowed_domains: Optional[List[str]] = None,
        max_depth: int = 3,
        max_pages: int = 50,
        ignore_patterns: Optional[List[str]] = None
    ):
        self.base_url = base_url
        self.allowed_domains = allowed_domains or []
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.ignore_patterns = ignore_patterns or []

        self.visited_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()
        self.queue: List[Dict[str, Any]] = [] # [{"url": ..., "depth": 0, "parent": None}]

    def enqueue(self, raw_url: str, depth: int = 0, parent: Optional[str] = None) -> Optional[str]:
        resolution_base = parent or self.base_url
        norm = normalize_url(raw_url, resolution_base)
        if not norm:
            return None

        if not is_allowed_domain(norm, self.base_url, self.allowed_domains):
            return None

        if matches_ignore_pattern(norm, self.ignore_patterns):
            return None

        if norm in self.discovered_urls:
            return None

        if depth > self.max_depth:
            return None

        if len(self.discovered_urls) >= self.max_pages:
            return None

        self.discovered_urls.add(norm)
        self.queue.append({
            "url": norm,
            "depth": depth,
            "parent": parent
        })
        return norm

    async def fetch_sitemap_urls(self) -> List[str]:
        """
        Attempts to discover pages from /sitemap.xml if reachable.
        """
        sitemap_url = urljoin(self.base_url, "/sitemap.xml")
        found = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(sitemap_url)
                if res.status_code == 200 and ("xml" in res.headers.get("content-type", "") or "<urlset" in res.text):
                    soup = BeautifulSoup(res.text, "html.parser")
                    for loc in soup.find_all("loc"):
                        loc_text = loc.get_text().strip()
                        enqueued = self.enqueue(loc_text, depth=1, parent=sitemap_url)
                        if enqueued:
                            found.append(enqueued)
        except Exception:
            pass
        return found

    async def discover_page_links(self, page: Page, current_url: str, current_depth: int) -> List[str]:
        """
        Extracts links and SPA pushState routes from the live Playwright DOM.
        """
        discovered = []
        try:
            # Extract browser-resolved hrefs from DOM
            hrefs = await page.eval_on_selector_all(
                "a[href], button[data-href], [role='link'][href]",
                """elements => elements.map(el => {
                    if (el.tagName === 'A') return el.href || el.getAttribute('href');
                    if (el.getAttribute('data-href')) return el.getAttribute('data-href');
                    return el.getAttribute('href');
                }).filter(Boolean)"""
            )

            for href in hrefs:
                norm = self.enqueue(href, depth=current_depth + 1, parent=current_url)
                if norm:
                    discovered.append(norm)

        except Exception:
            pass

        return discovered

    async def attach_spa_route_listener(self, page: Page):
        """
        Injects a lightweight script to track pushState/replaceState client-side transitions.
        """
        script = """
            if (!window.__webqa_spa_installed) {
                window.__webqa_spa_installed = true;
                window.__webqa_spa_routes = [];
                const originalPushState = history.pushState;
                history.pushState = function(...args) {
                    if (args[2]) {
                        window.__webqa_spa_routes.push(args[2]);
                    }
                    return originalPushState.apply(this, args);
                };
                const originalReplaceState = history.replaceState;
                history.replaceState = function(...args) {
                    if (args[2]) {
                        window.__webqa_spa_routes.push(args[2]);
                    }
                    return originalReplaceState.apply(this, args);
                };
            }
        """
        await page.add_init_script(script)
        try:
            await page.evaluate(script)
        except Exception:
            pass

    async def collect_spa_routes(self, page: Page, current_url: str, current_depth: int) -> List[str]:
        """
        Collects client-side SPA routes tracked by pushState/replaceState.
        """
        spa_routes = []
        try:
            routes = await page.evaluate("window.__webqa_spa_routes || []")
            for r in routes:
                norm = self.enqueue(str(r), depth=current_depth + 1, parent=current_url)
                if norm:
                    spa_routes.append(norm)
        except Exception:
            pass
        return spa_routes
