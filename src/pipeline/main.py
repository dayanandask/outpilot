import asyncio
import sys
import uuid
from pathlib import Path
from typing import Optional, List
import structlog

import typer
from rich.console import Console
from rich.table import Table

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from pipeline.models import SeedInput, Company, Prospect, Contact
from pipeline.db import (
    DatabaseManager,
    Run,
    CompanyRecord,
    ProspectRecord,
    ContactRecord,
)
from pipeline.stages.s1_apollo import ApolloStage
from pipeline.stages.s2_email import EmailStage

logger = structlog.get_logger(__name__)
app = typer.Typer(add_completion=False)
console = Console(force_terminal=False, no_color=True)

STATUS_EMOJI = {
    "completed": "[OK]",
    "failed": "[ERR]",
    "running": "[RUN]",
    "pending": "[WAIT]",
}


def _mask(value: Optional[str]) -> str:
    if not value:
        return ""
    return value[-4:].rjust(20, "*")


def _model_to_company_record(model: Company, run_id: str) -> CompanyRecord:
    return CompanyRecord(
        run_id=run_id,
        domain=model.domain,
        name=model.name,
        source=model.source,
        status="completed",
    )


def _model_to_prospect_record(model: Prospect, run_id: str) -> ProspectRecord:
    return ProspectRecord(
        run_id=run_id,
        company_domain=model.company_domain,
        full_name=model.full_name,
        title=model.title,
        linkedin_url=model.linkedin_url,
        status="completed",
    )


def _model_to_contact_record(model: Contact, run_id: str) -> ContactRecord:
    return ContactRecord(
        run_id=run_id,
        linkedin_url=model.prospect.linkedin_url,
        full_name=model.prospect.full_name,
        title=model.prospect.title,
        company_domain=model.prospect.company_domain,
        work_email=model.work_email,
        verified=model.verified,
        status="completed",
    )


def _render_checkpoint(contacts: List[Contact]) -> None:
    console.print(
        "\n[bold yellow]OUTREACH SUMMARY -- Review before sending[/bold yellow]\n"
    )
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Contact", style="cyan", no_wrap=False)
    table.add_column("Company", style="green")
    table.add_column("Email", style="white")

    for contact in contacts:
        name_title = f"{contact.prospect.full_name}, {contact.prospect.title}"
        table.add_row(name_title, contact.prospect.company_domain, contact.work_email)

    console.print(table)
    console.print(f"\nTotal: [bold]{len(contacts)}[/bold] emails will be sent.")
    console.print("Type 'send' to confirm, anything else to abort.")


@app.command()
def run(
    domain: str = typer.Argument(
        ..., help="Seed domain to start pipeline (e.g., stripe.com)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Run stages 1-3 only; skip sending emails"
    ),
    resume: Optional[str] = typer.Option(
        None, "--resume", help="Resume an existing run by run_id"
    ),
) -> None:
    """Run the full cold outreach pipeline."""
    asyncio.run(_run_pipeline(domain, dry_run, resume))


@app.command()
def status(run_id: str = typer.Argument(..., help="Run ID to inspect")) -> None:
    """Show progress summary for a given run."""
    asyncio.run(_show_status(run_id))


@app.command()
def list_runs() -> None:
    """List all past pipeline runs."""
    asyncio.run(_list_runs())


async def _run_pipeline(domain: str, dry_run: bool, resume: Optional[str]) -> None:
    seed_domain = domain.strip().lower()
    try:
        SeedInput(domain=seed_domain)
    except Exception as e:
        console.print(f"[bold red]Invalid domain:[/bold red] {e}")
        raise typer.Exit(1)

    run_id = resume if resume else f"run_{uuid.uuid4().hex[:8]}"
    db_manager = DatabaseManager(run_id)
    await db_manager.initialize()
    await db_manager.create_run(seed_domain)

    try:
        stage1 = ApolloStage()
        stage2 = EmailStage()
        stage1_label = "Stage 1: Searching companies..."
        stage2_label = "Stage 2: Resolving emails..."

        console.print(f"[dim]{stage1_label}[/dim]")
        companies, prospects = await stage1.execute([SeedInput(domain=seed_domain)])
        console.print(
            f"[green]Stage 1 done[/green] -- {len(companies)} companies, {len(prospects)} prospects"
        )
        await db_manager.save_companies(
            [_model_to_company_record(c, run_id) for c in companies]
        )
        await db_manager.save_prospects(
            [_model_to_prospect_record(p, run_id) for p in prospects]
        )

        if not prospects:
            console.print("[yellow]No prospects found. Pipeline complete.[/yellow]")
            await db_manager.update_run_status("completed")
            await stage1.close()
            await stage2.close()
            await db_manager.close()
            return

        console.print(f"[dim]{stage2_label}[/dim]")
        contacts = await stage2.execute(prospects)
        await db_manager.save_contacts(
            [_model_to_contact_record(c, run_id) for c in contacts]
        )
        console.print(
            f"[green]Stage 2 done[/green] -- {len(contacts)} contacts resolved"
        )

        if not contacts:
            console.print("[yellow]No emails resolved. Pipeline complete.[/yellow]")
            await db_manager.update_run_status("completed")
            await stage1.close()
            await stage2.close()
            await db_manager.close()
            return

        if dry_run:
            console.print(
                "\n[bold green]Dry run complete. Contacts resolved:[/bold green]"
            )
            _render_checkpoint(contacts)
            await db_manager.update_run_status("completed")
            await stage1.close()
            await stage2.close()
            await db_manager.close()
            return

        _render_checkpoint(contacts)
        console.print(
            "\n[bold yellow]Stage 3 (Brevo send) is not wired yet -- enable OutreachStage to send.[/bold yellow]"
        )
        console.print(f"\n[bold green]Pipeline complete![/bold green] Run ID: {run_id}")
        await db_manager.update_run_status("completed")

    finally:
        await stage1.close()
        await stage2.close()
        await db_manager.close()


async def _show_status(run_id: str) -> None:
    db_manager = DatabaseManager(run_id)
    try:
        await db_manager.initialize()
        async with await db_manager.get_session() as session:
            from sqlmodel import select

            stmt = select(Run).where(Run.run_id == run_id)
            result = await session.exec(stmt)
            run = result.one_or_none()
            if not run:
                console.print(f"[red]Run {run_id} not found.[/red]")
                return
            companies = await db_manager.get_companies()
            prospects = await db_manager.get_prospects()
            contacts = await db_manager.get_contacts()
            outreach = await db_manager.get_outreach_records()

        console.print(f"Run ID: [bold cyan]{run.run_id}[/bold cyan]")
        console.print(f"Domain: [white]{run.seed_domain}[/white]")
        console.print(
            f"Status: [bold]{run.status}[/bold] {STATUS_EMOJI.get(run.status, '')}"
        )
        console.print(f"Companies: {len(companies)}")
        console.print(f"Prospects: {len(prospects)}")
        console.print(f"Contacts: {len(contacts)}")
        console.print(f"Outreach: {len(outreach)}")
        if run.error_msg:
            console.print(f"[red]Error:[/red] {run.error_msg}")
    finally:
        await db_manager.close()


async def _list_runs() -> None:
    runs_dir = Path("runs")
    if not runs_dir.exists():
        console.print("No runs directory found.")
        return

    db_files = sorted(
        runs_dir.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    table = Table(title="Pipeline Runs", show_edge=True)
    table.add_column("Run ID", style="cyan")
    table.add_column("Domain", style="white")
    table.add_column("Status", style="green")
    table.add_column("Created")

    for db_file in db_files[:50]:
        run_id = db_file.stem
        db_manager = DatabaseManager(run_id)
        try:
            await db_manager.initialize()
            async with await db_manager.get_session() as session:
                from sqlmodel import select

                stmt = select(Run).where(Run.run_id == run_id)
                result = await session.exec(stmt)
                run = result.one_or_none()
                if run:
                    table.add_row(
                        run.run_id,
                        run.seed_domain,
                        f"{STATUS_EMOJI.get(run.status, '')} {run.status}",
                        run.created_at.strftime("%Y-%m-%d %H:%M"),
                    )
        except Exception:
            pass
        finally:
            await db_manager.close()

    console.print(table)


if __name__ == "__main__":
    app()
