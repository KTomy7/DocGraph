"""
DocGraph - Core Processing Pipeline
Orchestrates text extraction, LLM classification, atomic relocation, and cataloging.
"""

from pathlib import Path
from typing import Tuple
from src.extractor import extract_text
from src.classifier import classify_document, DocumentMetadata
from src.mover import relocate_file


def process_document(file_path: Path) -> Tuple[Path, DocumentMetadata, str]:
    """
    Executes the full ingestion lifecycle for a single document.
    
    Args:
        file_path: Absolute path to the raw input document.
        
    Returns:
        Tuple containing the final archived path, the generated metadata, 
        and the extraction method used ('digital' or 'ocr').
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    # 1. Extract Text
    text, ext_method = extract_text(file_path)
    
    # 2. Classify via LLM
    metadata = classify_document(text, file_path.name)
    
    # 3. Relocate safely (this also handles cataloging internally)
    dest_path = relocate_file(
        source_path=file_path, 
        metadata=metadata, 
        extraction_method=ext_method
    )
    
    return dest_path, metadata, ext_method
