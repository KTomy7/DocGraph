"""
DocGraph - Environment Health Check (Milestone 1 Verification)
"""

import sys
import shutil
from pathlib import Path
from rich.console import Console
from rich.table import Table
import ollama

# Ensure project root is in sys.path so we can import from src
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    INBOX_DIR,
    ARCHIVE_DIR,
    RAG_DIR,
    OLLAMA_HOST,
    LLM_MODEL,
    EMBEDDING_MODEL,
    VALID_CATEGORIES,
)

console = Console()


def verify_ollama() -> bool:
    """Check if Ollama server is reachable and required models are pulled."""
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        models_response = client.list()
        
        installed_models = []
        for m in models_response.get("models", []):
            if isinstance(m, dict):
                installed_models.append(m.get("model", "") or m.get("name", ""))
            else:
                installed_models.append(getattr(m, "model", "") or getattr(m, "name", ""))

        has_llm = any(LLM_MODEL in name for name in installed_models)
        has_embed = any(EMBEDDING_MODEL in name for name in installed_models)

        return has_llm and has_embed
    except Exception as e:
        console.print(f"[bold red]Failed to connect to Ollama:[/bold red] {e}")
        return False


def verify_tesseract() -> bool:
    """Check if tesseract binary is in system PATH."""
    return shutil.which("tesseract") is not None


def main():
    console.rule("[bold cyan]DocGraph - Milestone 1 Verification[/bold cyan]")

    table = Table(title="System & Environment Status")
    table.add_column("Component", style="bold")
    table.add_column("Target / Path", style="dim")
    table.add_column("Status", justify="right")

    # 1. Directory Structure
    dirs_exist = INBOX_DIR.exists() and ARCHIVE_DIR.exists() and RAG_DIR.exists()
    table.add_row(
        "Filesystem Layout",
        str(INBOX_DIR.parent),
        "[green]Ready[/green]" if dirs_exist else "[red]Missing[/red]",
    )

    # 2. Archive Subfolders
    categories_exist = all((ARCHIVE_DIR / cat).exists() for cat in VALID_CATEGORIES)
    table.add_row(
        "Archive Categories",
        f"{len(VALID_CATEGORIES)} subfolders",
        "[green]Ready[/green]" if categories_exist else "[red]Incomplete[/red]",
    )

    # 3. Tesseract Binary
    tess_ok = verify_tesseract()
    table.add_row(
        "Tesseract OCR",
        shutil.which("tesseract") or "Not found",
        "[green]Installed[/green]" if tess_ok else "[yellow]Missing (brew install tesseract)[/yellow]",
    )

    # 4. Ollama Connectivity & Models
    ollama_ok = verify_ollama()
    table.add_row(
        "Ollama Models",
        f"{LLM_MODEL}, {EMBEDDING_MODEL}",
        "[green]Connected & Pulled[/green]" if ollama_ok else "[red]Missing / Not Running[/red]",
    )

    console.print(table)

    if dirs_exist and categories_exist and tess_ok and ollama_ok:
        console.print("\n[bold green]✓ Milestone 1 Complete: Environment is ready for Milestone 2![/bold green]\n")
    else:
        console.print("\n[bold yellow]! Please fix the items above before proceeding.[/bold yellow]\n")


if __name__ == "__main__":
    main()