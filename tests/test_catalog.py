"""Unit tests for the SQLite document catalog & deduplication layer."""

import pytest
from pathlib import Path
from src.catalog import (
    init_catalog,
    catalog_document,
    is_document_cataloged,
    search_catalog,
    get_catalog_entry_by_hash,
    get_catalog_connection,
)
from src.classifier import DocumentMetadata

@pytest.fixture(autouse=True)
def clean_db():
    init_catalog()
    test_hash = "mock_hash_1234567890"
    yield test_hash
    with get_catalog_connection() as conn:
        conn.execute("DELETE FROM documents WHERE sha256 = ?", (test_hash,))
        conn.commit()

def test_catalog_lifecycle(tmp_path, clean_db):
    test_hash = clean_db
    assert not is_document_cataloged(test_hash)

    metadata = DocumentMetadata(
        category="University",
        document_type="Transcript",
        issuer="TUClujNapoca",
        document_date="2024-02-15",
        canonical_filename="2024-02-15_University_TUClujNapoca_Transcript.pdf",
    )
    fake_target = tmp_path / metadata.canonical_filename

    catalog_document(
        sha256=test_hash,
        original_filename="transcript.pdf",
        metadata=metadata,
        archive_path=fake_target,
        extraction_method="digital",
    )

    assert is_document_cataloged(test_hash)
    record = get_catalog_entry_by_hash(test_hash)
    assert record["issuer"] == "TUClujNapoca"
    assert record["category"] == "University"

    assert len(search_catalog(query="TUCluj")) >= 1
    assert len(search_catalog(category="University")) >= 1
    assert len(search_catalog(query="UnknownXYZ")) == 0
    