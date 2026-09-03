import uuid
from pathlib import Path
from typing import Optional
from playwright.async_api import Page
from backend.config import DATA_DIR

class EvidenceCollector:
    """
    Manages multimodal evidence capture: full-page screenshots, viewport screenshots,
    element-highlighted screenshots, Playwright trace packages, and videos.
    """
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.screenshots_dir = DATA_DIR / "screenshots" / run_id
        self.traces_dir = DATA_DIR / "traces"
        self.videos_dir = DATA_DIR / "videos" / run_id

        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir.mkdir(parents=True, exist_ok=True)

    async def capture_viewport_screenshot(self, page: Page, name_prefix: str = "viewport") -> str:
        """
        Captures the visible viewport screenshot.
        """
        filename = f"{name_prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = self.screenshots_dir / filename
        await page.screenshot(path=str(filepath), full_page=False)
        return f"screenshots/{self.run_id}/{filename}"

    async def capture_fullpage_screenshot(self, page: Page, name_prefix: str = "fullpage") -> str:
        """
        Captures full document scroll screenshot.
        """
        filename = f"{name_prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = self.screenshots_dir / filename
        await page.screenshot(path=str(filepath), full_page=True)
        return f"screenshots/{self.run_id}/{filename}"

    async def capture_element_screenshot(
        self,
        page: Page,
        selector: str,
        name_prefix: str = "element",
        highlight: bool = True
    ) -> Optional[str]:
        """
        Highlights the affected element with a red bounding outline, captures a screenshot,
        and cleanly restores the DOM style.
        """
        filename = f"{name_prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = self.screenshots_dir / filename

        try:
            locator = page.locator(selector).first
            if await locator.count() == 0:
                # Fallback to viewport screenshot if element selector cannot be resolved
                return await self.capture_viewport_screenshot(page, name_prefix=f"{name_prefix}_fallback")

            if highlight:
                # Apply temporary highlight style
                await locator.evaluate("""
                    el => {
                        el.__webqa_prev_outline = el.style.outline;
                        el.__webqa_prev_shadow = el.style.boxShadow;
                        el.style.outline = '3px solid #dc2626';
                        el.style.outlineOffset = '2px';
                        el.style.boxShadow = '0 0 12px rgba(220, 38, 38, 0.6)';
                    }
                """)

            # Capture screenshot of element or surrounding viewport
            await locator.screenshot(path=str(filepath))

            if highlight:
                # Restore original styles
                await locator.evaluate("""
                    el => {
                        el.style.outline = el.__webqa_prev_outline || '';
                        el.style.outlineOffset = '';
                        el.style.boxShadow = el.__webqa_prev_shadow || '';
                    }
                """)

            return f"screenshots/{self.run_id}/{filename}"
        except Exception:
            # Fallback to viewport screenshot if locator screenshot fails
            try:
                return await self.capture_viewport_screenshot(page, name_prefix=f"{name_prefix}_err")
            except Exception:
                return None

    def get_trace_path(self) -> Path:
        """Returns the file path where the Playwright trace zip should be saved."""
        return self.traces_dir / f"{self.run_id}.zip"

    def get_trace_url(self) -> str:
        """Returns relative URL for the trace archive."""
        return f"traces/{self.run_id}.zip"
