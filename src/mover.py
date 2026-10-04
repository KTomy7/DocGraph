"""
DocGraph - Safe File Relocation & Archiving
Handles integrity-verified atomic file moves into categorized archive structures.
"""

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from src.config import ARCHIVE_DIR
from src.classifier import DocumentMetadata


def calculate_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for integrity and deduplication."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def relocate_file(source_path: Path, metadata: DocumentMetadata) -> Path:
    """
    Atomically moves a document from inbox into the categorized archive.
    Verifies SHA-256 before the final atomic rename to detect data corruption.

    The source and destination must be on the same filesystem because
    ``os.replace`` is atomic only for same-filesystem moves.
    
    Returns:
        Path: The absolute path to the archived file.
    """
    source_path = Path(source_path).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    target_category_dir = (ARCHIVE_DIR / metadata.category).resolve()
    target_category_dir.mkdir(parents=True, exist_ok=True)

    dest_filename = metadata.canonical_filename
    target_path = target_category_dir / dest_filename

    # Handle collisions if a file with identical name already exists
    counter = 1
    base_stem = target_path.stem
    ext = target_path.suffix
    while target_path.exists():
        target_path = target_category_dir / f"{base_stem}_{counter}{ext}"
        counter += 1

    # 1. Check original hash.
    original_hash = calculate_sha256(source_path)

    # 2. Copy and verify a temporary file in the target directory. Keeping
    # it in the target directory ensures the final rename stays same-filesystem.
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=target_category_dir,
            prefix=f".{dest_filename}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)

        shutil.copy2(source_path, temp_path)
        with temp_path.open("rb") as temp_file:
            os.fsync(temp_file.fileno())

        archived_hash = calculate_sha256(temp_path)
        if original_hash != archived_hash:
            raise IOError(f"Integrity check failed while archiving {source_path.name}")

        # 3. Publish the verified file atomically. This fails with EXDEV
        # rather than falling back to a non-atomic copy/delete.
        os.replace(temp_path, target_path)
        temp_path = None

        # The verified destination is now durable; remove the source last.
        source_path.unlink()
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return target_path
