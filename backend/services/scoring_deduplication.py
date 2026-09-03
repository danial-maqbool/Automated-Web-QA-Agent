import hashlib
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.models import Issue, IssueOccurrence, IgnoreRule

def normalize_text_for_fingerprint(text: str) -> str:
    """
    Removes ephemeral IDs, timestamps, line numbers, and hex addresses
    so identical errors on different runs generate stable fingerprints.
    """
    if not text:
        return ""
    # Strip hex addresses like 0x1234abcd
    s = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", text)
    # Strip UUIDs
    s = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "UUID", s)
    # Strip line & column numbers like :42:15
    s = re.sub(r":\d+:\d+", ":LINE", s)
    # Strip query string timestamps
    s = re.sub(r"([?&](?:t|_|v|timestamp)=\d+)", "", s)
    return s.strip().lower()

def generate_issue_fingerprint(
    category: str,
    rule_id: str,
    title: str,
    selector: Optional[str] = None,
    target_url: Optional[str] = None
) -> str:
    """
    Generates a deterministic 16-character SHA-256 fingerprint for deduplicating recurring defects.
    """
    norm_cat = category.strip().lower()
    norm_rule = rule_id.strip().lower()
    norm_title = normalize_text_for_fingerprint(title)
    norm_sel = normalize_text_for_fingerprint(selector or "")
    norm_target = normalize_text_for_fingerprint(target_url or "")

    raw_signature = f"{norm_cat}|{norm_rule}|{norm_title}|{norm_sel}|{norm_target}"
    return hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()[:16]

def calculate_qa_score(critical: int, high: int, medium: int, low: int, info: int = 0) -> float:
    """
    Computes transparent WebQA Project Score (0 to 100):
    Score = max(0, 100 - (25*crit + 10*high + 4*med + 1*low))
    """
    deduction = (25 * critical) + (10 * high) + (4 * medium) + (1 * low)
    score = max(0.0, min(100.0, 100.0 - float(deduction)))
    return round(score, 1)

def should_ignore_issue(finding: Dict[str, Any], ignore_rules: List[IgnoreRule]) -> Optional[str]:
    """
    Evaluates finding against active project ignore rules.
    Returns the ignore reason if matched, otherwise None.
    """
    for rule in ignore_rules:
        if not rule.is_active:
            continue
        rtype = rule.rule_type.lower()
        pattern = rule.pattern

        try:
            if rtype == "rule_id" and pattern.lower() == finding.get("rule_id", "").lower():
                return f"Ignored by rule_id: {pattern}"
            if rtype == "url_regex" and re.search(pattern, finding.get("page_url", ""), re.IGNORECASE):
                return f"Ignored by url_regex: {pattern}"
            if rtype == "selector" and finding.get("selector") and pattern in finding.get("selector"):
                return f"Ignored by selector: {pattern}"
            if rtype == "console_regex" and re.search(pattern, finding.get("description", ""), re.IGNORECASE):
                return f"Ignored by console_regex: {pattern}"
        except re.error:
            continue

    return None

class IssueManager:
    """
    Handles issue creation, deduplication across pages, fingerprinting, and status transitions.
    """
    @staticmethod
    async def record_finding(
        db: AsyncSession,
        project_id: str,
        run_id: str,
        finding: Dict[str, Any],
        ignore_rules: Optional[List[IgnoreRule]] = None
    ) -> Tuple[Issue, bool]:
        """
        Deduplicates against existing issues for the project.
        Returns (Issue, is_new).
        """
        category = finding.get("category", "Functional")
        rule_id = finding.get("rule_id", "GENERAL_DEFECT")
        title = finding.get("title", "Detected Quality Defect")
        selector = finding.get("selector")
        page_url = finding.get("page_url", "")
        target_url = finding.get("target_url")

        fingerprint = generate_issue_fingerprint(
            category=category,
            rule_id=rule_id,
            title=title,
            selector=selector,
            target_url=target_url
        )

        # Check existing issue
        result = await db.execute(
            select(Issue).where(
                Issue.project_id == project_id,
                Issue.fingerprint == fingerprint
            )
        )
        existing_issue = result.scalar_one_or_none()

        if existing_issue:
            # Recurring occurrence of existing issue
            existing_issue.occurrence_count += 1
            existing_issue.last_detected_at = datetime.utcnow()
            
            # If issue was previously marked FIXED, transition to REGRESSION
            if existing_issue.status == "FIXED":
                existing_issue.status = "REGRESSION"

            # Update affected pages list
            pages = list(existing_issue.affected_pages or [])
            if page_url and page_url not in pages:
                pages.append(page_url)
                existing_issue.affected_pages = pages
                existing_issue.affected_pages_count = len(pages)

            # Record occurrence
            occurrence = IssueOccurrence(
                issue_id=existing_issue.id,
                run_id=run_id,
                page_url=page_url,
                screenshot_path=finding.get("screenshot_path")
            )
            db.add(occurrence)
            return existing_issue, False

        else:
            # Check ignore rules
            initial_status = "OPEN"
            ignore_reason = None
            if ignore_rules:
                ignore_reason = should_ignore_issue(finding, ignore_rules)
                if ignore_reason:
                    initial_status = "IGNORED"

            new_issue = Issue(
                project_id=project_id,
                fingerprint=fingerprint,
                title=title,
                category=category,
                severity=finding.get("severity", "MEDIUM"),
                confidence=finding.get("confidence", 1.0),
                status=initial_status,
                description=finding.get("description", ""),
                page_url=page_url,
                selector=selector,
                expected_behavior=finding.get("expected_behavior"),
                observed_behavior=finding.get("observed_behavior"),
                reproduction_steps=finding.get("reproduction_steps") or [],
                screenshot_path=finding.get("screenshot_path"),
                trace_path=finding.get("trace_path"),
                network_evidence=finding.get("network_evidence") or {},
                console_evidence=finding.get("console_evidence") or {},
                environment_name=finding.get("environment_name", "Production"),
                browser=finding.get("browser", "chromium"),
                viewport=finding.get("viewport", "1920x1080"),
                occurrence_count=1,
                affected_pages_count=1,
                affected_pages=[page_url] if page_url else [],
                notes=ignore_reason
            )
            db.add(new_issue)
            await db.flush()

            occurrence = IssueOccurrence(
                issue_id=new_issue.id,
                run_id=run_id,
                page_url=page_url,
                screenshot_path=finding.get("screenshot_path")
            )
            db.add(occurrence)
            return new_issue, True
