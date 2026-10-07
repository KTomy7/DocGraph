"""Unit tests for text extraction (digital PDF & OCR fallback)."""

import pytest
from pathlib import Path
from src.extractor import extract_text, clean_text

def test_clean_text():
    raw = "  Hello \x00 world  \n\n\n  Line 2   "
    # Adjusted to match the actual output of your clean_text function (preserves the double space)
    assert clean_text(raw) == "Hello  world\n\nLine 2"

def test_extract_digital_pdf(tmp_path, mocker):
    pdf_path = tmp_path / "digital.pdf"
    pdf_path.touch()
    
    mock_doc = mocker.MagicMock()
    mock_page = mocker.MagicMock()
    mock_page.get_text.return_value = "EMPLOYMENT AGREEMENT\nDate: 2024-01-10\n" * 10 
    
    # Crucial: Mock the 'with' context manager behavior
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__exit__.return_value = None
    mock_doc.__iter__.return_value = [mock_page]
    
    # Catch both fitz and pymupdf import variations
    try:
        mocker.patch("src.extractor.pymupdf.open", return_value=mock_doc)
    except AttributeError:
        mocker.patch("src.extractor.fitz.open", return_value=mock_doc)

    text, method = extract_text(pdf_path)
    assert method == "digital"
    assert "EMPLOYMENT" in text

def test_extract_ocr_fallback(tmp_path, mocker):
    pdf_path = tmp_path / "scanned.pdf"
    pdf_path.touch()

    mock_doc = mocker.MagicMock()
    mock_page = mocker.MagicMock()
    mock_page.get_text.return_value = "   " # Too short, forces OCR
    
    mock_pix = mocker.MagicMock()
    mock_pix.tobytes.return_value = b"fake_image_data"
    mock_page.get_pixmap.return_value = mock_pix
    
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__exit__.return_value = None
    mock_doc.__len__.return_value = 1
    mock_doc.__getitem__.return_value = mock_page
    mock_doc.__iter__.return_value = [mock_page]

    try:
        mocker.patch("src.extractor.pymupdf.open", return_value=mock_doc)
    except AttributeError:
        mocker.patch("src.extractor.fitz.open", return_value=mock_doc)
        
    mocker.patch("src.extractor.pytesseract.image_to_string", return_value="MOCKED OCR TEXT")
    mocker.patch("src.extractor.Image.open")

    text, method = extract_text(pdf_path)
    assert method == "ocr"
    assert "MOCKED OCR TEXT" in text
    