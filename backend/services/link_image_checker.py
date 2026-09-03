from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Optional, Set
import httpx
from playwright.async_api import Page

class LinkChecker:
    """
    Checks links for broken destinations, redirect loops, and improper usage.
    """
    def __init__(self, base_url: str, check_external: bool = False, timeout_sec: float = 8.0):
        self.base_url = base_url
        self.check_external = check_external
        self.timeout_sec = timeout_sec
        self._checked_urls_cache: Dict[str, Dict[str, Any]] = {}

    def classify_link(self, raw_href: str) -> str:
        s = raw_href.strip().lower()
        if s.startswith("mailto:"):
            return "Mail Link"
        if s.startswith("tel:"):
            return "Telephone Link"
        if s.startswith("#"):
            return "Anchor Link"
        if any(s.endswith(ext) for ext in (".pdf", ".zip", ".tar.gz", ".csv", ".xlsx", ".dmg", ".exe")):
            return "Download Link"

        joined = urljoin(self.base_url, raw_href)
        base_host = urlparse(self.base_url).netloc.lower()
        target_host = urlparse(joined).netloc.lower()

        if target_host == base_host:
            return "Internal Link"
        return "External Link"

    async def check_links_on_page(self, page: Page, current_url: str) -> List[Dict[str, Any]]:
        """
        Discovers all links on the page and tests their status.
        """
        findings: List[Dict[str, Any]] = []

        raw_links = await page.eval_on_selector_all(
            "a",
            """elements => elements.map(el => ({
                href: el.getAttribute('href'),
                text: el.innerText.trim().slice(0, 100),
                id: el.id,
                className: el.className
            }))"""
        )

        async with httpx.AsyncClient(
            timeout=self.timeout_sec,
            follow_redirects=True,
            max_redirects=5,
            headers={"User-Agent": "WebQA-Agent/1.0"}
        ) as client:
            for item in raw_links:
                href = item.get("href")
                
                # Check empty or whitespace href
                if href is None or href.strip() == "":
                    findings.append({
                        "rule_id": "LINK_EMPTY_HREF",
                        "severity": "LOW",
                        "confidence": 1.0,
                        "title": "Empty Anchor Href",
                        "description": "Anchor element has empty or missing href attribute.",
                        "page_url": current_url,
                        "target_url": "",
                        "element_text": item.get("text", "")
                    })
                    continue

                href_str = href.strip()
                link_type = self.classify_link(href_str)

                # Skip mail, tel, anchor
                if link_type in ("Mail Link", "Telephone Link", "Anchor Link"):
                    continue

                if link_type == "External Link" and not self.check_external:
                    continue

                full_url = urljoin(current_url, href_str)
                
                # Check cache first
                if full_url in self._checked_urls_cache:
                    cached = self._checked_urls_cache[full_url]
                    if cached.get("is_broken"):
                        findings.append({
                            **cached,
                            "page_url": current_url,
                            "element_text": item.get("text", "")
                        })
                    continue

                # Perform HTTP check
                try:
                    res = await client.get(full_url)
                    status = res.status_code
                    is_broken = status >= 400
                    
                    finding = {
                        "rule_id": f"LINK_HTTP_{status}" if status in (404, 500) else "LINK_FAILED_STATUS",
                        "severity": "CRITICAL" if status >= 500 else ("HIGH" if status == 404 else "MEDIUM"),
                        "confidence": 1.0,
                        "title": f"Broken Link (HTTP {status})",
                        "description": f"Link to '{full_url}' returned HTTP {status}.",
                        "page_url": current_url,
                        "target_url": full_url,
                        "status_code": status,
                        "link_type": link_type,
                        "is_broken": is_broken
                    }
                    self._checked_urls_cache[full_url] = finding
                    if is_broken:
                        finding["element_text"] = item.get("text", "")
                        findings.append(finding)

                except httpx.TooManyRedirects:
                    finding = {
                        "rule_id": "LINK_REDIRECT_LOOP",
                        "severity": "HIGH",
                        "confidence": 1.0,
                        "title": "Redirect Loop Detected",
                        "description": f"Link to '{full_url}' exceeded maximum redirects.",
                        "page_url": current_url,
                        "target_url": full_url,
                        "link_type": link_type,
                        "is_broken": True
                    }
                    self._checked_urls_cache[full_url] = finding
                    finding["element_text"] = item.get("text", "")
                    findings.append(finding)

                except Exception as e:
                    finding = {
                        "rule_id": "LINK_CONN_FAILED",
                        "severity": "HIGH",
                        "confidence": 0.95,
                        "title": "Link Connection Failed",
                        "description": f"Failed to connect to '{full_url}': {str(e)}",
                        "page_url": current_url,
                        "target_url": full_url,
                        "link_type": link_type,
                        "is_broken": True
                    }
                    self._checked_urls_cache[full_url] = finding
                    finding["element_text"] = item.get("text", "")
                    findings.append(finding)

        return findings


class ImageChecker:
    """
    Inspects image elements for broken sources, naturalWidth == 0, and missing alt attributes.
    """
    async def inspect_images(self, page: Page, current_url: str) -> List[Dict[str, Any]]:
        findings = []

        images_data = await page.eval_on_selector_all(
            "img",
            """elements => elements.map((el, i) => {
                let selector = '';
                if (el.id) selector = '#' + el.id;
                else if (el.className) selector = '.' + el.className.trim().split(/\\s+/).join('.');
                else selector = 'img:nth-of-type(' + (i + 1) + ')';

                return {
                    selector: selector,
                    src: el.getAttribute('src') || '',
                    currentSrc: el.currentSrc || '',
                    alt: el.getAttribute('alt'),
                    naturalWidth: el.naturalWidth,
                    naturalHeight: el.naturalHeight,
                    complete: el.complete
                };
            })"""
        )

        for img in images_data:
            src = img.get("src", "")
            alt = img.get("alt")
            nw = img.get("naturalWidth", 0)
            selector = img.get("selector", "img")

            # Missing or empty src
            if not src.strip():
                findings.append({
                    "rule_id": "IMG_MISSING_SRC",
                    "severity": "HIGH",
                    "confidence": 1.0,
                    "title": "Missing Image Source",
                    "description": f"Image element {selector} has missing or empty src attribute.",
                    "page_url": current_url,
                    "selector": selector,
                    "category": "Content"
                })
            # Broken image: complete and naturalWidth is 0
            elif img.get("complete") and nw == 0:
                findings.append({
                    "rule_id": "IMG_BROKEN_SRC",
                    "severity": "MEDIUM",
                    "confidence": 1.0,
                    "title": "Broken Image Detected",
                    "description": f"Image {selector} failed to render (naturalWidth = 0, src='{src}').",
                    "page_url": current_url,
                    "selector": selector,
                    "category": "Content"
                })

            # Missing alt text
            if alt is None:
                findings.append({
                    "rule_id": "IMG_MISSING_ALT",
                    "severity": "LOW",
                    "confidence": 0.95,
                    "title": "Image Missing Alt Text",
                    "description": f"Image {selector} does not have an alt attribute.",
                    "page_url": current_url,
                    "selector": selector,
                    "category": "Accessibility"
                })

        return findings
