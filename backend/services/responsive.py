from typing import List, Dict, Any, Optional
from playwright.async_api import Page

STANDARD_VIEWPORTS = [
    {"name": "Desktop 1080p", "width": 1920, "height": 1080},
    {"name": "Desktop Large", "width": 1440, "height": 900},
    {"name": "Laptop Standard", "width": 1366, "height": 768},
    {"name": "iPad Landscape", "width": 1024, "height": 768},
    {"name": "iPad Portrait", "width": 768, "height": 1024},
    {"name": "iPhone 14 Pro", "width": 390, "height": 844},
    {"name": "iPhone Small", "width": 375, "height": 812},
]

class ResponsiveTester:
    """
    Evaluates layout health, horizontal overflow, bounding box clipping,
    and element collisions across standard and custom viewports.
    """
    def __init__(self, viewports: Optional[List[Dict[str, Any]]] = None):
        self.viewports = viewports or STANDARD_VIEWPORTS

    async def detect_horizontal_overflow(self, page: Page, current_url: str, vp: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        try:
            overflow_data = await page.evaluate("""
                () => {
                    const scrollWidth = document.documentElement.scrollWidth;
                    const innerWidth = window.innerWidth;
                    const delta = scrollWidth - innerWidth;

                    if (delta <= 5) return null;

                    // Find elements causing the overflow
                    const offenders = [];
                    const all = document.querySelectorAll('*');
                    for (const el of all) {
                        const rect = el.getBoundingClientRect();
                        if (rect.right > innerWidth + 5 && rect.width > 0 && rect.height > 0) {
                            let sel = el.tagName.toLowerCase();
                            if (el.id) sel += '#' + el.id;
                            else if (el.className) sel += '.' + el.className.toString().trim().split(/\\s+/).join('.');
                            offenders.push({
                                selector: sel,
                                right: Math.round(rect.right),
                                width: Math.round(rect.width)
                            });
                            if (offenders.length >= 3) break;
                        }
                    }

                    return {
                        scrollWidth: scrollWidth,
                        innerWidth: innerWidth,
                        delta: delta,
                        offenders: offenders
                    };
                }
            """)

            if overflow_data:
                offender_str = ", ".join([o["selector"] for o in overflow_data.get("offenders", [])]) or "Document body"
                vp_label = f"{vp['width']}x{vp['height']}"
                findings.append({
                    "rule_id": "LAYOUT_HORIZ_OVERFLOW",
                    "severity": "MEDIUM",
                    "confidence": 0.95,
                    "title": f"Horizontal Viewport Overflow ({vp_label})",
                    "description": f"Page content ({overflow_data['scrollWidth']}px) leaks beyond viewport width ({overflow_data['innerWidth']}px). Likely culprits: {offender_str}",
                    "page_url": current_url,
                    "viewport": vp_label,
                    "selector": overflow_data.get("offenders", [{}])[0].get("selector"),
                    "category": "Responsive"
                })

        except Exception:
            pass

        return findings

    async def detect_element_overlaps(self, page: Page, current_url: str, vp: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Conservative collision detection between important interactive and text elements.
        """
        findings = []
        try:
            overlaps = await page.evaluate("""
                () => {
                    const selector = 'button:not([disabled]), input:not([type="hidden"]), select, h1, h2, h3';
                    const items = Array.from(document.querySelectorAll(selector))
                        .filter(el => {
                            const style = window.getComputedStyle(el);
                            return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                        });

                    const results = [];
                    for (let i = 0; i < items.length; i++) {
                        for (let j = i + 1; j < items.length; j++) {
                            const el1 = items[i];
                            const el2 = items[j];

                            // Skip parent-child containment
                            if (el1.contains(el2) || el2.contains(el1)) continue;

                            const r1 = el1.getBoundingClientRect();
                            const r2 = el2.getBoundingClientRect();

                            // Collision check
                            const xOverlap = Math.max(0, Math.min(r1.right, r2.right) - Math.max(r1.left, r2.left));
                            const yOverlap = Math.max(0, Math.min(r1.bottom, r2.bottom) - Math.max(r1.top, r2.top));
                            const overlapArea = xOverlap * yOverlap;

                            if (overlapArea > 100) {
                                const minArea = Math.min(r1.width * r1.height, r2.width * r2.height);
                                if (minArea > 0 && (overlapArea / minArea) > 0.3) {
                                    let s1 = el1.tagName.toLowerCase() + (el1.id ? '#' + el1.id : '');
                                    let s2 = el2.tagName.toLowerCase() + (el2.id ? '#' + el2.id : '');
                                    results.push({ el1: s1, el2: s2, area: Math.round(overlapArea) });
                                    if (results.length >= 3) return results;
                                }
                            }
                        }
                    }
                    return results;
                }
            """)

            vp_label = f"{vp['width']}x{vp['height']}"
            for item in (overlaps or []):
                findings.append({
                    "rule_id": "LAYOUT_ELEMENT_OVERLAP",
                    "severity": "MEDIUM",
                    "confidence": 0.85,
                    "title": f"Element Collision / Overlap ({vp_label})",
                    "description": f"Elements '{item['el1']}' and '{item['el2']}' overlap significantly ({item['area']}px² collision).",
                    "page_url": current_url,
                    "viewport": vp_label,
                    "selector": item['el1'],
                    "category": "Responsive"
                })

        except Exception:
            pass

        return findings

    async def detect_viewport_clipping(self, page: Page, current_url: str, vp: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detects critical interactive controls clipped outside the usable viewport boundary.
        """
        findings = []
        try:
            clipped = await page.evaluate("""
                () => {
                    const selector = 'button, input[type="submit"], [role="button"]';
                    const items = document.querySelectorAll(selector);
                    const results = [];
                    const innerW = window.innerWidth;

                    for (const el of items) {
                        const r = el.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0) {
                            if (r.left < 0 || r.right > innerW + 20) {
                                let sel = el.tagName.toLowerCase();
                                if (el.id) sel += '#' + el.id;
                                else if (el.className) sel += '.' + el.className.toString().trim().split(/\\s+/).join('.');
                                results.push({
                                    selector: sel,
                                    left: Math.round(r.left),
                                    right: Math.round(r.right),
                                    text: el.innerText.trim().slice(0, 50)
                                });
                                if (results.length >= 3) break;
                            }
                        }
                    }
                    return results;
                }
            """)

            vp_label = f"{vp['width']}x{vp['height']}"
            for c in (clipped or []):
                findings.append({
                    "rule_id": "LAYOUT_VIEWPORT_CLIPPING",
                    "severity": "HIGH",
                    "confidence": 0.9,
                    "title": f"Action Control Viewport Clipping ({vp_label})",
                    "description": f"Interactive control '{c['selector']}' ({c.get('text', '')}) extends outside viewport boundaries.",
                    "page_url": current_url,
                    "viewport": vp_label,
                    "selector": c['selector'],
                    "category": "Responsive"
                })

        except Exception:
            pass

        return findings

    async def inspect_page_viewports(
        self,
        page: Page,
        current_url: str,
        viewports_to_test: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Cycles through configured viewports, resizes the page, and records layout defects.
        """
        all_findings = []
        targets = viewports_to_test or self.viewports

        original_size = page.viewport_size

        for vp in targets:
            await page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            await page.wait_for_timeout(100) # layout settle

            # 1. Horizontal overflow
            overflow = await self.detect_horizontal_overflow(page, current_url, vp)
            all_findings.extend(overflow)

            # 2. Overlap detection
            overlaps = await self.detect_element_overlaps(page, current_url, vp)
            all_findings.extend(overlaps)

            # 3. Viewport clipping
            clipping = await self.detect_viewport_clipping(page, current_url, vp)
            all_findings.extend(clipping)

        # Restore initial viewport if set
        if original_size:
            await page.set_viewport_size(original_size)

        return all_findings
