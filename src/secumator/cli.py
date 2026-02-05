import asyncio
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

app = typer.Typer(name="secumator", help="Professional security audit report generator")
console = Console()


@app.command()
def scan(
    target: str = typer.Argument(..., help="Target URL or IP address"),
    scan_type: str = typer.Option("webapp", "--type", "-t", help="Scan type: webapp, network, api, full"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output report path"),
    format: str = typer.Option("pdf", "--format", "-f", help="Report format: pdf, html, json"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI-powered analysis"),
):
    """Run a security scan and generate a report."""
    from secumator.core.database import async_session_factory, init_db
    from secumator.models.scan import Scan, ScanType
    from secumator.scanners import ScanEngine
    from secumator.reports import ReportGenerator

    async def run():
        await init_db()
        
        async with async_session_factory() as db:
            scan_obj = Scan(target=target, scan_type=ScanType(scan_type))
            db.add(scan_obj)
            await db.commit()
            await db.refresh(scan_obj)

            engine = ScanEngine()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"[cyan]Scanning {target}...", total=None)
                scan_obj = await engine.run_scan(scan_obj, db)
                progress.update(task, description="[green]Scan completed!")

            console.print(f"\n[bold green]✓ Scan completed![/bold green]")
            console.print(f"  Status: {scan_obj.status.value}")
            console.print(f"  Findings: {len(scan_obj.findings)}")

            if scan_obj.findings:
                table = Table(title="Findings Summary")
                table.add_column("Severity", style="bold")
                table.add_column("Count", justify="right")

                severity_counts = {}
                for f in scan_obj.findings:
                    severity_counts[f.severity.value] = severity_counts.get(f.severity.value, 0) + 1

                colors = {"critical": "red", "high": "orange1", "medium": "yellow", "low": "cyan", "info": "dim"}
                for sev in ["critical", "high", "medium", "low", "info"]:
                    if count := severity_counts.get(sev, 0):
                        table.add_row(f"[{colors[sev]}]{sev.upper()}[/{colors[sev]}]", str(count))

                console.print(table)

            if output or format:
                generator = ReportGenerator()
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                    task = progress.add_task("[cyan]Generating report...", total=None)
                    report_path = await generator.generate(
                        scan_obj, scan_obj.findings, format=format, include_ai_analysis=not no_ai
                    )
                    progress.update(task, description="[green]Report generated!")

                if output:
                    import shutil
                    shutil.copy(report_path, output)
                    report_path = Path(output)

                console.print(f"\n[bold green]✓ Report saved:[/bold green] {report_path}")

    asyncio.run(run())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """Start the API server."""
    import uvicorn
    console.print(f"[bold cyan]Starting Secumator API server...[/bold cyan]")
    console.print(f"  Host: {host}")
    console.print(f"  Port: {port}")
    console.print(f"  Docs: http://{host}:{port}/docs")
    uvicorn.run("secumator.api:app", host=host, port=port, reload=reload)


@app.command()
def list_scans(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of scans to show"),
):
    """List recent scans."""
    from secumator.core.database import async_session_factory, init_db
    from secumator.models.scan import Scan
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    async def run():
        await init_db()
        async with async_session_factory() as db:
            result = await db.execute(
                select(Scan)
                .options(selectinload(Scan.findings))
                .order_by(Scan.created_at.desc())
                .limit(limit)
            )
            scans = result.scalars().all()

            if not scans:
                console.print("[yellow]No scans found.[/yellow]")
                return

            table = Table(title="Recent Scans")
            table.add_column("ID", style="cyan")
            table.add_column("Target")
            table.add_column("Type")
            table.add_column("Status")
            table.add_column("Findings", justify="right")
            table.add_column("Created")

            status_colors = {
                "pending": "yellow",
                "running": "blue",
                "completed": "green",
                "failed": "red",
                "cancelled": "dim",
            }

            for s in scans:
                color = status_colors.get(s.status.value, "white")
                table.add_row(
                    str(s.id),
                    s.target[:40] + "..." if len(s.target) > 40 else s.target,
                    s.scan_type.value,
                    f"[{color}]{s.status.value}[/{color}]",
                    str(len(s.findings)),
                    s.created_at.strftime("%Y-%m-%d %H:%M"),
                )

            console.print(table)

    asyncio.run(run())


@app.command()
def version():
    """Show version information."""
    from secumator import __version__
    rprint(f"[bold cyan]Secumator[/bold cyan] v{__version__}")
    rprint("Professional Security Audit Report Generator")


if __name__ == "__main__":
    app()
