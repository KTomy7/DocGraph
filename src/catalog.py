"""
DocGraph - Document Catalog & Deduplication Registry
Manages SQLite persistence for document metadata, hash fingerprints, and archive locations.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.config import STATE_DB_PATH
from src.classifier import DocumentMetadata


def get_catalog_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Returns a connection to the SQLite catalog database with dict-like row access."""
    path = db_path or STATE_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_catalog(db_path: Optional[Path] = None) -> bool:
    """Initialize the catalog and return whether setup completed successfully."""
    try:
        with get_catalog_connection(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    sha256 TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    canonical_filename TEXT NOT NULL,
                    archive_path TEXT NOT NULL,
                    category TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    issuer TEXT NOT NULL,
                    document_date TEXT,
                    extraction_method TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)
            # Indexes for fast lookup
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON documents(category);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_issuer ON documents(issuer);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_date ON documents(document_date);")
            conn.commit()
    except (OSError, sqlite3.Error):
        return False
    return True


def is_document_cataloged(sha256: str, db_path: Optional[Path] = None) -> bool:
    """Check if a document with this exact SHA-256 hash has already been registered."""
    init_catalog(db_path)
    with get_catalog_connection(db_path) as conn:
        cursor = conn.execute("SELECT 1 FROM documents WHERE sha256 = ?", (sha256,))
        return cursor.fetchone() is not None


def catalog_document(
    sha256: str,
    original_filename: str,
    metadata: DocumentMetadata,
    archive_path: Path,
    extraction_method: str,
    db_path: Optional[Path] = None,
) -> None:
    """Register a newly processed document into the catalog."""
    init_catalog(db_path)
    with get_catalog_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO documents (
                sha256,
                original_filename,
                canonical_filename,
                archive_path,
                category,
                document_type,
                issuer,
                document_date,
                extraction_method,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sha256) DO UPDATE SET
                original_filename = excluded.original_filename,
                canonical_filename = excluded.canonical_filename,
                archive_path = excluded.archive_path,
                category = excluded.category,
                document_type = excluded.document_type,
                issuer = excluded.issuer,
                document_date = excluded.document_date,
                extraction_method = excluded.extraction_method
            """,
            (
                sha256,
                original_filename,
                metadata.canonical_filename,
                str(archive_path.resolve()),
                metadata.category,
                metadata.document_type,
                metadata.issuer,
                metadata.document_date,
                extraction_method,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()


def search_catalog(
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Search indexed documents by category, issuer, type, or general keyword.
    """
    init_catalog(db_path)
    with get_catalog_connection(db_path) as conn:
        sql = "SELECT * FROM documents WHERE 1=1"
        params: List[Any] = []

        if category:
            sql += " AND category = ?"
            params.append(category)

        if query:
            sql += """
                AND (
                    canonical_filename LIKE ? ESCAPE '!'
                    OR issuer LIKE ? ESCAPE '!'
                    OR document_type LIKE ? ESCAPE '!'
                    OR original_filename LIKE ? ESCAPE '!'
                )
            """
            escaped_query = (
                query.replace("!", "!!").replace("%", "!%").replace("_", "!_")
            )
            wildcard = f"%{escaped_query}%"
            params.extend([wildcard, wildcard, wildcard, wildcard])

        sql += " ORDER BY document_date DESC, created_at DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def get_catalog_entry_by_hash(
    sha256: str, db_path: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """Retrieve full catalog record for a specific hash."""
    init_catalog(db_path)
    with get_catalog_connection(db_path) as conn:
        cursor = conn.execute("SELECT * FROM documents WHERE sha256 = ?", (sha256,))
        row = cursor.fetchone()
        return dict(row) if row else None
    