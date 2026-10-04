"""
DocGraph - Extractor Verification (Milestone 2)
"""

import sys
import tempfile
from pathlib import Path
from rich.console import Console
import pymupdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extractor import extract_text

console = Console()


def create_sample_digital_pdf(output_path: Path):
    """Creates a sample PDF with selectable digital text."""
    doc = pymupdf.open()
    page = doc.new_page()
    text = (
        "CONTRACT DE INCHIRIERE\n"
        "Data: 15.09.2024\n"
        "Proprietar: Popescu Ioan\n"
        "Chirias: Kiss Tamas\n"
        "Suma de garantie: 500 EUR.\n"
        "Apartament situat in Cluj-Napoca, str. Memorandumului nr. 20."
    )
    page.insert_text((50, 72), text, fontsize=14)
    doc.save(output_path)
    doc.close()


def create_sample_scanned_image(output_path: Path):
    """
    Creates a realistic crisp scanned image by rendering a PDF page to a PNG.
    This provides realistic anti-aliased font rendering for OCR testing.
    """
    doc = pymupdf.open()
    page = doc.new_page()
    text = (
        "CERTIFICAT FISCAL\n"
        "Identificator: RO987214\n"
        "Statut: Aprobat"
    )
    page.insert_text((50, 72), text, fontsize=18)
    
    # Render at 300 DPI to simulate a real scanner output
    mat = pymupdf.Matrix(300 / 72, 300 / 72)
    pix = page.get_pixmap(matrix=mat)
    pix.save(output_path)
    doc.close()


def main() -> int:
    console.rule("[bold cyan]DocGraph - Milestone 2: Extractor Verification[/bold cyan]")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_pdf = temp_path / "temp_test_digital.pdf"
        test_img = temp_path / "temp_test_scanned.png"

        try:
            # Test 1: Digital PDF Extraction
            console.print("\n[bold]1. Testing Digital PDF Extraction...[/bold]")
            create_sample_digital_pdf(test_pdf)
            pdf_text, pdf_method = extract_text(test_pdf)

            console.print(f"  Method detected: [green]{pdf_method}[/green]")
            console.print(f"  Characters extracted: [cyan]{len(pdf_text)}[/cyan]")
            assert pdf_method == "digital", "Expected 'digital' extraction for native PDF"
            assert "Popescu Ioan" in pdf_text, "Failed to extract digital text content"

            # Test 2: Image OCR Extraction
            console.print("\n[bold]2. Testing Image OCR Fallback (Tesseract)...[/bold]")
            create_sample_scanned_image(test_img)
            img_text, img_method = extract_text(test_img)

            console.print(f"  Method detected: [green]{img_method}[/green]")
            console.print(f"  Extracted text: [cyan]{img_text.strip()}[/cyan]")
            assert img_method == "ocr", "Expected 'ocr' extraction for image"
            assert "CERTIFICAT" in img_text.upper(), "OCR failed to read header"
            assert "987214" in img_text, "OCR failed to read numeric identifier"

            console.print("\n[bold green]✓ Milestone 2 Complete: Text extractor and OCR fallback verified![/bold green]\n")
            return 0

        except Exception as e:
            console.print(f"\n[bold red]✕ Test failed:[/bold red] {e}\n")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
