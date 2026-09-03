import pytest
from backend.services.ai_advisor import GeminiAdvisor

@pytest.mark.asyncio
async def test_ai_advisor_offline_deterministic_fallback():
    # With no API key or AI disabled, advisor must gracefully return deterministic fallback
    advisor = GeminiAdvisor(api_key=None)
    assert advisor.enabled is False

    finding = {
        "title": "Broken link on /pricing",
        "category": "Navigation",
        "severity": "HIGH",
        "description": "Returns HTTP 404.",
        "selector": "a#pricing-link"
    }

    explanation = await advisor.generate_issue_explanation(finding)
    assert "executive_summary" in explanation
    assert "suspected_root_cause" in explanation
    assert "remediation_suggestion" in explanation
    assert explanation["source"] == "deterministic_rules"
    assert "Navigation" in explanation["executive_summary"]

    scenarios = await advisor.suggest_scenarios_for_page("http://example.com", "<html>...</html>")
    assert len(scenarios) >= 1
    assert "Smoke Test" in scenarios[0]["name"]
