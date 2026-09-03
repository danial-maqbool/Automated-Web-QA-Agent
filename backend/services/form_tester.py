import re
from typing import List, Dict, Any, Optional
from playwright.async_api import Page

SAFE_FORM_DEFAULTS = {
    "name": "QA Test User",
    "email": "qa.test@example.com",
    "tel": "03001234567",
    "number": "42",
    "text": "Automated QA test input",
    "textarea": "Automated QA test message and feedback.",
    "password": "QaTestPassword!123",
    "url": "https://example.com",
    "date": "2026-09-01",
}

DESTRUCTIVE_KEYWORDS = {
    "delete", "remove", "pay", "purchase", "checkout", "buy",
    "order", "transfer", "destroy", "cancel subscription", "terminate"
}

def is_safe_form(form_data: Dict[str, Any]) -> bool:
    """
    Evaluates form text, buttons, and action URLs against destructive keywords.
    """
    text_corpus = " ".join([
        form_data.get("action", ""),
        form_data.get("id", ""),
        form_data.get("name", ""),
        form_data.get("submit_text", "")
    ]).lower()

    for kw in DESTRUCTIVE_KEYWORDS:
        if kw in text_corpus:
            return False
    return True

class FormTester:
    """
    Discovers forms, analyzes input constraints, and safely tests validation.
    """
    async def discover_forms(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extracts structured form schemas, field constraints, and submit buttons from DOM.
        """
        return await page.evaluate("""
            () => {
                const forms = Array.from(document.querySelectorAll('form'));
                return forms.map((f, fIdx) => {
                    let formSelector = '';
                    if (f.id) formSelector = '#' + f.id;
                    else if (f.name) formSelector = 'form[name="' + f.name + '"]';
                    else formSelector = 'form:nth-of-type(' + (fIdx + 1) + ')';

                    const action = f.getAttribute('action') || '';
                    const method = (f.getAttribute('method') || 'GET').toUpperCase();

                    // Find submit button
                    const submitBtn = f.querySelector('button[type="submit"], input[type="submit"], button:not([type])');
                    let submitSelector = submitBtn ? (submitBtn.id ? '#' + submitBtn.id : formSelector + ' button[type="submit"]') : null;
                    let submitText = submitBtn ? submitBtn.innerText.trim() : '';

                    // Fields
                    const fields = Array.from(f.querySelectorAll('input, textarea, select')).map(el => {
                        let sel = el.id ? '#' + el.id : (el.name ? `[name="${el.name}"]` : el.tagName.toLowerCase());
                        return {
                            selector: sel,
                            tag: el.tagName.toLowerCase(),
                            type: (el.getAttribute('type') || (el.tagName === 'TEXTAREA' ? 'textarea' : 'text')).toLowerCase(),
                            name: el.getAttribute('name') || '',
                            id: el.getAttribute('id') || '',
                            required: el.hasAttribute('required') || el.required,
                            minLength: el.minLength > 0 ? el.minLength : null,
                            maxLength: el.maxLength > 0 ? el.maxLength : null,
                            min: el.min || null,
                            max: el.max || null,
                            pattern: el.pattern || null,
                            placeholder: el.placeholder || '',
                            value: el.value || ''
                        };
                    });

                    return {
                        selector: formSelector,
                        action: action,
                        method: method,
                        submit_selector: submitSelector,
                        submit_text: submitText,
                        fields: fields
                    };
                });
            }
        """)

    def generate_field_value(self, field: Dict[str, Any], mode: str = "valid") -> str:
        """
        Generates safe boundary or format values for a given form input.
        Modes: 'valid', 'empty', 'invalid_email', 'too_short', 'too_long'
        """
        f_type = field.get("type", "text")
        
        if mode == "empty":
            return ""

        if mode == "invalid_email":
            return "not-an-email"

        if mode == "too_short":
            return "a"

        if mode == "too_long":
            max_len = field.get("maxLength") or 255
            return "X" * (max_len + 10)

        # Default 'valid'
        if f_type in ("email",):
            return SAFE_FORM_DEFAULTS["email"]
        if f_type in ("tel", "phone"):
            return SAFE_FORM_DEFAULTS["tel"]
        if f_type in ("number", "range"):
            return SAFE_FORM_DEFAULTS["number"]
        if f_type in ("password",):
            return SAFE_FORM_DEFAULTS["password"]
        if f_type in ("url",):
            return SAFE_FORM_DEFAULTS["url"]
        if f_type in ("date",):
            return SAFE_FORM_DEFAULTS["date"]
        if field.get("tag") == "textarea":
            return SAFE_FORM_DEFAULTS["textarea"]
        
        # Check name clues
        name_lower = field.get("name", "").lower()
        if "name" in name_lower:
            return SAFE_FORM_DEFAULTS["name"]
        if "email" in name_lower:
            return SAFE_FORM_DEFAULTS["email"]
        if "phone" in name_lower or "tel" in name_lower:
            return SAFE_FORM_DEFAULTS["tel"]

        return SAFE_FORM_DEFAULTS["text"]

    async def test_form_validation(self, page: Page, current_url: str, form_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Safely tests form fields for empty required submission and invalid email formats.
        """
        findings: List[Dict[str, Any]] = []

        if not is_safe_form(form_data):
            # Blocked for safety
            return findings

        form_sel = form_data.get("selector")
        submit_sel = form_data.get("submit_selector")
        fields = form_data.get("fields", [])

        if not submit_sel or not fields:
            return findings

        # Check for required fields with missing validation
        required_fields = [f for f in fields if f.get("required")]
        email_fields = [f for f in fields if f.get("type") == "email" or "email" in f.get("name", "").lower()]

        # 1. Test empty required submission
        if required_fields:
            try:
                # Clear all inputs
                for f in fields:
                    try:
                        await page.fill(f["selector"], "")
                    except Exception:
                        pass

                # Monitor if submission occurs (e.g. navigation or network request or page change)
                initial_url = page.url
                submitted = False

                async with page.expect_response(lambda r: r.request.method in ("POST", "PUT"), timeout=1500) as resp_info:
                    try:
                        await page.click(submit_sel, timeout=1000)
                    except Exception:
                        pass
                
                # If a POST response was received with all empty required fields
                if resp_info.value:
                    submitted = True
            except Exception:
                # Timed out waiting for response, which is normal when client-side validation prevents submit
                submitted = False

            if submitted:
                req_names = ", ".join([f.get("name") or f["selector"] for f in required_fields])
                findings.append({
                    "rule_id": "FORM_REQ_EMPTY_SUBMIT",
                    "severity": "HIGH",
                    "confidence": 0.92,
                    "title": "Missing Required Form Validation",
                    "description": f"Form '{form_sel}' submitted to server despite empty required fields: {req_names}.",
                    "page_url": current_url,
                    "selector": form_sel,
                    "category": "Form"
                })

        # 2. Test invalid email acceptance
        if email_fields:
            email_f = email_fields[0]
            try:
                # Fill email with invalid format
                await page.fill(email_f["selector"], "not-a-valid-email")
                
                # Check HTML5 checkValidity
                is_valid = await page.evaluate(f"""
                    () => {{
                        const el = document.querySelector('{email_f["selector"]}');
                        return el ? el.checkValidity() : true;
                    }}
                """)

                if is_valid and email_f.get("type") != "email":
                    findings.append({
                        "rule_id": "FORM_EMAIL_NO_VALIDATION",
                        "severity": "MEDIUM",
                        "confidence": 0.9,
                        "title": "Email Field Lacks Format Validation",
                        "description": f"Input '{email_f['selector']}' appears to be an email field but lacks type='email' or regex pattern validation.",
                        "page_url": current_url,
                        "selector": email_f["selector"],
                        "category": "Form"
                    })
            except Exception:
                pass

        return findings
