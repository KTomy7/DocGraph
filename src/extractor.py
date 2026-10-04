"""
DocGraph - Document Text Extraction & OCR Fallback Engine
Handles native digital extraction (PyMuPDF) and scanned documents (Tesseract OCR).
"""

import io
from pathlib import Path
from typing import Tuple
import pymupdf
from PIL import Image
import pytesseract

from src.config import MIN_DIGITAL_TEXT_CHARS, TESSERACT_LANGUAGES


def clean_text(text: str) -> str:
    """Normalize whitespace and strip null bytes."""
    if not text:
        return ""
    # Strip null characters that can appear in malformed PDF streams
    text = text.replace("\x00", "")
    lines = [line.strip() for line in text.splitlines()]
    
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned_lines.append("")
                prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False
            
    return "\n".join(cleaned_lines).strip()


def extract_from_image(image_path: Path) -> str:
    """Extract text directly from a raw image file (.png, .jpg, .jpeg, etc.)."""
    with Image.open(image_path) as img:
        text = pytesseract.image_to_string(img, lang=TESSERACT_LANGUAGES)
    return clean_text(text)


def extract_from_pdf(pdf_path: Path) -> Tuple[str, str]:
    """
    Extract text from a PDF file.
    Tries native digital extraction first; falls back to OCR if sparse or scanned.
    
    Returns:
        Tuple[str, str]: (extracted_text, method_used ["digital" | "ocr"])
    """
    doc = pymupdf.open(pdf_path)
    full_text = []

    # 1. Attempt fast digital text extraction
    for page in doc:
        full_text.append(page.get_text())

    extracted = clean_text("\n".join(full_text))

    # If digital text exists and meets the minimum length, return immediately
    if len(extracted) >= MIN_DIGITAL_TEXT_CHARS:
        doc.close()
        return extracted, "digital"

    # 2. Fallback to Tesseract OCR for scanned pages
    ocr_text = []
    # 300 DPI (zoom 300 / 72 = 4.1667) gives optimal OCR accuracy for IDs and small print
    zoom = 300 / 72
    mat = pymupdf.Matrix(zoom, zoom)

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        
        with Image.open(io.BytesIO(img_bytes)) as img:
            page_text = pytesseract.image_to_string(img, lang=TESSERACT_LANGUAGES)
            ocr_text.append(page_text)

    doc.close()
    return clean_text("\n".join(ocr_text)), "ocr"


def extract_text(file_path: Path) -> Tuple[str, str]:
    """
    Main extraction router based on file extension.
    
    Returns:
        Tuple[str, str]: (extracted_text, extraction_method)
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return extract_from_pdf(file_path)
    elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        return extract_from_image(file_path), "ocr"
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
    