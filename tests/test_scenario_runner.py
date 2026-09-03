import pytest
from backend.services.scenario_runner import ScenarioRunner, export_scenario_to_playwright_ts
from backend.services.browser import BrowserManager

@pytest.mark.asyncio
async def test_scenario_runner_execution():
    mgr = BrowserManager()
    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()

        await page.set_content("""
            <!DOCTYPE html>
            <html>
                <head><title>Scenario Target</title></head>
                <body>
                    <input id="test-input" type="text">
                    <button id="test-btn" onclick="document.getElementById('result').innerText = document.getElementById('test-input').value">Submit</button>
                    <div id="result">Initial</div>
                </body>
            </html>
        """)

        steps = [
            {"action_type": "assert_title", "expected_value": "Scenario Target"},
            {"action_type": "fill", "target": "#test-input", "value": "Playwright Automation"},
            {"action_type": "click", "target": "#test-btn"},
            {"action_type": "wait", "value": "100"},
            {"action_type": "assert_text", "expected_value": "Playwright Automation"},
            {"action_type": "assert_visibility", "target": "#result"}
        ]

        runner = ScenarioRunner(page)
        res = await runner.run_scenario(steps)

        assert res["passed"] is True
        assert res["executed_steps_count"] == len(steps)

        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()

def test_export_to_playwright_ts():
    steps = [
        {"action_type": "navigate", "target": "https://example.com"},
        {"action_type": "fill", "target": "#email", "value": "qa@example.com"},
        {"action_type": "click", "target": "#submit-btn"},
        {"action_type": "assert_url_contains", "expected_value": "dashboard"}
    ]

    ts_code = export_scenario_to_playwright_ts("User Login Flow", steps)
    assert "test('User Login Flow'" in ts_code
    assert "page.goto('https://example.com')" in ts_code
    assert "page.locator('#email').first().fill('qa@example.com')" in ts_code
    assert "page.locator('#submit-btn').first().click()" in ts_code
    assert "expect(page.url()).toContain('dashboard')" in ts_code
