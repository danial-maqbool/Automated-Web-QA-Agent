import pytest
from pathlib import Path
from PIL import Image, ImageDraw
from backend.services.visual_regression import compare_screenshots, DOMRegressionAnalyzer

def test_visual_regression_identical_images(tmp_path):
    img_a = tmp_path / "baseline.png"
    img_b = tmp_path / "current.png"
    diff_out = tmp_path / "diff.png"

    # Create identical images
    img1 = Image.new("RGB", (200, 200), (37, 99, 235))
    img1.save(img_a)
    img1.save(img_b)

    passed, diff_count, diff_pct = compare_screenshots(img_a, img_b, diff_out)
    assert passed is True
    assert diff_count == 0
    assert diff_pct == 0.0

def test_visual_regression_altered_images(tmp_path):
    img_a = tmp_path / "baseline.png"
    img_b = tmp_path / "current.png"
    diff_out = tmp_path / "diff.png"

    # Baseline: blue background
    img1 = Image.new("RGB", (200, 200), (37, 99, 235))
    img1.save(img_a)

    # Current: altered with a red box in the center (50x50 = 2500 pixels)
    img2 = Image.new("RGB", (200, 200), (37, 99, 235))
    draw = ImageDraw.Draw(img2)
    draw.rectangle([50, 50, 100, 100], fill=(220, 38, 38))
    img2.save(img_b)

    passed, diff_count, diff_pct = compare_screenshots(img_a, img_b, diff_out, pixel_threshold_pct=1.0)
    assert passed is False
    assert diff_count > 2000
    assert diff_pct > 5.0
    assert diff_out.exists()

def test_dom_regression_analysis():
    html_baseline = """
        <html>
            <nav><a href="/">Home</a><a href="/pricing">Pricing</a></nav>
            <h1>Main Title</h1>
            <button id="btn-save">Save</button>
            <button id="btn-submit">Submit</button>
        </html>
    """
    html_current = """
        <html>
            <nav><a href="/">Home</a></nav> <!-- Missing /pricing link -->
            <h2>Sub Title</h2> <!-- Missing H1 -->
            <button id="btn-submit">Submit</button> <!-- Missing btn-save -->
        </html>
    """

    skel_base = DOMRegressionAnalyzer.extract_dom_skeleton(html_baseline)
    skel_curr = DOMRegressionAnalyzer.extract_dom_skeleton(html_current)

    findings = DOMRegressionAnalyzer.compare_skeletons(skel_base, skel_curr)
    rule_ids = [f["rule_id"] for f in findings]

    assert "DOM_MISSING_HEADING" in rule_ids
    assert "DOM_MISSING_BUTTON" in rule_ids
    assert "DOM_MISSING_NAV" in rule_ids
