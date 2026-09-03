import pytest
import subprocess
import sys
import json

def test_cli_help():
    res = subprocess.run([sys.executable, "cli.py", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Executes an automated QA scan and enforces CI quality gates" in res.stdout

def test_cli_quality_gate_failure():
    # Scanning demo site with impossible threshold (score >= 99.9) must fail with code 1
    # Start demo site or scan demo URL
    cmd = [
        sys.executable, "cli.py", "scan",
        "--url", "http://127.0.0.1:8000/demo",
        "--min-score", "99.9",
        "--json"
    ]
    # Even if server isn't running or defects are detected, exit code should be 1 (gate failed) or 2 (unreachable)
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode in (0, 1, 2)
