import pytest
from backend.services.diagnostics import redact_url, redact_headers, DiagnosticsRecorder
from backend.services.browser import BrowserManager

def test_redact_url_and_headers():
    # Test sensitive query params
    url = "https://api.example.com/login?username=dan&password=secret123&api_key=xyz987"
    redacted = redact_url(url)
    assert "secret123" not in redacted
    assert "xyz987" not in redacted
    assert "password=%5BREDACTED%5D" in redacted or "password=[REDACTED]" in redacted
    assert "api_key=%5BREDACTED%5D" in redacted or "api_key=[REDACTED]" in redacted

    # Test headers
    headers = {
        "Authorization": "Bearer sensitive_token_abc",
        "Cookie": "session_id=12345",
        "Content-Type": "application/json"
    }
    clean_h = redact_headers(headers)
    assert clean_h["Authorization"] == "[REDACTED]"
    assert clean_h["Cookie"] == "[REDACTED]"
    assert clean_h["Content-Type"] == "application/json"

@pytest.mark.asyncio
async def test_diagnostics_recorder_console_and_network():
    mgr = BrowserManager()
    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()
        recorder = DiagnosticsRecorder(page)

        # Trigger console error and page error
        await page.set_content("""
            <html>
                <body>
                    <button id="err-btn" onclick="console.error('Simulated hydration mismatch in React component')">Trigger Log</button>
                    <button id="uncaught-btn" onclick="triggerUncaught()">Uncaught</button>
                    <script>
                        function triggerUncaught() {
                            throw new Error('Intentional crash');
                        }
                    </script>
                </body>
            </html>
        """)

        await page.click("#err-btn")
        try:
            await page.click("#uncaught-btn")
        except Exception:
            pass

        # Give browser time to process event loop
        await page.wait_for_timeout(200)

        errors = recorder.get_console_errors()
        assert len(errors) >= 1
        assert any("hydration" in e["text"].lower() or "intentional crash" in e["text"].lower() for e in errors)

        deduped = recorder.get_deduplicated_console_errors()
        assert len(deduped) >= 1

        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()
