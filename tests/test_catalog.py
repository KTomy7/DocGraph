"""
DocGraph - Milestone 4 Verification (Catalog & Deduplication Registry)
"""

import sys
import tempfile
from pathlib import Path
from rich.console import Console

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import init_filesystem
from src.classifier import DocumentMetadata
from src.catalog import (
    init_catalog,
    catalog_document,
    is_document_cataloged,
    search_catalog,
    get_catalog_entry_by_hash,
)

console = Console()


def main() -> int:
    console.rule("[bold cyan]DocGraph - Milestone 4: Document Catalog & Deduplication[/bold cyan]")

    test_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    mock_metadata = DocumentMetadata(
        category="University",
        document_type="Transcript",
        issuer="TUClujNapoca",
        document_date="2024-02-15",
        canonical_filename="2024-02-15_University_TUClujNapoca_Transcript.pdf",
    )
    mock_path = PROJECT_ROOT / "data" / "archive" / "University" / mock_metadata.canonical_filename

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "state.db"
        init_filesystem()
        init_catalog(db_path)

        try:
            # 1. Deduplication Check (Before Insert)
            console.print("[bold]1. Checking non-existent hash check...[/bold]")
            assert not is_document_cataloged(test_hash, db_path), "Hash should not exist initially!"
            console.print("  [green]Confirmed: Hash not found in catalog[/green]")

            # 2. Register Document
            console.print("\n[bold]2. Cataloging document...[/bold]")
            catalog_document(
                sha256=test_hash,
                original_filename="transcript_semester_1.pdf",
                metadata=mock_metadata,
                archive_path=mock_path,
                extraction_method="digital",
                db_path=db_path,
            )
            assert is_document_cataloged(test_hash, db_path), "Hash should exist after cataloging!"
            console.print("  [green]Confirmed: Document successfully cataloged[/green]")

            # 3. Retrieve by Hash
            console.print("\n[bold]3. Fetching record by SHA-256...[/bold]")
            record = get_catalog_entry_by_hash(test_hash, db_path)
            assert record is not None, "Failed to retrieve record by hash"
            assert record["issuer"] == "TUClujNapoca"
            assert record["category"] == "University"
            console.print(f"  Retrieved: [cyan]{record['canonical_filename']}[/cyan] ({record['issuer']})")

            # 4. Search Catalog
            console.print("\n[bold]4. Testing search queries...[/bold]")
            results_by_query = search_catalog(query="TUCluj", db_path=db_path)
            assert len(results_by_query) >= 1, "Failed to search by issuer keyword"

            results_by_cat = search_catalog(category="University", db_path=db_path)
            assert len(results_by_cat) >= 1, "Failed to search by category"

            results_empty = search_catalog(query="NonExistentTermXYZ", db_path=db_path)
            assert len(results_empty) == 0, "Expected zero results for non-matching term"

            console.print(f"  [green]Search query 'TUCluj': {len(results_by_query)} hit(s)[/green]")
            console.print(f"  [green]Search category 'University': {len(results_by_cat)} hit(s)[/green]")

            console.print("\n[bold green]✓ Milestone 4 Complete: Document Catalog verified![/bold green]\n")
            return 0

        except Exception as e:
            console.print(f"\n[bold red]✕ Test failed:[/bold red] {e}\n")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
