import pytest
from backend.services.interaction import classify_action, InteractionGraph, ExploratoryEngine
from backend.services.browser import BrowserManager

def test_classify_action_safety():
    # Blocked actions
    assert classify_action({"text": "Delete Account", "id": "btn-del"}) == "BLOCKED"
    assert classify_action({"text": "Pay Now ($99)", "id": "pay-btn"}) == "BLOCKED"
    assert classify_action({"text": "Cancel Subscription"}) == "BLOCKED"
    assert classify_action({"text": "Deploy to Production"}) == "BLOCKED"
    assert classify_action({"text": "Transfer Funds"}) == "BLOCKED"

    # Caution actions
    assert classify_action({"text": "Submit Feedback"}) == "CAUTION"
    assert classify_action({"text": "Submit Feedback"}, allow_caution=True) == "SAFE"

    # Safe actions
    assert classify_action({"text": "View Details"}) == "SAFE"
    assert classify_action({"text": "Next Page"}) == "SAFE"
    assert classify_action({"text": "Sort by Price"}) == "SAFE"
    assert classify_action({"text": "Expand FAQ"}) == "SAFE"

def test_interaction_graph_reproduction_steps():
    graph = InteractionGraph()
    
    # State 1: Home
    graph.add_state("state_home", "https://example.com/", "Home")
    assert graph.get_reproduction_steps("state_home") == [
        {"action": "navigate", "target": "https://example.com/"}
    ]

    # State 2: Pricing reached via click
    action1 = {"action": "click", "target": "a#nav-pricing", "text": "Pricing"}
    graph.add_state("state_pricing", "https://example.com/pricing", "Pricing", parent_state_id="state_home", action=action1)

    steps = graph.get_reproduction_steps("state_pricing")
    assert len(steps) == 2
    assert steps[0]["action"] == "navigate"
    assert steps[1]["target"] == "a#nav-pricing"

@pytest.mark.asyncio
async def test_exploratory_engine_dead_button():
    mgr = BrowserManager()
    try:
        ctx = await mgr.create_context(headless=True)
        page = await ctx.new_page()

        await page.set_content("""
            <!DOCTYPE html>
            <html>
                <body>
                    <!-- Dead button that does nothing -->
                    <button id="btn-dead">Click Me (Dead Button)</button>
                    <!-- Destructive button that must be ignored -->
                    <button id="btn-delete">Delete Everything</button>
                </body>
            </html>
        """)

        engine = ExploratoryEngine(max_actions_per_page=3)
        findings, actions = await engine.test_safe_buttons_and_interactions(page, "http://test/")

        # Verify destructive button was NOT clicked
        clicked_selectors = [a["target"] for a in actions]
        assert "#btn-delete" not in clicked_selectors
        assert "#btn-dead" in clicked_selectors

        # Verify dead button finding was raised
        assert any(f["rule_id"] == "BTN_NO_RESPONSE" for f in findings)

        await page.close()
        await mgr.close_context(ctx)
    finally:
        await mgr.shutdown()
