"""
DocGraph - Safe File Relocation & Archiving
Handles integrity-verified atomic file moves into categorized archive structures.
"""

import hashlib
import shutil
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
    Safely moves a document from inbox into the categorized archive.
    Verifies SHA-256 before and after copy to guarantee zero data corruption.
    
    Returns:
        Path: The absolute path to the archived file.
    """
    source_path = Path(source_path).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    target_category_dir = ARCHIVE_DIR / metadata.category
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

    # 1. Check original hash
    original_hash = calculate_sha256(source_path)

    # 2. Copy file to destination
    shutil.copy2(source_path, target_path)

    # 3. Verify destination hash matches original
    archived_hash = calculate_sha256(target_path)
    if original_hash != archived_hash:
        # Integrity check failed: clean up corrupt destination and abort
        target_path.unlink(missing_ok=True)
        raise IOError(f"Integrity check failed while archiving {source_path.name}")

    # 4. Remove original only after verified safe write
    source_path.unlink()

    return target_path
