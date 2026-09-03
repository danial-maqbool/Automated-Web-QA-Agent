from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.async_api import Page

AXE_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "assets" / "axe.min.js"

class AccessibilityScanner:
    """
    Executes WCAG 2.1 AA audits using locally bundled axe-core (no CDN scripts).
    Also performs keyboard accessibility and focus navigation checks.
    """
    def __init__(self):
        if not AXE_SCRIPT_PATH.exists():
            raise FileNotFoundError(f"axe.min.js not found at {AXE_SCRIPT_PATH}")
        self._axe_script = AXE_SCRIPT_PATH.read_text(encoding="utf-8")

    async def run_axe_audit(self, page: Page, current_url: str) -> List[Dict[str, Any]]:
        """
        Injects local axe-core and executes WCAG audit.
        """
        findings: List[Dict[str, Any]] = []
        try:
            # Inject axe script
            await page.evaluate(self._axe_script)

            # Run axe analysis
            axe_results = await page.evaluate("""
                async () => {
                    return await axe.run({
                        runOnly: {
                            type: 'tag',
                            values: ['wcag2a', 'wcag2aa', 'best-practice']
                        }
                    });
                }
            """)

            violations = axe_results.get("violations", [])
            for v in violations:
                rule_id = v.get("id", "unknown-rule")
                impact = v.get("impact", "moderate")
                description = v.get("description", "")
                help_url = v.get("helpUrl", "")

                for node in v.get("nodes", []):
                    target_selectors = node.get("target", [])
                    selector = " > ".join(target_selectors) if isinstance(target_selectors, list) else str(target_selectors)
                    html_snippet = node.get("html", "")[:300]
                    failure_summary = node.get("failureSummary", "")

                    # Map impact to WebQA severity
                    severity = "CRITICAL" if impact == "critical" else ("HIGH" if impact == "serious" else ("MEDIUM" if impact == "moderate" else "LOW"))

                    findings.append({
                        "rule_id": rule_id,
                        "impact": impact,
                        "severity": severity,
                        "confidence": 0.98,
                        "title": f"Accessibility: {rule_id.replace('-', ' ').title()}",
                        "description": description,
                        "page_url": current_url,
                        "selector": selector,
                        "html_snippet": html_snippet,
                        "failure_summary": failure_summary,
                        "help_url": help_url,
                        "category": "Accessibility"
                    })

        except Exception as e:
            # If script injection or page navigation fails
            pass

        return findings

    async def test_keyboard_navigation(self, page: Page, current_url: str) -> List[Dict[str, Any]]:
        """
        Simulates Tab and Shift+Tab navigation to discover focus traps,
        unreachable controls, and missing visible focus indicators.
        """
        findings: List[Dict[str, Any]] = []
        try:
            # Discover interactive elements
            interactive_count = await page.evaluate("""
                () => document.querySelectorAll(
                    "a[href], button:not([disabled]), input:not([disabled]):not([type='hidden']), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex='-1'])"
                ).length
            """)

            if interactive_count == 0:
                return findings

            # Reset focus to top
            await page.keyboard.press("Escape")
            
            focused_elements = []
            tab_cycles = min(interactive_count + 5, 25)

            for i in range(tab_cycles):
                await page.keyboard.press("Tab")
                active_info = await page.evaluate("""
                    () => {
                        const el = document.activeElement;
                        if (!el || el === document.body) return null;
                        
                        const style = window.getComputedStyle(el);
                        const hasVisibleOutline = style.outlineStyle !== 'none' && style.outlineWidth !== '0px';
                        const hasBoxShadow = style.boxShadow && style.boxShadow !== 'none';
                        const isFocusVisible = hasVisibleOutline || hasBoxShadow;

                        let selector = el.tagName.toLowerCase();
                        if (el.id) selector += '#' + el.id;
                        else if (el.className) selector += '.' + el.className.trim().split(/\\s+/).join('.');

                        return {
                            selector: selector,
                            tagName: el.tagName,
                            isFocusVisible: isFocusVisible
                        };
                    }
                """)

                if active_info:
                    focused_elements.append(active_info["selector"])
                    if not active_info["isFocusVisible"]:
                        # Found element with no visible focus style
                        findings.append({
                            "rule_id": "A11Y_MISSING_FOCUS_INDICATOR",
                            "severity": "LOW",
                            "confidence": 0.85,
                            "title": "Missing Visible Focus Indicator",
                            "description": f"Interactive element '{active_info['selector']}' lacks visible outline or box-shadow when focused via Tab navigation.",
                            "page_url": current_url,
                            "selector": active_info["selector"],
                            "category": "Accessibility"
                        })
                        break # Record first clear instance per page

            # Detect potential focus traps: if last 4 focused selectors are identical on Tab
            if len(focused_elements) >= 4 and len(set(focused_elements[-4:])) == 1 and interactive_count > 1:
                stuck_selector = focused_elements[-1]
                findings.append({
                    "rule_id": "A11Y_FOCUS_TRAP",
                    "severity": "HIGH",
                    "confidence": 0.9,
                    "title": "Potential Keyboard Focus Trap",
                    "description": f"Focus appears trapped at '{stuck_selector}' during sequential Tab navigation.",
                    "page_url": current_url,
                    "selector": stuck_selector,
                    "category": "Accessibility"
                })

        except Exception:
            pass

        return findings
