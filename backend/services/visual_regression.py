import math
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
from PIL import Image, ImageChops, ImageDraw
from bs4 import BeautifulSoup
from backend.config import DATA_DIR

def compare_screenshots(
    baseline_path: Path,
    current_path: Path,
    diff_output_path: Path,
    color_threshold: int = 25,
    pixel_threshold_pct: float = 0.5
) -> Tuple[bool, int, float]:
    """
    Compares two screenshots pixel-by-pixel with anti-aliasing tolerance.
    Generates a visual diff highlight image.
    Returns: (passed, diff_pixel_count, diff_percentage)
    """
    if not baseline_path.exists() or not current_path.exists():
        return False, 0, 100.0

    img_base = Image.open(baseline_path).convert("RGB")
    img_curr = Image.open(current_path).convert("RGB")

    # Match dimensions if slight variance occurs
    max_w = max(img_base.width, img_curr.width)
    max_h = max(img_base.height, img_curr.height)

    if img_base.size != (max_w, max_h):
        padded_base = Image.new("RGB", (max_w, max_h), (255, 255, 255))
        padded_base.paste(img_base, (0, 0))
        img_base = padded_base

    if img_curr.size != (max_w, max_h):
        padded_curr = Image.new("RGB", (max_w, max_h), (255, 255, 255))
        padded_curr.paste(img_curr, (0, 0))
        img_curr = padded_curr

    # Create grayscale base for diff output
    diff_img = img_curr.convert("RGBA")
    draw = ImageDraw.Draw(diff_img)

    base_bytes = img_base.tobytes()
    curr_bytes = img_curr.tobytes()

    diff_pixel_count = 0
    total_pixels = max_w * max_h

    # Fast difference scanning
    for i in range(0, len(base_bytes), 3):
        r_diff = abs(base_bytes[i] - curr_bytes[i])
        g_diff = abs(base_bytes[i+1] - curr_bytes[i+1])
        b_diff = abs(base_bytes[i+2] - curr_bytes[i+2])

        # Euclidean RGB distance or max delta
        if (r_diff + g_diff + b_diff) > (color_threshold * 3):
            diff_pixel_count += 1
            pixel_idx = i // 3
            x = pixel_idx % max_w
            y = pixel_idx // max_w
            # Draw magenta diff indicator
            draw.point((x, y), fill=(220, 38, 38, 220))

    diff_output_path.parent.mkdir(parents=True, exist_ok=True)
    diff_img.save(diff_output_path, format="PNG")

    diff_percentage = round((diff_pixel_count / max(total_pixels, 1)) * 100.0, 3)
    passed = diff_percentage <= pixel_threshold_pct

    return passed, diff_pixel_count, diff_percentage

class DOMRegressionAnalyzer:
    """
    Analyzes structural DOM changes (missing buttons, headings, navigation links)
    without brittle full raw HTML string comparisons.
    """
    @staticmethod
    def extract_dom_skeleton(html_content: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "html.parser")

        # Headings
        h1s = [h.get_text().strip() for h in soup.find_all("h1") if h.get_text().strip()]
        h2s = [h.get_text().strip() for h in soup.find_all("h2") if h.get_text().strip()]

        # Buttons
        buttons = [
            (b.get_text().strip() or b.get("id") or b.get("aria-label") or "button")
            for b in soup.find_all(["button", "input"])
            if b.name == "button" or b.get("type") in ("button", "submit")
        ]

        # Nav links
        nav_links = [
            a.get_text().strip()
            for a in soup.select("nav a, [role='navigation'] a")
            if a.get_text().strip()
        ]

        # Forms
        forms = [f.get("action") or f.get("id") or "form" for f in soup.find_all("form")]

        return {
            "h1": sorted(h1s),
            "h2": sorted(h2s),
            "buttons": sorted(buttons),
            "nav_links": sorted(nav_links),
            "forms": sorted(forms),
        }

    @staticmethod
    def compare_skeletons(baseline: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []

        # Missing H1
        missing_h1 = set(baseline.get("h1", [])) - set(current.get("h1", []))
        for h in missing_h1:
            findings.append({
                "rule_id": "DOM_MISSING_HEADING",
                "severity": "HIGH",
                "title": f"Structural DOM Drift: Missing H1 Heading",
                "description": f"Primary heading '{h}' was present in baseline but missing in current run.",
                "category": "Visual"
            })

        # Missing Buttons
        missing_btns = set(baseline.get("buttons", [])) - set(current.get("buttons", []))
        for b in missing_btns:
            findings.append({
                "rule_id": "DOM_MISSING_BUTTON",
                "severity": "HIGH",
                "title": f"Structural DOM Drift: Missing Button",
                "description": f"Interactive control '{b}' was present in baseline but missing in current run.",
                "category": "Functional"
            })

        # Missing Navigation items
        missing_nav = set(baseline.get("nav_links", [])) - set(current.get("nav_links", []))
        for n in missing_nav:
            findings.append({
                "rule_id": "DOM_MISSING_NAV",
                "severity": "MEDIUM",
                "title": f"Structural DOM Drift: Missing Navigation Link",
                "description": f"Navigation link '{n}' was present in baseline but missing in current run.",
                "category": "Navigation"
            })

        return findings
