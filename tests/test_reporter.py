import pytest
import json
from backend.services.reporter import format_issue_markdown, QAReporter

def test_format_issue_markdown():
    issue = {
        "title": "Broken link on /pricing",
        "category": "Navigation",
        "severity": "HIGH",
        "confidence": 0.95,
        "status": "OPEN",
        "page_url": "https://example.com/pricing",
        "selector": "a#missing-link",
        "description": "Returns HTTP 404.",
        "reproduction_steps": [
            {"action": "navigate", "target": "https://example.com/pricing"},
            {"action": "click", "target": "a#missing-link"}
        ]
    }

    md = format_issue_markdown(issue)
    assert "[Navigation] Broken link on /pricing" in md
    assert "**Severity:** `HIGH`" in md
    assert "1. Navigate https://example.com/pricing" in md
    assert "2. Click a#missing-link" in md

def test_json_and_csv_reports():
    issues = [
        {
            "id": "iss-1",
            "title": "Broken Link",
            "category": "Navigation",
            "severity": "HIGH",
            "confidence": 1.0,
            "status": "OPEN",
            "page_url": "http://test/a",
            "description": "404 Not Found"
        }
    ]
    report_data = {
        "project_name": "Test Site",
        "qa_score": 90.0,
        "issues": issues
    }

    # JSON report
    json_str = QAReporter.generate_json_report(report_data)
    parsed = json.loads(json_str)
    assert parsed["project_name"] == "Test Site"
    assert parsed["qa_score"] == 90.0

    # CSV report
    csv_str = QAReporter.generate_csv_report(issues)
    assert "Broken Link" in csv_str
    assert "Navigation" in csv_str
    assert "http://test/a" in csv_str

def test_html_report():
    report_data = {
        "project_name": "Production App",
        "environment": "Staging",
        "qa_score": 85.0,
        "total_pages_tested": 15,
        "total_issues_found": 3,
        "critical_issues_count": 0,
        "high_issues_count": 1,
        "accessibility_count": 2,
        "issues": [
            {
                "title": "Missing alt on logo",
                "category": "Accessibility",
                "severity": "LOW",
                "confidence": 0.95,
                "page_url": "http://test/logo",
                "description": "Image lacks alt tag"
            }
        ]
    }

    html = QAReporter.generate_html_report(report_data)
    assert "WebQA Audit Report" in html
    assert "Production App" in html
    assert "85" in html
    assert "Missing alt on logo" in html
