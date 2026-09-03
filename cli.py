import sys
import asyncio
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from backend.config import settings
from backend.database import init_db, AsyncSessionLocal
from backend.models import Project, Environment, QARun, Issue
from backend.services.orchestrator import QAOrchestrator
from sqlalchemy import select

app = typer.Typer(help="WebQA Agent CI/CD Command-Line Quality Gate")
console = Console()

@app.command()
def scan(
    url: str = typer.Option(..., "--url", "-u", help="Target URL to inspect"),
    project_name: str = typer.Option("CI Run Project", "--project", "-p", help="Project name"),
    scan_type: str = typer.Option("QUICK_SCAN", "--type", "-t", help="QUICK_SCAN or FULL_SCAN"),
    browser: str = typer.Option("chromium", "--browser", "-b", help="Browser engine"),
    min_score: float = typer.Option(80.0, "--min-score", help="Quality gate: Minimum QA Score (0-100)"),
    max_critical: int = typer.Option(0, "--max-critical", help="Quality gate: Maximum allowed Critical defects"),
    max_high: int = typer.Option(3, "--max-high", help="Quality gate: Maximum allowed High defects"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON results")
):
    """
    Executes an automated QA scan and enforces CI quality gates with exit codes:
    0 = Passed, 1 = Quality Gate Failed, 2 = Execution Error.
    """
    async def _run_scan() -> int:
        try:
            await init_db()
            async with AsyncSessionLocal() as db:
                # Find or create project
                proj_res = await db.execute(select(Project).where(Project.base_url == url))
                proj = proj_res.scalar_one_or_none()
                if not proj:
                    proj = Project(
                        name=project_name,
                        base_url=url,
                        allowed_domains=[]
                    )
                    db.add(proj)
                    await db.flush()
                    env = Environment(
                        project_id=proj.id,
                        name="CI Environment",
                        base_url=url,
                        is_default=True
                    )
                    db.add(env)
                    await db.commit()
                project_id = proj.id

                # Create Run
                qa_run = QARun(
                    project_id=project_id,
                    scan_type=scan_type,
                    status="PENDING",
                    trigger="CLI",
                    browser=browser
                )
                db.add(qa_run)
                await db.commit()
                run_id = qa_run.id

            if not json_output:
                console.print(f"[bold blue]Starting WebQA Scan on:[/bold blue] {url} (Run ID: {run_id})")

            orchestrator = QAOrchestrator(run_id)
            completed_run = await orchestrator.execute_scan(project_id)

            if completed_run.status == "FAILED":
                if not json_output:
                    console.print(f"[bold red]Scan execution failed:[/bold red] {completed_run.error_message}")
                return 2

            score = completed_run.qa_score
            critical = completed_run.critical_issues
            high = completed_run.high_issues

            # Quality gate evaluation
            gate_passed = True
            failure_reasons = []

            if score < min_score:
                gate_passed = False
                failure_reasons.append(f"QA Score {score} is below required threshold of {min_score}")

            if critical > max_critical:
                gate_passed = False
                failure_reasons.append(f"Critical issues count ({critical}) exceeds limit ({max_critical})")

            if high > max_high:
                gate_passed = False
                failure_reasons.append(f"High issues count ({high}) exceeds limit ({max_high})")

            if json_output:
                result_payload = {
                    "schema_version": "1.0",
                    "run_id": completed_run.id,
                    "target_url": url,
                    "scan_type": scan_type,
                    "browser": browser,
                    "pages_tested": completed_run.pages_tested,
                    "total_issues": completed_run.total_issues,
                    "qa_score": score,
                    "critical_issues": critical,
                    "high_issues": high,
                    "medium_issues": completed_run.medium_issues,
                    "low_issues": completed_run.low_issues,
                    "quality_gate_passed": gate_passed,
                    "failure_reasons": failure_reasons
                }
                print(json.dumps(result_payload, indent=2))
            else:
                table = Table(title=f"WebQA Audit Summary - {url}")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="bold")
                table.add_row("Pages Tested", str(completed_run.pages_tested))
                table.add_row("WebQA Project Score", f"{score}/100")
                table.add_row("Total Issues", str(completed_run.total_issues))
                table.add_row("Critical Issues", str(critical))
                table.add_row("High Issues", str(high))
                table.add_row("Quality Gate Result", "[bold green]PASSED[/bold green]" if gate_passed else "[bold red]FAILED[/bold red]")
                console.print(table)

                if not gate_passed:
                    for reason in failure_reasons:
                        console.print(f"[red]• {reason}[/red]")

            return 0 if gate_passed else 1

        except Exception as e:
            if not json_output:
                console.print(f"[bold red]Unexpected CLI error:[/bold red] {str(e)}")
            return 2

    exit_code = asyncio.run(_run_scan())
    sys.exit(exit_code)

if __name__ == "__main__":
    app()
