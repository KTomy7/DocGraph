"""
DocGraph - Core Processing Pipeline
Orchestrates text extraction, LLM classification, atomic relocation, and cataloging.
"""

import logging
from pathlib import Path
from typing import Tuple
from src.extractor import extract_text
from src.classifier import classify_document, DocumentMetadata
from src.mover import relocate_file
from src.rag_engine import index_document

logger = logging.getLogger(__name__)


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
    
    # 3. Relocate & Catalog
    dest_path = relocate_file(
        source_path=file_path, 
        metadata=metadata, 
        extraction_method=ext_method
    )
    
    # 4. Knowledge Graph Indexing (best-effort; do not block document ingestion)
    try:
        index_document(text, metadata.canonical_filename)
    except Exception:
        logger.exception(
            "Knowledge graph indexing failed for %s; continuing without graph metadata.",
            file_path,
        )
    
    return dest_path, metadata, ext_method
