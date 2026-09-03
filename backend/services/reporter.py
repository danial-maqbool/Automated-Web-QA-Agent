import io
import csv
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from backend.config import DATA_DIR

def format_issue_markdown(issue: Dict[str, Any]) -> str:
    """
    Formats a detected issue into GitHub/JIRA-compatible Markdown.
    """
    steps = issue.get("reproduction_steps") or []
    steps_md = "\n".join([
        f"{idx+1}. {s.get('action', '').capitalize()} {s.get('target', '')} {s.get('value', '')}"
        for idx, s in enumerate(steps)
    ]) if steps else "1. Navigate to " + issue.get("page_url", "")

    return f"""### [{issue.get('category', 'Functional')}] {issue.get('title', 'Detected Defect')}

**Environment:** {issue.get('environment_name', 'Production')}  
**Severity:** `{issue.get('severity', 'MEDIUM')}` | **Confidence:** `{round(issue.get('confidence', 1.0), 2)}` | **Status:** `{issue.get('status', 'OPEN')}`  
**Page URL:** {issue.get('page_url', '')}  
**Selector:** `{issue.get('selector') or 'N/A'}`  

#### Description
{issue.get('description', '')}

#### Steps to Reproduce
{steps_md}

#### Expected Behavior
{issue.get('expected_behavior') or 'Interface should function predictably without error.'}

#### Observed Behavior
{issue.get('observed_behavior') or issue.get('description', '')}

#### Evidence & Diagnostic Context
- **Browser / Viewport:** {issue.get('browser', 'chromium')} / {issue.get('viewport', '1920x1080')}
- **Occurrence Count:** {issue.get('occurrence_count', 1)}
- **Affected Pages:** {issue.get('affected_pages_count', 1)}
- **Screenshot Path:** `{issue.get('screenshot_path') or 'None'}`
"""

class QAReporter:
    """
    Generates structured HTML, JSON, and CSV quality reports.
    """
    @staticmethod
    def generate_json_report(report_data: Dict[str, Any]) -> str:
        return json.dumps(report_data, indent=2, default=str)

    @staticmethod
    def generate_csv_report(issues: List[Dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Title", "Category", "Severity", "Confidence", "Status",
            "Page URL", "Selector", "Occurrences", "First Detected", "Description"
        ])

        for iss in issues:
            writer.writerow([
                iss.get("id", ""),
                iss.get("title", ""),
                iss.get("category", ""),
                iss.get("severity", ""),
                iss.get("confidence", ""),
                iss.get("status", ""),
                iss.get("page_url", ""),
                iss.get("selector", ""),
                iss.get("occurrence_count", 1),
                iss.get("first_detected_at", ""),
                iss.get("description", "")
            ])

        return output.getvalue()

    @staticmethod
    def generate_html_report(report: Dict[str, Any]) -> str:
        score = report.get("qa_score", 100.0)
        grade = "A+" if score >= 95 else ("A" if score >= 90 else ("B" if score >= 80 else ("C" if score >= 70 else ("D" if score >= 60 else "F"))))
        grade_color = "#16a34a" if score >= 80 else ("#d97706" if score >= 60 else "#dc2626")

        issues_html = ""
        for iss in report.get("issues", []):
            sev = iss.get("severity", "MEDIUM")
            badge_color = "#dc2626" if sev == "CRITICAL" else ("#ea580c" if sev == "HIGH" else ("#d97706" if sev == "MEDIUM" else "#2563eb"))
            
            issues_html += f"""
            <div class="issue-card">
              <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                  <span class="badge" style="background-color: {badge_color}; color:white;">{sev}</span>
                  <span class="badge" style="background-color: #f1f5f9; color:#475569; margin-left:0.5rem;">{iss.get('category', 'Functional')}</span>
                  <h3 style="margin-top:0.5rem; margin-bottom:0.25rem;">{iss.get('title', '')}</h3>
                  <p style="color:#64748b; font-size:0.875rem;">URL: <code>{iss.get('page_url', '')}</code></p>
                </div>
                <div style="text-align:right; font-size:0.875rem; color:#64748b;">
                  <div>Confidence: <strong>{round(iss.get('confidence', 1.0)*100)}%</strong></div>
                  <div>Occurrences: <strong>{iss.get('occurrence_count', 1)}</strong></div>
                </div>
              </div>
              <p style="margin-top:0.75rem; color:#334155;">{iss.get('description', '')}</p>
            </div>
            """

        recs_html = "".join([f"<li>{r}</li>" for r in report.get("recommendations", ["Ensure all critical defects are resolved prior to release."])])

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>WebQA Report - {report.get('project_name', 'Project')}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#f8fafc; color:#0f172a; margin:0; padding:2rem; }}
    .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
    header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f5f9; padding-bottom: 1.5rem; margin-bottom: 2rem; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem; text-align: center; }}
    .kpi-num {{ font-size: 2rem; font-weight: 700; color: #0f172a; margin-top: 0.25rem; }}
    .issue-card {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; background: #ffffff; }}
    .badge {{ font-size: 0.75rem; font-weight: 700; padding: 0.25rem 0.6rem; border-radius: 9999px; text-transform: uppercase; display: inline-block; }}
    @media print {{ body {{ background: white; padding: 0; }} .container {{ box-shadow: none; border: none; padding: 0; }} }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1 style="margin:0; font-size: 1.75rem;">WebQA Audit Report</h1>
        <p style="margin:0.25rem 0 0 0; color:#64748b;">Project: <strong>{report.get('project_name', '')}</strong> | Environment: <strong>{report.get('environment', 'Production')}</strong></p>
        <p style="margin:0.25rem 0 0 0; color:#94a3b8; font-size:0.875rem;">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
      </div>
      <div style="text-align:center; padding: 1rem 1.5rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
        <div style="font-size:0.875rem; color:#64748b; font-weight:600;">WebQA Score</div>
        <div style="font-size:2.5rem; font-weight:800; color:{grade_color};">{score}</div>
        <div style="font-weight:700; color:{grade_color};">Grade: {grade}</div>
      </div>
    </header>

    <h2>Executive Overview</h2>
    <div class="kpi-grid">
      <div class="kpi-card">
        <div style="font-size:0.875rem; color:#64748b;">Pages Tested</div>
        <div class="kpi-num">{report.get('total_pages_tested', 0)}</div>
      </div>
      <div class="kpi-card">
        <div style="font-size:0.875rem; color:#64748b;">Total Issues</div>
        <div class="kpi-num" style="color: #dc2626;">{report.get('total_issues_found', 0)}</div>
      </div>
      <div class="kpi-card">
        <div style="font-size:0.875rem; color:#64748b;">Critical / High</div>
        <div class="kpi-num" style="color: #ea580c;">{report.get('critical_issues_count', 0) + report.get('high_issues_count', 0)}</div>
      </div>
      <div class="kpi-card">
        <div style="font-size:0.875rem; color:#64748b;">Accessibility</div>
        <div class="kpi-num">{report.get('accessibility_count', 0)}</div>
      </div>
    </div>

    <h2>Defect Inventory</h2>
    {issues_html or "<p style='color:#16a34a; font-weight:600;'>No defects detected! All automated checks passed.</p>"}

    <h2 style="margin-top:2rem;">Quality Remediation Recommendations</h2>
    <ul style="line-height:1.8; color:#334155;">
      {recs_html}
    </ul>
  </div>
</body>
</html>"""
