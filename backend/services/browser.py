import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from backend.config import settings, DATA_DIR

class BrowserManager:
    """
    Manages Playwright browser lifecycles, pooling, and context isolation.
    """
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browsers: Dict[str, Browser] = {}
        self._loop = None
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        curr_loop = asyncio.get_running_loop()
        if self._lock is None or self._loop != curr_loop:
            self._lock = asyncio.Lock()
            self._loop = curr_loop
            self._playwright = None
            self._browsers = {}
        return self._lock

    async def get_playwright(self) -> Playwright:
        lock = self._get_lock()
        async with lock:
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            return self._playwright

    async def get_browser(
        self,
        browser_name: str = "chromium",
        headless: bool = True,
        slow_mo: int = 0
    ) -> Browser:
        """
        Retrieves or launches a shared browser instance for the specified engine.
        """
        p = await self.get_playwright()
        b_name = browser_name.lower()
        key = f"{b_name}_{headless}_{slow_mo}"
        lock = self._get_lock()

        async with lock:
            if key not in self._browsers or not self._browsers[key].is_connected():
                if b_name == "firefox":
                    browser_type = p.firefox
                elif b_name == "webkit":
                    browser_type = p.webkit
                else:
                    browser_type = p.chromium
                
                self._browsers[key] = await browser_type.launch(
                    headless=headless,
                    slow_mo=slow_mo,
                    args=["--no-sandbox", "--disable-dev-shm-usage"] if b_name == "chromium" else []
                )
            return self._browsers[key]

    async def create_context(
        self,
        browser_name: str = "chromium",
        headless: bool = True,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        record_video_dir: Optional[Path] = None,
        storage_state_path: Optional[str] = None,
        extra_http_headers: Optional[Dict[str, str]] = None,
        enable_tracing: bool = True,
    ) -> BrowserContext:
        """
        Creates an isolated browser context per QA run.
        Denies camera and microphone by default.
        """
        browser = await self.get_browser(browser_name=browser_name, headless=headless)
        
        context_kwargs: Dict[str, Any] = {
            "viewport": {"width": viewport_width, "height": viewport_height},
            "permissions": [], # camera and microphone denied by default
            "ignore_https_errors": True,
        }
        
        if record_video_dir:
            record_video_dir.mkdir(parents=True, exist_ok=True)
            context_kwargs["record_video_dir"] = str(record_video_dir)
            context_kwargs["record_video_size"] = {"width": viewport_width, "height": viewport_height}

        if storage_state_path and Path(storage_state_path).exists():
            context_kwargs["storage_state"] = storage_state_path

        if extra_http_headers:
            context_kwargs["extra_http_headers"] = extra_http_headers

        context = await browser.new_context(**context_kwargs)
        
        # Configure timeouts
        context.set_default_timeout(settings.REQUEST_TIMEOUT_MS)
        context.set_default_navigation_timeout(settings.REQUEST_TIMEOUT_MS)

        if enable_tracing:
            await context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True
            )

        return context

    async def close_context(
        self,
        context: BrowserContext,
        trace_save_path: Optional[Path] = None
    ):
        """
        Stops tracing if requested, saves trace artifact, and closes the isolated context.
        """
        try:
            if trace_save_path:
                trace_save_path.parent.mkdir(parents=True, exist_ok=True)
                await context.tracing.stop(path=str(trace_save_path))
            else:
                await context.tracing.stop()
        except Exception:
            pass
        finally:
            try:
                await context.close()
            except Exception:
                pass

    async def shutdown(self):
        """
        Gracefully terminates all active browsers and the Playwright driver.
        """
        lock = self._get_lock()
        async with lock:
            for browser in self._browsers.values():
                try:
                    if browser.is_connected():
                        await browser.close()
                except Exception:
                    pass
            self._browsers.clear()

            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None

# Global browser manager singleton
browser_manager = BrowserManager()
