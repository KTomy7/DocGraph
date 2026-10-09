"""Unit tests for the SQLite document catalog & deduplication layer."""

import pytest
from src.catalog import (
    init_catalog,
    catalog_document,
    is_document_cataloged,
    search_catalog,
    get_catalog_entry_by_hash,
)
from src.classifier import DocumentMetadata

@pytest.fixture
def catalog_db(tmp_path):
    db_path = tmp_path / "catalog.db"
    assert init_catalog(db_path) is True
    return db_path

def test_catalog_lifecycle(tmp_path, catalog_db):
    test_hash = "mock_hash_1234567890"
    assert not is_document_cataloged(test_hash, db_path=catalog_db)

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
        db_path=catalog_db,
    )

    assert is_document_cataloged(test_hash, db_path=catalog_db)
    record = get_catalog_entry_by_hash(test_hash, db_path=catalog_db)
    assert record["issuer"] == "TUClujNapoca"
    assert record["category"] == "University"

    assert len(search_catalog(query="TUCluj", db_path=catalog_db)) == 1
    assert len(search_catalog(category="University", db_path=catalog_db)) == 1
    assert search_catalog(query="UnknownXYZ", db_path=catalog_db) == []


def test_init_catalog_reports_success(catalog_db):
    assert catalog_db.exists()


def test_init_catalog_reports_failure(catalog_db):
    database_directory = catalog_db
    database_directory.unlink()
    database_directory.mkdir()

    assert init_catalog(database_directory) is False
    