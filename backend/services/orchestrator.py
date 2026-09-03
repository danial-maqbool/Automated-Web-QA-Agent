import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from backend.database import AsyncSessionLocal
from backend.models import (
    Project, Environment, QARun, Page as PageModel, PageVisit, 
    RunEvent, Screenshot, NetworkRequest, ConsoleMessage, 
    AccessibilityFinding, PerformanceMetric, IgnoreRule
)
from backend.services.browser import browser_manager
from backend.services.crawler import PageCrawler
from backend.services.diagnostics import DiagnosticsRecorder
from backend.services.link_image_checker import LinkChecker, ImageChecker
from backend.services.accessibility import AccessibilityScanner
from backend.services.responsive import ResponsiveTester
from backend.services.form_tester import FormTester
from backend.services.interaction import ExploratoryEngine
from backend.services.evidence import EvidenceCollector
from backend.services.scoring_deduplication import IssueManager, calculate_qa_score
from backend.services.regression_analyzer import RegressionAnalyzer

class QAOrchestrator:
    """
    Coordinates browser execution, page discovery, deterministic testing modules,
    evidence capture, issue normalization, deduplication, and database persistence.
    """
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.cancelled = False
        self.evidence = EvidenceCollector(run_id)

    async def log_event(self, db: AsyncSession, level: str, message: str, url: Optional[str] = None):
        event = RunEvent(
            run_id=self.run_id,
            level=level,
            message=message[:500],
            url=url
        )
        db.add(event)
        await db.flush()

    async def execute_scan(self, project_id: str) -> QARun:
        async with AsyncSessionLocal() as db:
            # Load Run and Project
            run_res = await db.execute(select(QARun).where(QARun.id == self.run_id))
            run = run_res.scalar_one()

            proj_res = await db.execute(
                select(Project)
                .options(selectinload(Project.environments), selectinload(Project.ignore_rules))
                .where(Project.id == project_id)
            )
            project = proj_res.scalar_one()

            # Find target base URL from environment or project
            base_url = project.base_url
            env_name = "Production"
            if run.environment_id:
                for env in project.environments:
                    if env.id == run.environment_id:
                        base_url = env.base_url
                        env_name = env.name
                        break

            # Update Run status to RUNNING
            run.status = "RUNNING"
            run.started_at = datetime.utcnow()
            run.current_url = base_url
            run.current_action = "Initializing browser session"
            await db.commit()

            await self.log_event(db, "INFO", f"QA run started for {project.name} on {base_url} ({run.scan_type})", base_url)
            await db.commit()

        # Limits based on scan_type
        if run.scan_type == "QUICK_SCAN":
            max_pages = 5
            max_depth = 1
        else:
            max_pages = 25
            max_depth = 3

        crawler = PageCrawler(
            base_url=base_url,
            allowed_domains=project.allowed_domains,
            max_depth=max_depth,
            max_pages=max_pages
        )
        crawler.enqueue(base_url, depth=0)

        # Initialize engines
        a11y_scanner = AccessibilityScanner()
        responsive_tester = ResponsiveTester()
        form_tester = FormTester()
        exploratory_engine = ExploratoryEngine(max_actions_per_page=3)

        context = None
        pages_tested = 0
        all_discovered_findings: List[Dict[str, Any]] = []

        try:
            context = await browser_manager.create_context(
                browser_name=run.browser or "chromium",
                headless=True,
                viewport_width=run.viewport_width,
                viewport_height=run.viewport_height,
                enable_tracing=True
            )

            # Discover sitemap URLs if available
            await crawler.fetch_sitemap_urls()

            while crawler.queue and not self.cancelled:
                item = crawler.queue.pop(0)
                current_url = item["url"]
                current_depth = item["depth"]

                if current_url in crawler.visited_urls:
                    continue
                crawler.visited_urls.add(current_url)

                async with AsyncSessionLocal() as db:
                    # Refresh run status check
                    r_check = await db.execute(select(QARun.status).where(QARun.id == self.run_id))
                    current_status = r_check.scalar_one()
                    if current_status == "CANCELLED":
                        self.cancelled = True
                        break

                    # Update run progress
                    r_obj = await db.get(QARun, self.run_id)
                    r_obj.current_url = current_url
                    r_obj.current_action = f"Navigating to {current_url}"
                    r_obj.pages_discovered = len(crawler.discovered_urls)
                    r_obj.pages_tested = pages_tested
                    await self.log_event(db, "INFO", f"Navigated to {current_url}", current_url)
                    await db.commit()

                # Open browser page
                page = await context.new_page()
                diagnostics = DiagnosticsRecorder(page)
                await crawler.attach_spa_route_listener(page)

                t_nav_start = time.time()
                status_code = None
                nav_error = None

                try:
                    resp = await page.goto(current_url, wait_until="domcontentloaded", timeout=20000)
                    if resp:
                        status_code = resp.status
                except Exception as e:
                    nav_error = str(e)

                load_time_ms = round((time.time() - t_nav_start) * 1000.0, 2)
                page_title = await page.title() if not nav_error else "Error"

                # Capture viewport screenshot
                page_screenshot = None
                if not nav_error:
                    page_screenshot = await self.evidence.capture_viewport_screenshot(page, "page_nav")

                # Store or update Page & PageVisit in DB
                async with AsyncSessionLocal() as db:
                    parsed_path = current_url.replace(base_url, "") or "/"
                    page_record_res = await db.execute(
                        select(PageModel).where(
                            PageModel.project_id == project_id,
                            PageModel.url == current_url
                        )
                    )
                    page_record = page_record_res.scalar_one_or_none()
                    if not page_record:
                        page_record = PageModel(
                            project_id=project_id,
                            url=current_url,
                            path=parsed_path,
                            title=page_title,
                            status_code=status_code,
                            load_time_ms=load_time_ms,
                            screenshot_path=page_screenshot,
                            last_tested_at=datetime.utcnow()
                        )
                        db.add(page_record)
                        await db.flush()
                    else:
                        page_record.title = page_title
                        page_record.status_code = status_code
                        page_record.load_time_ms = load_time_ms
                        page_record.screenshot_path = page_screenshot
                        page_record.last_tested_at = datetime.utcnow()

                    page_visit = PageVisit(
                        run_id=self.run_id,
                        page_id=page_record.id,
                        url=current_url,
                        status_code=status_code,
                        title=page_title,
                        load_time_ms=load_time_ms,
                        depth=current_depth,
                        screenshot_path=page_screenshot
                    )
                    db.add(page_visit)
                    await db.commit()
                    page_visit_id = page_visit.id

                pages_tested += 1

                if nav_error:
                    # Navigation / Link error
                    all_discovered_findings.append({
                        "category": "Navigation",
                        "rule_id": "LINK_CONN_FAILED",
                        "title": f"Navigation Failed: {current_url}",
                        "severity": "CRITICAL",
                        "confidence": 1.0,
                        "description": f"Failed to navigate to page: {nav_error}",
                        "page_url": current_url
                    })
                    await page.close()
                    continue

                # 1. Discover child links
                await crawler.discover_page_links(page, current_url, current_depth)
                await crawler.collect_spa_routes(page, current_url, current_depth)

                # 2. Link & Image Checks
                link_checker = LinkChecker(base_url=base_url)
                broken_links = await link_checker.check_links_on_page(page, current_url)
                all_discovered_findings.extend(broken_links)

                image_checker = ImageChecker()
                broken_images = await image_checker.inspect_images(page, current_url)
                all_discovered_findings.extend(broken_images)

                # 3. Accessibility Scan (local axe-core)
                a11y_findings = await a11y_scanner.run_axe_audit(page, current_url)
                all_discovered_findings.extend(a11y_findings)

                # 4. Content Quality & SEO Checks
                page_html = await page.content()
                soup = BeautifulSoup(page_html, "html.parser")
                
                # Check SEO Title & Description
                if not soup.title or not soup.title.get_text().strip():
                    all_discovered_findings.append({
                        "category": "SEO",
                        "rule_id": "SEO_MISSING_TITLE",
                        "title": "Missing Page Title",
                        "severity": "LOW",
                        "confidence": 1.0,
                        "description": "The page lacks a descriptive <title> tag.",
                        "page_url": current_url
                    })

                # Check Content Defects: placeholder or raw stack traces
                body_text = soup.get_text()
                if "lorem ipsum" in body_text.lower():
                    all_discovered_findings.append({
                        "category": "Content",
                        "rule_id": "CONTENT_LOREM_IPSUM",
                        "title": "Placeholder Lorem Ipsum Text Found",
                        "severity": "LOW",
                        "confidence": 0.95,
                        "description": "Page contains placeholder 'Lorem ipsum' filler copy.",
                        "page_url": current_url
                    })

                if any(x in body_text for x in ("Traceback (most recent call last)", "NullPointerException", "Unhandled Rejection")):
                    all_discovered_findings.append({
                        "category": "Content",
                        "rule_id": "CONTENT_EXPOSED_STACK_TRACE",
                        "title": "Raw Stack Trace Exposed in UI",
                        "severity": "CRITICAL",
                        "confidence": 0.98,
                        "description": "An unhandled application stack trace or internal error was rendered directly in the user interface.",
                        "page_url": current_url
                    })

                # 5. Responsive Checks (on mobile viewport)
                mobile_findings = await responsive_tester.detect_horizontal_overflow(
                    page, current_url, {"name": "Mobile", "width": 390, "height": 844}
                )
                all_discovered_findings.extend(mobile_findings)

                # 6. Form Testing
                forms = await form_tester.discover_forms(page)
                for f_data in forms:
                    f_issues = await form_tester.test_form_validation(page, current_url, f_data)
                    all_discovered_findings.extend(f_issues)

                # 7. Exploratory Button Interactions
                btn_issues, _ = await exploratory_engine.test_safe_buttons_and_interactions(page, current_url)
                all_discovered_findings.extend(btn_issues)

                # 8. Console and Network Diagnostics
                console_errs = diagnostics.get_deduplicated_console_errors()
                for ce in console_errs:
                    all_discovered_findings.append({
                        "category": "Console",
                        "rule_id": "CONSOLE_UNCAUGHT_ERR" if ce["type"] == "error" else "CONSOLE_WARNING",
                        "title": f"Console Error: {ce['text'][:60]}",
                        "severity": "HIGH",
                        "confidence": 0.95,
                        "description": f"Browser console recorded: {ce['text']} at {ce['location']}",
                        "page_url": current_url,
                        "console_evidence": ce
                    })

                net_failures = diagnostics.get_grouped_network_failures()
                for nf in net_failures:
                    st = nf.get("status_code")
                    all_discovered_findings.append({
                        "category": "Network",
                        "rule_id": f"NET_STATUS_{st}" if st else "NET_REQUEST_FAILED",
                        "severity": "CRITICAL" if (st and st >= 500) else "HIGH",
                        "confidence": 1.0,
                        "title": f"Network Failure: {nf['method']} {nf['url'][:60]}",
                        "description": f"Request to '{nf['url']}' failed with {nf['failure_reason']}",
                        "page_url": current_url,
                        "network_evidence": nf
                    })

                # Persist evidence to database for this PageVisit
                async with AsyncSessionLocal() as db:
                    for ce in diagnostics.console_logs:
                        db.add(ConsoleMessage(
                            page_visit_id=page_visit_id,
                            message_type=ce["type"],
                            text=ce["text"],
                            location=ce["location"]
                        ))
                    for nr in diagnostics.network_records:
                        db.add(NetworkRequest(
                            page_visit_id=page_visit_id,
                            method=nr["method"],
                            url=nr["url"],
                            resource_type=nr["resource_type"],
                            status_code=nr["status_code"],
                            duration_ms=nr["duration_ms"],
                            size_bytes=nr["size_bytes"],
                            failed=nr["failed"],
                            failure_reason=nr["failure_reason"]
                        ))
                    for a11y in a11y_findings:
                        db.add(AccessibilityFinding(
                            page_visit_id=page_visit_id,
                            rule_id=a11y["rule_id"],
                            impact=a11y["impact"],
                            description=a11y["description"],
                            selector=a11y.get("selector"),
                            html_snippet=a11y.get("html_snippet")
                        ))
                    db.add(PerformanceMetric(
                        page_visit_id=page_visit_id,
                        load_time_ms=load_time_ms,
                        request_count=len(diagnostics.network_records),
                        transfer_size_bytes=sum([nr["size_bytes"] for nr in diagnostics.network_records])
                    ))
                    await db.commit()

                await page.close()

            # Trace archive save
            trace_path = self.evidence.get_trace_path()
            await browser_manager.close_context(context, trace_save_path=trace_path)
            context = None

            # Process, deduplicate, and score findings
            async with AsyncSessionLocal() as db:
                p_rules_res = await db.execute(select(IgnoreRule).where(IgnoreRule.project_id == project_id))
                ignore_rules = p_rules_res.scalars().all()

                crit_count = 0
                high_count = 0
                med_count = 0
                low_count = 0
                info_count = 0

                for finding in all_discovered_findings:
                    finding["environment_name"] = env_name
                    finding["browser"] = run.browser
                    finding["viewport"] = f"{run.viewport_width}x{run.viewport_height}"
                    
                    # Highlight screenshot for finding if available
                    if not finding.get("screenshot_path") and page_screenshot:
                        finding["screenshot_path"] = page_screenshot

                    issue, is_new = await IssueManager.record_finding(
                        db=db,
                        project_id=project_id,
                        run_id=self.run_id,
                        finding=finding,
                        ignore_rules=ignore_rules
                    )

                    sev = issue.severity.upper()
                    if sev == "CRITICAL":
                        crit_count += 1
                    elif sev == "HIGH":
                        high_count += 1
                    elif sev == "MEDIUM":
                        med_count += 1
                    elif sev == "LOW":
                        low_count += 1
                    else:
                        info_count += 1

                await db.commit()

                # Calculate final QA score
                qa_score = calculate_qa_score(
                    critical=crit_count,
                    high=high_count,
                    medium=med_count,
                    low=low_count,
                    info=info_count
                )

                # Finalize run
                run_obj = await db.get(QARun, self.run_id)
                run_obj.status = "CANCELLED" if self.cancelled else "COMPLETED"
                run_obj.completed_at = datetime.utcnow()
                run_obj.pages_tested = pages_tested
                run_obj.total_issues = len(all_discovered_findings)
                run_obj.critical_issues = crit_count
                run_obj.high_issues = high_count
                run_obj.medium_issues = med_count
                run_obj.low_issues = low_count
                run_obj.info_issues = info_count
                run_obj.qa_score = qa_score
                run_obj.current_action = "Scan finished"

                await db.commit()

                # Run regression analysis
                await RegressionAnalyzer.analyze_run_regression(db, project_id, self.run_id)
                await db.commit()

                await self.log_event(db, "SUCCESS", f"QA scan completed. Score: {qa_score}/100. Issues: {len(all_discovered_findings)}")
                await db.commit()

                return run_obj

        except Exception as e:
            if context:
                await browser_manager.close_context(context)
            async with AsyncSessionLocal() as db:
                run_obj = await db.get(QARun, self.run_id)
                run_obj.status = "FAILED"
                run_obj.error_message = str(e)
                run_obj.completed_at = datetime.utcnow()
                await self.log_event(db, "ERROR", f"Run failed with exception: {str(e)}")
                await db.commit()
                return run_obj
