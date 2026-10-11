import subprocess
import platform
import typer

from pathlib import Path
from rich.console import Console
console = Console()


def open_file_in_default_viewer(file_path: str):
    """Open a file in the default viewer based on the operating system."""

    if not file_path or not Path(file_path).is_file():
        console.print(f"[red]Error:[/red] Cannot open file. File path is invalid: {file_path}")
        raise typer.Exit(code=1)

    console.print(f"[blue]Opening:[/blue] {file_path}")

    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", file_path])
        elif platform.system() == "Windows":  # Windows
            subprocess.run(["start", file_path], shell=True)
        else:  # Linux and other OSes
            subprocess.run(["xdg-open", file_path])
    except Exception as e:
        raise RuntimeError(f"Failed to open file:[/red] {e}")
