"""Tests for the SQLite document catalog."""

from pathlib import Path

import pytest

from src.catalog import (
    catalog_document,
    get_catalog_connection,
    get_catalog_entry_by_hash,
    init_catalog,
    is_document_cataloged,
    search_catalog,
)
from src.classifier import DocumentMetadata
from src import mover


@pytest.fixture
def metadata() -> DocumentMetadata:
    return DocumentMetadata(
        category="University",
        document_type="Transcript",
        issuer="TUClujNapoca",
        document_date="2024-02-15",
        canonical_filename="2024-02-15_University_TUClujNapoca_Transcript.pdf",
    )


def test_catalog_document_and_search(tmp_path: Path, metadata: DocumentMetadata) -> None:
    db_path = tmp_path / "state.db"
    document_hash = "a" * 64

    init_catalog(db_path)
    assert not is_document_cataloged(document_hash, db_path)

    catalog_document(
        sha256=document_hash,
        original_filename="transcript_semester_1.pdf",
        metadata=metadata,
        archive_path=tmp_path / metadata.canonical_filename,
        extraction_method="digital",
        db_path=db_path,
    )

    assert is_document_cataloged(document_hash, db_path)
    record = get_catalog_entry_by_hash(document_hash, db_path)
    assert record is not None
    assert record["issuer"] == "TUClujNapoca"
    assert record["category"] == "University"
    assert len(search_catalog(query="TUCluj", db_path=db_path)) == 1
    assert len(search_catalog(category="University", db_path=db_path)) == 1
    assert search_catalog(query="NonExistentTermXYZ", db_path=db_path) == []


def test_catalog_update_preserves_created_at(
    tmp_path: Path, metadata: DocumentMetadata
) -> None:
    db_path = tmp_path / "state.db"
    document_hash = "b" * 64
    init_catalog(db_path)

    catalog_document(
        document_hash,
        "original.pdf",
        metadata,
        tmp_path / "first.pdf",
        "digital",
        db_path,
    )
    with get_catalog_connection(db_path) as connection:
        created_at = connection.execute(
            "SELECT created_at FROM documents WHERE sha256 = ?", (document_hash,)
        ).fetchone()[0]

    updated_metadata = metadata.model_copy(update={"issuer": "UpdatedIssuer"})
    catalog_document(
        document_hash,
        "updated.pdf",
        updated_metadata,
        tmp_path / "second.pdf",
        "ocr",
        db_path,
    )

    record = get_catalog_entry_by_hash(document_hash, db_path)
    assert record is not None
    assert record["issuer"] == "UpdatedIssuer"
    assert record["created_at"] == created_at


def test_search_treats_like_metacharacters_literally(
    tmp_path: Path, metadata: DocumentMetadata
) -> None:
    db_path = tmp_path / "state.db"
    init_catalog(db_path)
    catalog_document(
        "c" * 64,
        "report_2024.pdf",
        metadata,
        tmp_path / "report_2024.pdf",
        "digital",
        db_path,
    )

    assert search_catalog(query="%", db_path=db_path) == []
    assert len(search_catalog(query="report_", db_path=db_path)) == 1


def test_relocate_file_catalogs_and_skips_duplicate(
    tmp_path: Path,
    metadata: DocumentMetadata,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    archive_dir = tmp_path / "archive"
    db_path = tmp_path / "state.db"
    source_path = tmp_path / "incoming.pdf"
    source_path.write_bytes(b"document contents")
    monkeypatch.setattr(mover, "ARCHIVE_DIR", archive_dir)

    archived_path = mover.relocate_file(source_path, metadata, db_path)

    assert archived_path.exists()
    assert not source_path.exists()
    record = get_catalog_entry_by_hash(mover.calculate_sha256(archived_path), db_path)
    assert record is not None
    assert record["archive_path"] == str(archived_path)

    duplicate_path = tmp_path / "duplicate.pdf"
    duplicate_path.write_bytes(b"document contents")
    with caplog.at_level("INFO", logger="src.mover"):
        duplicate_archive_path = mover.relocate_file(duplicate_path, metadata, db_path)
    assert duplicate_archive_path == archived_path
    assert duplicate_path.exists()
    assert "Skipping duplicate document" in caplog.text
