"""
DocGraph - Milestone 3 Verification (Classification & Safe Relocation)
"""

import sys
from pathlib import Path
from rich.console import Console
import pymupdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import init_filesystem, INBOX_DIR
from src.extractor import extract_text
from src.classifier import classify_document
from src.mover import relocate_file, calculate_sha256

console = Console()


def create_mock_lease_pdf(output_path: Path):
    """Creates a sample apartment lease document."""
    doc = pymupdf.open()
    page = doc.new_page()
    text = (
        "APARTMENT TENANCY AGREEMENT\n"
        "Date of Agreement: 2024-03-01\n"
        "Landlord: Cartagena Living Properties SL\n"
        "Tenant: Kiss Tamas\n"
        "Property: Calle Mayor 12, Cartagena, Spain\n"
        "Monthly Rent: 550 EUR\n"
        "Security Deposit: 550 EUR"
    )
    page.insert_text((50, 72), text, fontsize=12)
    doc.save(output_path)
    doc.close()


def main() -> int:
    console.rule("[bold cyan]DocGraph - Milestone 3: Classification & Safe Mover[/bold cyan]")
    init_filesystem()

    test_doc = INBOX_DIR / "temp_incoming_lease.pdf"
    create_mock_lease_pdf(test_doc)
    initial_hash = calculate_sha256(test_doc)

    try:
        console.print("[bold]1. Extracting Text from Test Document...[/bold]")
        text, method = extract_text(test_doc)
        console.print(f"  Extracted {len(text)} chars via [green]{method}[/green]")

        console.print("\n[bold]2. Querying Ollama (qwen2.5:14b) for Metadata Classification...[/bold]")
        metadata = classify_document(text, original_filename=test_doc.name)
        
        console.print(f"  Category: [green]{metadata.category}[/green]")
        console.print(f"  Document Type: [cyan]{metadata.document_type}[/cyan]")
        console.print(f"  Issuer: [cyan]{metadata.issuer}[/cyan]")
        console.print(f"  Date: [cyan]{metadata.document_date}[/cyan]")
        console.print(f"  Target Filename: [bold yellow]{metadata.canonical_filename}[/bold yellow]")

        assert metadata.category in ["Housing", "Contracts"], f"Unexpected category: {metadata.category}"

        console.print("\n[bold]3. Relocating File to Archive...[/bold]")
        archived_path = relocate_file(test_doc, metadata)
        
        console.print(f"  Archived to: [green]{archived_path}[/green]")
        assert archived_path.exists(), "Archived file does not exist!"
        assert not test_doc.exists(), "Original file was not cleaned up from inbox!"
        assert calculate_sha256(archived_path) == initial_hash, "Hash mismatch after relocation!"

        console.print("\n[bold green]✓ Milestone 3 Complete: Classification and atomic move verified![/bold green]\n")
        
        # Cleanup test artifact
        archived_path.unlink()
        return 0

    except Exception as e:
        console.print(f"\n[bold red]✕ Test failed:[/bold red] {e}\n")
        if test_doc.exists():
            test_doc.unlink()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
