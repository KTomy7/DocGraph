"""DocGraph environment health checks."""

import shutil

import ollama
from rich.console import Console
from rich.table import Table

from src.config import (
    ARCHIVE_DIR,
    CORE_CATEGORIES,
    EMBEDDING_MODEL,
    INBOX_DIR,
    LLM_MODEL,
    RAG_DIR,
    OLLAMA_HOST,
    init_filesystem,
)

console = Console()


def verify_ollama() -> bool:
    """Check if Ollama server is reachable and required models are pulled."""
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        models_response = client.list()

        models = getattr(models_response, "models", None)
        if models is None and isinstance(models_response, dict):
            models = models_response.get("models", [])
        elif models is None:
            models = []

        installed_models = []
        for model in models:
            if isinstance(model, dict):
                installed_models.append(model.get("model", "") or model.get("name", ""))
            else:
                installed_models.append(
                    getattr(model, "model", "") or getattr(model, "name", "")
                )

        has_llm = any(LLM_MODEL in name for name in installed_models)
        has_embed = any(EMBEDDING_MODEL in name for name in installed_models)
        return has_llm and has_embed
    except Exception as error:
        console.print(f"[bold red]Failed to connect to Ollama:[/bold red] {error}")
        return False


def verify_tesseract() -> bool:
    """Check if tesseract binary is in system PATH."""
    return shutil.which("tesseract") is not None


def main() -> int:
    """Run all environment checks and return a process status code."""
    console.rule("[bold cyan]DocGraph - Environment Verification[/bold cyan]")

    filesystem_ok = init_filesystem()
    dirs_exist = filesystem_ok and INBOX_DIR.exists() and ARCHIVE_DIR.exists() and RAG_DIR.exists()
    categories_exist = filesystem_ok and all(
        (ARCHIVE_DIR / category).exists() for category in CORE_CATEGORIES
    )
    tess_ok = verify_tesseract()
    ollama_ok = verify_ollama()

    table = Table(title="System & Environment Status")
    table.add_column("Component", style="bold")
    table.add_column("Target / Path", style="dim")
    table.add_column("Status", justify="right")
    table.add_row(
        "Filesystem Layout",
        str(INBOX_DIR.parent),
        "[green]Ready[/green]" if dirs_exist else "[red]Missing[/red]",
    )
    table.add_row(
        "Archive Categories",
        f"{len(CORE_CATEGORIES)} subfolders",
        "[green]Ready[/green]" if categories_exist else "[red]Incomplete[/red]",
    )
    table.add_row(
        "Tesseract OCR",
        shutil.which("tesseract") or "Not found",
        "[green]Installed[/green]"
        if tess_ok
        else "[yellow]Missing (brew install tesseract)[/yellow]",
    )
    table.add_row(
        "Ollama Models",
        f"{LLM_MODEL}, {EMBEDDING_MODEL}",
        "[green]Connected & Pulled[/green]"
        if ollama_ok
        else "[red]Missing / Not Running[/red]",
    )
    console.print(table)

    if dirs_exist and categories_exist and tess_ok and ollama_ok:
        console.print("\n[bold green]✓ Environment is ready.[/bold green]\n")
        return 0

    console.print("\n[bold yellow]! Please fix the items above before proceeding.[/bold yellow]\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
