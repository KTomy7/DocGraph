"""End-to-end integration tests requiring live services (Ollama, File System)."""

import pytest
import requests
from pathlib import Path
from src.classifier import classify_document, DocumentMetadata
from src.mover import relocate_file, calculate_sha256
from src.catalog import get_catalog_entry_by_hash
from src.config import OLLAMA_HOST

# Apply the integration marker to every test in this file automatically
pytestmark = pytest.mark.integration

def is_ollama_running():
    """Helper to check if Ollama is actively serving requests."""
    try:
        # Extract base URL in case OLLAMA_HOST includes /api/chat
        base_url = OLLAMA_HOST.split("/api")[0] if "/api" in OLLAMA_HOST else OLLAMA_HOST
        response = requests.get(base_url, timeout=2)
        return response.status_code == 200
    except Exception:
        return False

@pytest.mark.skipif(not is_ollama_running(), reason="Local Ollama daemon is not running.")
def test_full_pipeline_live(tmp_path, monkeypatch):
    """
    Tests the complete pipeline: Live LLM Classification -> Atomic Move -> Database Cataloging.
    """
    # 1. Setup isolated file system and database
    test_archive = tmp_path / "archive"
    test_db = tmp_path / "integration_state.db"
    
    monkeypatch.setattr("src.mover.ARCHIVE_DIR", test_archive)
    try:
        monkeypatch.setattr("src.config.ARCHIVE_DIR", test_archive)
    except Exception:
        pass

    # 2. Create a mock source document
    source_file = tmp_path / "raw_inbox_document.pdf"
    source_file.write_bytes(b"%PDF-1.4\nIntegrity payload for live test.")
    orig_hash = calculate_sha256(source_file)

    # 3. Define clear text to force the live LLM into a predictable response
    document_text = (
        "RESIDENTIAL LEASE AGREEMENT\n"
        "Date: 2024-10-05\n"
        "Landlord: RealEstateCorp\n"
        "Tenant: John Doe\n"
        "This document serves as a housing contract for apartment 4B."
    )
    
    # Restrict categories so the LLM has strict boundaries during the test
    monkeypatch.setattr("src.classifier.get_active_categories", lambda: ["Housing", "Miscellaneous"])

    # 4. EXECUTE LIVE LLM INFERENCE
    # This reaches out to your local hardware and forces the LLM to generate JSON
    metadata = classify_document(document_text, "lease.pdf")
    
    # 5. Verify live classification accuracy
    assert isinstance(metadata, DocumentMetadata)
    assert metadata.category == "Housing"
    assert "RealEstateCorp" in metadata.issuer
    assert metadata.document_date == "2024-10-05"

    # 6. EXECUTE LIVE FILE RELOCATION
    dest_file = relocate_file(
        source_path=source_file, 
        metadata=metadata, 
        db_path=test_db, 
        extraction_method="digital"
    )

    # 7. Verify atomic file operations
    assert dest_file.exists(), "The file was not moved to the archive."
    assert not source_file.exists(), "The source file was not deleted."
    assert calculate_sha256(dest_file) == orig_hash, "File corruption detected during move."

    # 8. Verify live database insertion
    db_entry = get_catalog_entry_by_hash(orig_hash, db_path=test_db)
    assert db_entry is not None, "Document was not cataloged in the SQLite database."
    assert db_entry["category"] == "Housing"
    assert db_entry["extraction_method"] == "digital"
    