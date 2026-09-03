import time
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from playwright.async_api import Page

BLOCKED_KEYWORDS = {
    "delete", "remove", "destroy", "drop", "terminate", "deactivate",
    "pay", "purchase", "buy", "checkout", "charge", "order",
    "subscribe", "cancel subscription", "publish", "deploy", "transfer"
}

CAUTION_KEYWORDS = {
    "send", "submit", "post", "invite", "reset password", "modify", "save changes"
}

def classify_action(el_data: Dict[str, Any], allow_caution: bool = False) -> str:
    """
    Classifies a proposed browser action as SAFE, CAUTION, or BLOCKED.
    Inspects text, aria-label, attributes, and context.
    """
    tokens = " ".join([
        el_data.get("text", ""),
        el_data.get("aria_label", ""),
        el_data.get("title", ""),
        el_data.get("id", ""),
        el_data.get("data_testid", ""),
        el_data.get("action_url", ""),
        el_data.get("role", "")
    ]).lower()

    # Check blocked keywords first
    for kw in BLOCKED_KEYWORDS:
        if kw in tokens:
            return "BLOCKED"

    # Check caution keywords
    for kw in CAUTION_KEYWORDS:
        if kw in tokens:
            return "SAFE" if allow_caution else "CAUTION"

    return "SAFE"

class InteractionGraph:
    """
    Maintains a directed graph of application states and transitions
    for generating reproducible defect steps.
    """
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {} # state_id -> state_metadata
        self.edges: List[Dict[str, Any]] = [] # [{from, to, action}]
        self.paths_to_states: Dict[str, List[Dict[str, Any]]] = {}

    def add_state(self, state_id: str, url: str, title: str, parent_state_id: Optional[str] = None, action: Optional[Dict[str, Any]] = None):
        if state_id not in self.nodes:
            self.nodes[state_id] = {
                "id": state_id,
                "url": url,
                "title": title,
                "discovered_at": time.time()
            }
            if parent_state_id and action:
                self.edges.append({
                    "from": parent_state_id,
                    "to": state_id,
                    "action": action
                })
                parent_path = self.paths_to_states.get(parent_state_id, [])
                self.paths_to_states[state_id] = parent_path + [action]
            else:
                self.paths_to_states[state_id] = [{"action": "navigate", "target": url}]

    def get_reproduction_steps(self, state_id: str) -> List[Dict[str, Any]]:
        return self.paths_to_states.get(state_id, [])

class ExploratoryEngine:
    """
    Autonomous explorer that safely exercises interactive interface controls
    and discovers dead buttons or state defects.
    """
    def __init__(self, max_actions_per_page: int = 5, allow_caution: bool = False):
        self.max_actions_per_page = max_actions_per_page
        self.allow_caution = allow_caution
        self.explored_actions: Set[str] = set()

    async def discover_interactive_elements(self, page: Page) -> List[Dict[str, Any]]:
        """
        Finds all clickable controls (buttons, tabs, accordions) and extracts metadata.
        """
        return await page.evaluate("""
            () => {
                const selector = 'button, [role="button"], [role="tab"], summary, .btn';
                const elements = Array.from(document.querySelectorAll(selector));

                return elements.map((el, i) => {
                    const style = window.getComputedStyle(el);
                    const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                    const isEnabled = !el.disabled && !el.hasAttribute('disabled');

                    let sel = '';
                    if (el.id) sel = '#' + el.id;
                    else if (el.className && typeof el.className === 'string') {
                        sel = '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.');
                    } else {
                        sel = el.tagName.toLowerCase() + ':nth-of-type(' + (i + 1) + ')';
                    }

                    return {
                        selector: sel,
                        text: el.innerText.trim().slice(0, 100),
                        aria_label: el.getAttribute('aria-label') || '',
                        title: el.getAttribute('title') || '',
                        id: el.id || '',
                        data_testid: el.getAttribute('data-testid') || '',
                        role: el.getAttribute('role') || el.tagName.toLowerCase(),
                        isVisible: isVisible,
                        isEnabled: isEnabled
                    };
                }).filter(el => el.isVisible && el.isEnabled);
            }
        """)

    async def test_safe_buttons_and_interactions(
        self,
        page: Page,
        current_url: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Explores safe buttons and flags dead buttons or defects.
        Returns (findings, executed_actions).
        """
        findings = []
        executed_actions = []

        elements = await self.discover_interactive_elements(page)
        action_count = 0

        for el in elements:
            if action_count >= self.max_actions_per_page:
                break

            classification = classify_action(el, self.allow_caution)
            if classification != "SAFE":
                continue

            sel = el.get("selector")
            action_sig = f"{current_url}_{sel}"
            if action_sig in self.explored_actions:
                continue

            self.explored_actions.add(action_sig)

            # Record pre-interaction state snapshot
            initial_dom_hash = await page.evaluate("() => document.body.innerHTML.length")
            initial_url = page.url

            # Execute safe click
            try:
                action_count += 1
                executed_actions.append({
                    "action": "click",
                    "target": sel,
                    "text": el.get("text")
                })

                await page.locator(sel).first.click(timeout=2500, no_wait_after=True)
                await page.wait_for_timeout(300)

                # Check post-interaction state
                post_dom_hash = await page.evaluate("() => document.body.innerHTML.length")
                post_url = page.url

                # Dead button check: no URL change, no DOM change, button text implies action
                text_lower = el.get("text", "").lower()
                if (
                    initial_url == post_url and
                    initial_dom_hash == post_dom_hash and
                    len(text_lower) > 2 and
                    not any(x in text_lower for x in ("close", "cancel", "dismiss"))
                ):
                    findings.append({
                        "rule_id": "BTN_NO_RESPONSE",
                        "severity": "LOW",
                        "confidence": 0.8,
                        "title": "Interactive Control Produces No State Change",
                        "description": f"Clicking active button '{sel}' ('{el.get('text')}') resulted in no DOM mutation, navigation, or visible UI update.",
                        "page_url": current_url,
                        "selector": sel,
                        "category": "Functional"
                    })

            except Exception:
                pass

        return findings, executed_actions
