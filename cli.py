"""
DocGraph CLI
Unified command-line interface for document ingestion and catalog management.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.pipeline import process_document
from src.catalog import search_catalog, init_catalog
from src.config import init_filesystem
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

    if filesystem_ok and catalog_ok:
        console.print("\n[bold green]All systems operational.[/bold green]")
        raise typer.Exit(code=0)
    else:
        console.print("\n[bold red]Some components failed. Please check the logs above.[/bold red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
    