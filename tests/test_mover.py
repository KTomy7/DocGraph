"""Unit tests for safe atomic file relocation."""

import pytest
from src.classifier import DocumentMetadata
from src.mover import calculate_sha256, relocate_file

@pytest.fixture
def mover_setup(tmp_path, monkeypatch):
    """Sets up isolated archive and database paths for mover tests."""
    test_archive = tmp_path / "archive"
    test_db = tmp_path / "test_state.db"
    monkeypatch.setattr("src.mover.ARCHIVE_DIR", test_archive)
    return test_archive, test_db

def test_relocate_file_atomic_success(tmp_path, mover_setup):
    test_db = mover_setup
    
    source_file = tmp_path / "inbox_doc.pdf"
    source_file.write_bytes(b"%PDF-1.4\nMock file content payload")
    orig_hash = calculate_sha256(source_file)

    meta = DocumentMetadata(
        category="Contracts",
        document_type="Agreement",
        issuer="PartnerCompany",
        document_date="2024-05-01",
        canonical_filename="2024-05-01_Contracts_PartnerCompany_Agreement.pdf",
    )

    # Execute with isolated database path
    dest_file = relocate_file(source_file, meta, db_path=test_db)

    assert dest_file.exists()
    assert calculate_sha256(dest_file) == orig_hash
    assert not source_file.exists() # Source should be unlinked

def test_relocate_file_duplicate_skip(tmp_path, mover_setup):
    test_db = mover_setup
    
    source_file = tmp_path / "inbox_doc.pdf"
    source_file.write_bytes(b"%PDF-1.4\nDuplicate payload")
    
    meta = DocumentMetadata(
        category="Contracts",
        document_type="Agreement",
        issuer="PartnerCompany",
        document_date="2024-05-01",
        canonical_filename="dup.pdf",
    )

    # First move
    first_dest = relocate_file(source_file, meta, db_path=test_db)
    
    # Recreate the source file with identical content
    source_file.write_bytes(b"%PDF-1.4\nDuplicate payload")
    
    # Second move should detect duplicate via DB hash and return early
    second_dest = relocate_file(source_file, meta, db_path=test_db)
    
    assert first_dest == second_dest
    assert source_file.exists() # Source remains untouched because it was skipped

def test_relocate_file_rollback_on_db_failure(tmp_path, mover_setup, mocker):
    test_archive, test_db = mover_setup
    
    source_file = tmp_path / "inbox_doc.pdf"
    source_file.write_bytes(b"%PDF-1.4\nFailing payload")
    
    meta = DocumentMetadata(
        category="Contracts",
        document_type="Agreement",
        issuer="PartnerCompany",
        document_date="2024-05-01",
        canonical_filename="fail.pdf",
    )

    # Force the database insertion to crash
    mocker.patch("src.mover.catalog_document", side_effect=Exception("DB Error"))

    with pytest.raises(Exception, match="DB Error"):
        relocate_file(source_file, meta, db_path=test_db)

    # The rollback should have deleted the copied archive file and kept the inbox file
    assert source_file.exists()
    assert not (test_archive / "Contracts" / "fail.pdf").exists()
    