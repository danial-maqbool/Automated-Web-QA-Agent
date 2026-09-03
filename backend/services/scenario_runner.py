import time
from typing import List, Dict, Any, Optional
from playwright.async_api import Page
from backend.services.diagnostics import DiagnosticsRecorder
from backend.services.evidence import EvidenceCollector

class StepExecutionResult:
    def __init__(self, step_index: int, action_type: str, passed: bool, message: str = "", duration_ms: float = 0.0):
        self.step_index = step_index
        self.action_type = action_type
        self.passed = passed
        self.message = message
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "action_type": self.action_type,
            "passed": self.passed,
            "message": self.message,
            "duration_ms": round(self.duration_ms, 2)
        }

class ScenarioRunner:
    """
    Executes user-defined test scenarios, no-code steps, and assertions against Playwright.
    """
    def __init__(self, page: Page, diagnostics: Optional[DiagnosticsRecorder] = None, evidence: Optional[EvidenceCollector] = None):
        self.page = page
        self.diagnostics = diagnostics
        self.evidence = evidence

    async def execute_step(self, step: Dict[str, Any], index: int) -> StepExecutionResult:
        action = step.get("action_type", "").lower()
        target = step.get("target")
        val = step.get("value")
        exp = step.get("expected_value")
        is_optional = step.get("is_optional", False)

        t0 = time.time()

        try:
            # Action: Navigate
            if action == "navigate":
                await self.page.goto(target or val, wait_until="domcontentloaded")

            # Action: Click
            elif action == "click":
                await self.page.locator(target).first.click(timeout=5000)

            # Action: Fill
            elif action == "fill":
                await self.page.locator(target).first.fill(val or "")

            # Action: Select
            elif action == "select":
                await self.page.locator(target).first.select_option(val or "")

            # Action: Check / Uncheck
            elif action == "check":
                await self.page.locator(target).first.check()
            elif action == "uncheck":
                await self.page.locator(target).first.uncheck()

            # Action: Wait
            elif action == "wait":
                ms = int(val) if val and str(val).isdigit() else 1000
                await self.page.wait_for_timeout(ms)

            # Action: Press Key
            elif action == "press_key":
                await self.page.keyboard.press(val or "Enter")

            # Action: Take Screenshot
            elif action == "take_screenshot":
                if self.evidence:
                    await self.evidence.capture_viewport_screenshot(self.page, f"step_{index}")

            # Assertion: URL Equals or Contains
            elif action in ("assert_url", "assert_url_contains"):
                actual_url = self.page.url
                target_str = exp or val or target or ""
                if action == "assert_url" and actual_url != target_str:
                    raise AssertionError(f"Expected URL '{target_str}', got '{actual_url}'")
                elif action == "assert_url_contains" and target_str not in actual_url:
                    raise AssertionError(f"Expected URL to contain '{target_str}', got '{actual_url}'")

            # Assertion: Title Equals
            elif action == "assert_title":
                actual_title = await self.page.title()
                if actual_title != (exp or val):
                    raise AssertionError(f"Expected title '{exp or val}', got '{actual_title}'")

            # Assertion: Text Exists / Does Not Exist
            elif action in ("assert_text", "assert_text_exists"):
                expected_text = exp or val or ""
                page_text = await self.page.content()
                if expected_text not in page_text:
                    raise AssertionError(f"Text '{expected_text}' not found on page.")

            elif action == "assert_text_not_exists":
                forbidden_text = exp or val or ""
                page_text = await self.page.content()
                if forbidden_text in page_text:
                    raise AssertionError(f"Forbidden text '{forbidden_text}' found on page.")

            # Assertion: Visibility
            elif action == "assert_visibility":
                is_vis = await self.page.locator(target).first.is_visible()
                if not is_vis:
                    raise AssertionError(f"Element '{target}' is not visible.")

            elif action == "assert_hidden":
                is_vis = await self.page.locator(target).first.is_visible()
                if is_vis:
                    raise AssertionError(f"Element '{target}' is unexpectedly visible.")

            # Assertion: Element Enabled / Disabled
            elif action == "assert_enabled":
                is_en = await self.page.locator(target).first.is_enabled()
                if not is_en:
                    raise AssertionError(f"Element '{target}' is disabled.")

            elif action == "assert_disabled":
                is_en = await self.page.locator(target).first.is_enabled()
                if is_en:
                    raise AssertionError(f"Element '{target}' is unexpectedly enabled.")

            # Assertion: No Console Errors
            elif action == "assert_no_console_errors":
                if self.diagnostics:
                    errors = self.diagnostics.get_console_errors()
                    if errors:
                        raise AssertionError(f"Expected 0 console errors, but found {len(errors)}: {errors[0]['text']}")

            # Assertion: No Failed Requests
            elif action == "assert_no_failed_requests":
                if self.diagnostics:
                    fails = self.diagnostics.get_failed_network_requests()
                    if fails:
                        raise AssertionError(f"Expected 0 network failures, but found {len(fails)}: {fails[0]['url']}")

            else:
                return StepExecutionResult(index, action, False, f"Unknown action: '{action}'", (time.time() - t0) * 1000)

            return StepExecutionResult(index, action, True, "Step passed", (time.time() - t0) * 1000)

        except Exception as e:
            duration = (time.time() - t0) * 1000
            if is_optional:
                return StepExecutionResult(index, action, True, f"Optional step skipped: {str(e)}", duration)
            return StepExecutionResult(index, action, False, str(e), duration)

    async def run_scenario(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes an ordered list of scenario steps.
        """
        results = []
        overall_passed = True

        for idx, step in enumerate(steps):
            res = await self.execute_step(step, idx)
            results.append(res.to_dict())
            if not res.passed:
                overall_passed = False
                break

        return {
            "passed": overall_passed,
            "steps_count": len(steps),
            "executed_steps_count": len(results),
            "step_results": results
        }

def export_scenario_to_playwright_ts(scenario_name: str, steps: List[Dict[str, Any]]) -> str:
    """
    Exports a test scenario to readable, idiomatic Playwright TypeScript code.
    """
    lines = [
        "import { test, expect } from '@playwright/test';",
        "",
        f"test('{scenario_name}', async ({{ page }}) => {{",
    ]

    for step in steps:
        action = step.get("action_type", "").lower()
        target = step.get("target", "")
        val = step.get("value", "")
        exp = step.get("expected_value", "")

        if action == "navigate":
            lines.append(f"  await page.goto('{target or val}');")
        elif action == "click":
            lines.append(f"  await page.locator('{target}').first().click();")
        elif action == "fill":
            lines.append(f"  await page.locator('{target}').first().fill('{val}');")
        elif action == "select":
            lines.append(f"  await page.locator('{target}').first().selectOption('{val}');")
        elif action == "check":
            lines.append(f"  await page.locator('{target}').first().check();")
        elif action == "uncheck":
            lines.append(f"  await page.locator('{target}').first().uncheck();")
        elif action == "wait":
            lines.append(f"  await page.waitForTimeout({val or 1000});")
        elif action == "press_key":
            lines.append(f"  await page.keyboard.press('{val or 'Enter'}');")
        elif action == "assert_url":
            lines.append(f"  expect(page.url()).toBe('{exp or val or target}');")
        elif action == "assert_url_contains":
            lines.append(f"  expect(page.url()).toContain('{exp or val or target}');")
        elif action == "assert_title":
            lines.append(f"  await expect(page).toHaveTitle('{exp or val}');")
        elif action == "assert_text":
            lines.append(f"  await expect(page.locator('body')).toContainText('{exp or val}');")
        elif action == "assert_visibility":
            lines.append(f"  await expect(page.locator('{target}')).toBeVisible();")
        elif action == "assert_hidden":
            lines.append(f"  await expect(page.locator('{target}')).toBeHidden();")

    lines.append("});")
    return "\n".join(lines)
