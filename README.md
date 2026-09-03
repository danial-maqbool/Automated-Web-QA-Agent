# WebQA Agent

> **Enterprise-Grade Automated Website Quality-Assurance Platform**  
> Inspects websites, executes browser workflows, detects functional and visual defects, collects multimodal evidence, assigns severity, and produces actionable regression reports.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/tested%20with-Playwright-green.svg)](https://playwright.dev/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB.svg)](https://react.dev/)

---

## Highlights

- **Deterministic-First Testing**: 100% functional without external LLM dependencies; optional AI augmentation for exploratory planning and executive defect summaries.
- **Autonomous Crawler & SPA Support**: Discovers routes across standard MPAs and single-page applications (React, Next.js, Vue, Angular) via dynamic DOM extraction and history API monitoring.
- **Safety Classifier**: Hardened guardrails preventing accidental execution of destructive actions (`delete`, `purchase`, `pay`, `cancel`, `transfer`).
- **Comprehensive Quality Modules**:
  - 🔗 **Broken Link & Redirect Checker**
  - ⚠️ **Console & Uncaught Exception Interceptor**
  - 🌐 **Network Diagnostic Monitor** with credential redaction
  - 📝 **Safe Form Testing & Validation Analysis**
  - ♿ **Accessibility Scanner** (locally bundled `axe-core`, WCAG 2.1 AA)
  - 📱 **Responsive & Horizontal Overflow Tester** (7 standard device viewports)
  - 👁️ **Visual Regression Engine** (pixel diffing with baseline management)
  - ⚡ **Performance & Core Web Vitals** (FCP, LCP, CLS, Load Timings)
  - 🔍 **SEO & Metadata Auditor**
  - 🛡️ **Passive Security Checks**
- **Artifact & Evidence Pipeline**: Element-highlighted screenshots, Playwright traces, network HAR logs, and reproducible step-by-step defect logs.
- **Issue Deduplication & Scoring**: Deduplicates recurring errors across hundreds of pages and computes a transparent 100-point **WebQA Project Score**.
- **Modern Web Dashboard**: Real-time run telemetry, interactive site map, network/console inspect tools, and visual diff sliders.
- **CI/CD Quality Gates**: Headless CLI runner with configurable quality thresholds and pipeline exit codes.

---

## Architecture Overview

Refer to [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for full architectural specifications and Mermaid diagrams.

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend development)
- Playwright browser binaries

### Installation

```bash
# Clone the repository
git clone https://github.com/danial-maqbool/Automated-Web-QA-Agent.git
cd Automated-Web-QA-Agent

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Running the Application

```bash
# Start backend and frontend services
python run.py
```

Access the WebQA Dashboard at `http://localhost:8000`.

---

## Safe Testing Commitment
WebQA Agent defaults to non-destructive interactions. Read [`docs/SAFE_TESTING.md`](docs/SAFE_TESTING.md) for details on safety policies, blocked actions, and sensitive data redaction.

---

## License
MIT License. See [LICENSE](LICENSE) for details.
