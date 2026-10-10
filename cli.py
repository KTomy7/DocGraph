"""
DocGraph CLI
Unified command-line interface for document ingestion and catalog management.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.pipeline import process_document
from src.catalog import init_catalog, is_catalog_initialized, search_catalog
from src.config import INBOX_DIR, init_filesystem, is_filesystem_initialized
from src.check_env import verify_ollama, verify_tesseract

app = typer.Typer(
    name="docgraph",
    help="Intelligent Document Cataloging & Archiving Pipeline",
    add_completion=False,
)
console = Console()


@app.command()
def init():
    """Initialize the SQLite catalog and archive directories."""
    filesystem_ok = init_filesystem()
    catalog_ok = init_catalog()
    tesseract_ok = verify_tesseract()

    if filesystem_ok and catalog_ok and tesseract_ok:
        console.print("[bold green]✓[/bold green] DocGraph catalog, directories and Tesseract initialized.")
        return

    if filesystem_ok:
        console.print("[green]✓[/green] Filesystem directories initialized.")
    else:
        console.print("[red]✗[/red] Failed to initialize filesystem directories.")

    if catalog_ok:
        console.print("[green]✓[/green] SQLite catalog initialized.")
    else:
        console.print("[red]✗[/red] Failed to initialize SQLite catalog.")

    if tesseract_ok:
        console.print("[green]✓[/green] Tesseract OCR is available.")
    else:
        console.print("[red]✗[/red] Tesseract OCR is not available. Please install it and ensure it's in your system PATH.")
    raise typer.Exit(code=1)


@app.command()
def doctor():
    """Run a diagnostic check on the DocGraph environment."""
    filesystem_ok = init_filesystem()
    catalog_ok = init_catalog()
    ollama_ok = verify_ollama()
    tesseract_ok = verify_tesseract()

    console.print("[bold]DocGraph Environment Diagnostics[/bold]\n")
    console.print(f"Filesystem directories: {'[green]OK[/green]' if filesystem_ok else '[red]FAIL[/red]'}")
    console.print(f"SQLite catalog: {'[green]OK[/green]' if catalog_ok else '[red]FAIL[/red]'}")
    console.print(f"Ollama connectivity: {'[green]OK[/green]' if ollama_ok else '[red]FAIL[/red]'}")
    console.print(f"Tesseract OCR: {'[green]OK[/green]' if tesseract_ok else '[red]FAIL[/red]'}")

    if filesystem_ok and catalog_ok and ollama_ok and tesseract_ok:
        console.print("\n[bold green]All systems operational.[/bold green]")
        raise typer.Exit(code=0)
    else:
        console.print("\n[bold red]Some components failed. Please check the logs above.[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def ingest():
    """Process all PDFs currently in the inbox."""
    if not is_filesystem_initialized() or not is_catalog_initialized():
        console.print(
            "[red]Error:[/red] DocGraph is not initialized. "
            "Run [bold]docgraph init[/bold] first."
        )
        raise typer.Exit(code=1)

    # File discovery
    files_to_process = sorted(INBOX_DIR.rglob("*.pdf"))
    if not files_to_process:
        console.print(f"[yellow]Warning:[/yellow] No PDFs found in {INBOX_DIR}")
        raise typer.Exit(code=0)

    console.print(f"Found {len(files_to_process)} document(s) to ingest.\n")

    # Ingestion Loop
    for file_path in files_to_process:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(f"Processing [cyan]{file_path.name}[/cyan]...", total=None)

            try:
                # Delegate to the core pipeline service
                dest_path, metadata, ext_method = process_document(file_path)
            except Exception as e:
                console.print(f"[red]✗ Failed:[/red] {file_path.name}\n  Reason: {str(e)}")
                continue

        # Terminal UI Output
        console.print(
            f"[green]✓ Ingested:[/green] {file_path.name}\n"
            f"  [dim]Category:[/dim] {metadata.category} | [dim]Issuer:[/dim] {metadata.issuer} | [dim]Method:[/dim] {ext_method}\n"
            f"  [dim]Archived at:[/dim] {dest_path}\n"
        )


if __name__ == "__main__":
    app()
    