import os
import json
from typing import Dict, Any, List, Optional
import httpx
from backend.config import settings

class GeminiAdvisor:
    """
    Optional AI-assisted quality advisor powered by Google Gemini.
    Strictly optional: If GEMINI_API_KEY is missing or AI_ENABLED is False,
    falls back cleanly to deterministic heuristic recommendations without runtime error.
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model = model or settings.GEMINI_MODEL or "gemini-2.5-flash"
        self.enabled = bool(settings.AI_ENABLED and self.api_key)

    async def generate_issue_explanation(self, issue: Dict[str, Any]) -> Dict[str, str]:
        """
        Generates executive summary, root cause hypothesis, and engineer remediation steps.
        """
        category = issue.get("category", "Functional")
        title = issue.get("title", "")
        desc = issue.get("description", "")
        selector = issue.get("selector", "")
        observed = issue.get("observed_behavior", "")

        # Fallback deterministic explanation if AI disabled or offline
        fallback = {
            "executive_summary": f"Detected a {issue.get('severity', 'MEDIUM')} priority {category} defect: {title}.",
            "suspected_root_cause": f"Observed unexpected behavior at selector '{selector or 'DOM root'}'. May be caused by missing client-side validation, broken endpoint route, or unhandled null reference.",
            "remediation_suggestion": "Inspect server response logs, verify HTML input attributes, and ensure robust client-side error boundary handling.",
            "source": "deterministic_rules"
        }

        if not self.enabled:
            return fallback

        prompt = f"""You are an expert QA Engineer. Analyze this detected website defect:
Category: {category}
Title: {title}
Description: {desc}
Selector: {selector}
Observed: {observed}

Return a valid JSON object with keys:
"executive_summary": concise 1-sentence impact explanation for stakeholders
"suspected_root_cause": likely underlying code cause
"remediation_suggestion": actionable instructions for the engineering team
"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text)
                    parsed["source"] = "gemini_ai"
                    return parsed
        except Exception:
            pass

        return fallback

    async def suggest_scenarios_for_page(self, page_url: str, html_summary: str) -> List[Dict[str, Any]]:
        """
        Suggests candidate automated test scenarios based on page structure.
        """
        fallback_scenarios = [
            {
                "name": f"Smoke Test: {page_url}",
                "description": "Verifies title, basic text, and lack of console errors.",
                "steps": [
                    {"action_type": "navigate", "target": page_url},
                    {"action_type": "assert_no_console_errors"},
                    {"action_type": "assert_no_failed_requests"}
                ]
            }
        ]

        if not self.enabled:
            return fallback_scenarios

        prompt = f"""Given this web page URL: {page_url} and structure snippet:
{html_summary[:2000]}

Suggest 2 critical automated test scenarios. Return JSON array of objects with keys:
"name", "description", "steps" (each step with action_type, target, value, expected_value).
"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"}
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text)
        except Exception:
            pass

        return fallback_scenarios
