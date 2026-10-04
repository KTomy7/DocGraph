# --- Base Directories ---
"""
DocGraph - Central Configuration Module
Defines directory layouts, local models, and system paths.
"""

from pathlib import Path
from typing import List
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# File Processing Pipelines
INBOX_DIR = DATA_DIR / "00_inbox"
ARCHIVE_DIR = DATA_DIR / "archive"
RAG_DIR = DATA_DIR / "rag"

# Database Path
STATE_DB_PATH = DATA_DIR / "state.db"

# Canonical Document Categories
VALID_CATEGORIES: List[str] = [
    "Identity",
    "Academic",
    "Housing",
    "Contracts",
    "Finance",
    "Vehicle",
    "Miscellaneous",
]

# --- Ollama & Local Model Settings ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("DOCGRAPH_LLM_MODEL", "qwen2.5:14b")
EMBEDDING_MODEL = os.getenv("DOCGRAPH_EMBED_MODEL", "nomic-embed-text")

# --- OCR & Text Settings ---
MIN_DIGITAL_TEXT_CHARS = 50  # Fallback to Tesseract if fewer characters extracted


def init_filesystem() -> None:
    """Ensure all required folders exist on startup."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    RAG_DIR.mkdir(parents=True, exist_ok=True)

    for category in VALID_CATEGORIES:
        (ARCHIVE_DIR / category).mkdir(parents=True, exist_ok=True)


# Run initialization on import
init_filesystem()
