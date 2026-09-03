import pytest
from backend.services.form_tester import FormTester, is_safe_form, SAFE_FORM_DEFAULTS
from backend.services.browser import BrowserManager

def test_is_safe_form_classification():
    safe_form = {
        "action": "/api/contact",
        "submit_text": "Send Message",
        "id": "contact-form"
    }
    unsafe_form_delete = {
        "action": "/api/account/delete",
        "submit_text": "Delete Account Permanently",
        "id": "delete-form"
    }
    unsafe_form_pay = {
        "action": "/api/checkout",
        "submit_text": "Pay Now $99.00",
        "id": "pay-form"
    }

    assert is_safe_form(safe_form) is True
    assert is_safe_form(unsafe_form_delete) is False
    assert is_safe_form(unsafe_form_pay) is False

def test_generate_field_value():
    tester = FormTester()
    assert tester.generate_field_value({"type": "email"}, mode="valid") == "qa.test@example.com"
    assert tester.generate_field_value({"type": "email"}, mode="invalid_email") == "not-an-email"
    assert tester.generate_field_value({"type": "tel"}, mode="valid") == "03001234567"
    assert tester.generate_field_value({"type": "text", "maxLength": 10}, mode="too_long") == "X" * 20

@pytest.mark.asyncio
async def test_form_discovery_on_page():
    mgr = BrowserManager()
    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()

        await page.set_content("""
            <!DOCTYPE html>
            <html>
                <body>
                    <form id="signup-form" action="/api/signup" method="POST">
                        <input id="user-name" name="name" type="text" required placeholder="Name">
                        <input id="user-email" name="email" type="email" required placeholder="Email">
                        <input id="user-age" name="age" type="number" min="18" max="100">
                        <button type="submit" id="btn-submit">Create Account</button>
                    </form>
                </body>
            </html>
        """)

        tester = FormTester()
        forms = await tester.discover_forms(page)

        assert len(forms) == 1
        form = forms[0]
        assert form["selector"] == "#signup-form"
        assert form["method"] == "POST"
        assert form["submit_selector"] == "#btn-submit"
        assert len(form["fields"]) == 3

        field_names = [f["name"] for f in form["fields"]]
        assert "name" in field_names
        assert "email" in field_names
        assert "age" in field_names

        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()
