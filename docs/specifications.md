# DocGraph 📁🕸️

**A Privacy-First, Air-Gapped Personal Document Management & Relational Assistant**

## 1. Executive Summary & Project Overview

**DocGraph** is a self-hosted, local-first document retrieval assistant and automatic filer designed specifically for personal sensitive records (national IDs, passports, university transcripts, diplomas, apartment leases, employment contracts, tax filings, and insurance policies).

Unlike traditional document management setups that either dump files into flat folders or depend on complex multi-container web stacks (such as Paperless-ngx with Redis, Celery, and PostgreSQL), DocGraph runs as an integrated, Python-based CLI application. It pairs an atomic file-organization state machine with **LightRAG** (dual-level Knowledge Graph Retrieval-Augmented Generation) backed by local LLMs via **Ollama**.

### Core Guarantees

* **100% Air-Gapped & Private:** Zero third-party telemetry, zero external cloud LLM calls. Everything executes on local hardware.
* **Apple Silicon Accelerated:** Fully optimized for unified memory and Metal GPU acceleration (ideal for MacBook Pro Apple Silicon architectures).
* **Deterministic Organization:** Documents are parsed, classified against a strict JSON schema, canonically renamed, and moved into organized folders.
* **Relational Multi-Hop Queries:** Uses a knowledge graph to connect entities across time (e.g., matching a lease agreement to a university enrollment year without requiring keyword overlaps).
* **iCloud Bridge Ready:** Designed to test entirely in local staging folders first, with seamless transition to Apple iCloud Drive directories (`~/Library/Mobile Documents/com~apple~CloudDocs/...`).

## 2. Hardware Feasibility & Sizing

### Target Hardware: MacBook Pro 14" (Apple Silicon, 24 GB Unified Memory)

The recommended local stack runs comfortably within a 24 GB unified memory footprint:

| Component | Model / Technology | Memory Footprint | Context / Bandwidth |
|---|---|---|---|
| **LLM Inference** | `qwen2.5:7b-instruct` (q4_k_m) | ~4.5 GB – 5.2 GB VRAM | High extraction accuracy, strict JSON compliance |
| **Embedding Engine** | `nomic-embed-text` | ~450 MB – 600 MB VRAM | 8,192 token window, fast retrieval |
| **Graph & Vector Stores** | NetworkX + NanoVectorDB | ~300 MB RAM | Embedded in-memory / disk cache |
| **System Headroom** | macOS & CLI Engine | ~18 GB RAM remaining | Ample headroom for daily multitasking |

### Why Paperless-ngx Is Not Required

Paperless-ngx is an excellent web-based archival platform, but it adds substantial architectural weight:

* Requires multiple long-running Docker containers (PostgreSQL, Redis, Web UI, Celery workers).
* Imposes its own internal file management and tag database.
* DocGraph replaces the necessary parts with:
  1. **OCR / Text Parsing:** PyMuPDF (`fitz`) for digital PDFs + `pytesseract` for scanned records.
  2. **Metadata & Deduplication:** SQLite3 (`state.db`).
  3. **File Organization:** Python standard file-system operations.
  4. **Intelligence:** LightRAG + Ollama.

## 3. Technology Stack

| Layer | Selected Tool | Role & Justification |
|---|---|---|
| **Runtime** | Python 3.11+ | Modern typing, high-performance async I/O, ML ecosystem compatibility. |
| **CLI & Interface** | `Typer` + `Rich` | Subcommand parsing, progress animations, colored tables, and error diagnostics. |
| **PDF Extraction** | `PyMuPDF` (`fitz`) | Fast extraction of embedded digital PDF text layers. |
| **OCR Fallback** | `pytesseract` (Tesseract) | Robust fallback OCR engine for photo scans, receipts, and identity documents. |
| **Local Inference Host** | `Ollama` | Manages local model loading and Apple Silicon Metal GPU acceleration. |
| **Inference LLM** | `qwen2.5:7b-instruct` | State-of-the-art 7B parameter model for instruction following and structured JSON. |
| **Embedding Model** | `nomic-embed-text` | High-accuracy semantic vector representations with an 8k context window. |
| **Graph RAG Core** | `LightRAG` (`lightrag-hku`) | Incremental dual-level graph generation (Entity/Relation graph + vector chunks). |
| **Graph Store** | `NetworkX` | Embedded, zero-maintenance GraphML file serialization. |
| **Vector Store** | `NanoVectorDB` | File-based vector index embedded directly into the workspace. |
| **State Tracking** | `SQLite3` | Local database for SHA-256 hashes, paths, classification records, and statuses. |

## 4. End-to-End System Topology

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                    User / CLI Interface (Typer + Rich)                 │
 │             python cli.py [ingest | search | ask | doctor]             │
 └───────────────────┬────────────────────────────────┬───────────────────┘
                     │                                │
                     ▼                                ▼
       ┌───────────────────────────┐    ┌───────────────────────────┐
       │     Ingestion Pipeline    │    │   Dual-Engine Retrieval   │
       │                           │    │                           │
       │ 1. Guard & Deduplication  │    │ 1. Exact Metadata Search  │
       │    (SHA-256 vs SQLite)    │    │    (SQLite path lookup)   │
       │ 2. Text Normalization     │    │                           │
       │    (PyMuPDF / Tesseract)  │    │ 2. Relational Graph Query │
       │ 3. Strict Schema Extract  │    │    (LightRAG Hybrid:      │
       │    (Ollama JSON)          │    │     GraphML + NanoDB)     │
       │ 4. Atomic File Mover      │    │                           │
       │ 5. Graph RAG Indexing     │    │ 3. Synthesis & Open Hook  │
       └─────────────┬─────────────┘    └─────────────▲─────────────┘
                     │                                │
                     ▼                                │
       ┌──────────────────────────────────────────────┴─────────────┐
       │                   Local Storage Subsystems                 │
       │                                                            │
       │  • Incoming:   ./data/00_inbox/                            │
       │  • Archive:    ./data/archive/{Category}/{CanonicalName}   │
       │  • State DB:   ./data/state.db (SQLite3)                   │
       │  • Graph DB:   ./data/rag/graph_chunk_entity_relation.xml  │
       │  • Vectors:    ./data/rag/vdb_chunks.json                  │
       └────────────────────────────────────────────────────────────┘
```

## 5. Storage Architecture & Directory Layout

### Complete File Tree

```text
docgraph/
├── data/
│   ├── 00_inbox/                               # Drop point for incoming PDFs and scans
│   ├── archive/                                # Structured target directory tree
│   │   ├── Identity/                           # Passports, IDs, Birth Certificates
│   │   ├── Academic/                           # Degrees, Diplomas, Transcripts
│   │   ├── Housing/                            # Leases, Tenancy Contracts, Utility Bills
│   │   ├── Contracts/                          # Employment Contracts, NDAs, Services
│   │   ├── Finance/                            # Tax Declarations, Invoices, Bank Letters
│   │   └── Vehicle/                            # Car Insurance, Title, Road Inspections
│   ├── rag/                                    # LightRAG internal persistence
│   │   ├── graph_chunk_entity_relation.graphml # NetworkX Graph topology
│   │   ├── vdb_chunks.json                     # Vector index for text chunks
│   │   ├── vdb_entities.json                   # Vector index for extracted entities
│   │   └── kv_store_*.json                     # Caches and document mappings
│   └── state.db                                # SQLite file-tracking database
│
├── src/
│   ├── __init__.py
│   ├── config.py                               # Paths, model aliases, and thresholds
│   ├── catalog.py                              # SQLite schema, hash indexing, queries
│   ├── extractor.py                            # PyMuPDF + Tesseract fallback logic
│   ├── classifier.py                           # Ollama structured JSON prompt handler
│   ├── mover.py                                # Atomic move, rename, and verification
│   └── rag_engine.py                           # LightRAG initialization and wrappers
│
├── cli.py                                      # Command-line interface definitions
├── requirements.txt
└── README.md
```

### Where Data and Relationships Are Stored

1. **Raw Documents (`data/archive/`):** Original physical PDF files, renamed and organized.
2. **Entity Graph (`data/rag/graph_chunk_entity_relation.graphml`):** XML-based adjacency list containing labeled nodes (`Person`, `Organization`, `Asset`, `Document`, `Date`) and edges (`ISSUED_BY`, `PERTAINS_TO`, `COVERS`, `EXPIRES_ON`, `PAID_TO`).
3. **Vector Embeddings (`data/rag/vdb_*.json`):** 512-token chunk embeddings and entity descriptions generated by `nomic-embed-text`.
4. **Relational State DB (`data/state.db`):** SQLite database recording document checksums, ingestion timestamps, original paths, and archive paths.

## 6. Document Lifecycle & State Machine

To prevent file loss, sync loops, or indexing corruptions, files follow a strict one-way state progression:

```text
[Inbox PDF] ──► [Hash Check] ──► [Extract Text] ──► [Classify] ──► [Safe Move] ──► [Index Graph]
```

### Detailed Pipeline Steps

1. **Deduplication & Lock Verification:**
   * Calculate file SHA-256 hash.
   * Query `state.db`. If the hash exists, log the duplicate, skip processing, and leave the inbox file in place.
   * Ensure write operations are closed before reading (prevents partial reads during large file copies).
2. **Text Normalization:**
   * Run fast digital text extraction via `PyMuPDF`.
   * If extracted characters are fewer than 50 (e.g., scanned images or IDs), trigger OCR via `pytesseract`.
3. **Strict Classification & Extraction:**
   * Send the extracted text snippet to Ollama (`qwen2.5:7b-instruct`) enforcing the following JSON schema:
     ```json
     {
       "category": "Identity | Academic | Housing | Contracts | Finance | Vehicle",
       "document_type": "string",
       "issuer": "string",
       "document_date": "YYYY-MM-DD or null",
       "canonical_filename": "YYYY-MM-DD_Category_Issuer_DocType.pdf"
     }
     ```
4. **Atomic Relocation:**
   * Destination path is determined: `data/archive/{category}/{canonical_filename}`.
   * Copy file to target $\to$ Verify hash equality $\to$ Unlink original from `00_inbox/`.
   * Record entry in `state.db`.
5. **Incremental Graph Indexing:**
   * Dispatch raw text and document metadata to `LightRAG.insert()`.
   * LightRAG extracts entity nodes, links edges, and embeds chunks without requiring a full re-index of historical files.

## 7. Dual-Retrieval Mechanics

When querying the assistant, the engine routes requests through two complementary layers:

### A. Metadata & Exact Path Search (`search`)
* Designed for fast file retrieval by date, issuer, or category without running an LLM.
* Queries `state.db` directly.
* Supports an `--open` flag that launches the file immediately in the native macOS viewer (Preview.app).

### B. Relational Graph-RAG Query (`ask`)
* Designed for contextual, multi-hop, or synthesis questions across documents.
* **Query Flow:**
  1. Deconstructs the question to find target entities and relationships.
  2. Traverses graph paths (e.g., `Self` $\to$ `Rented` $\to$ `Apartment` $\to$ `Lease Document`).
  3. Pulls vector text chunks tied directly to those graph nodes.
  4. Returns the synthesized answer along with the exact source file path.

## 8. Command-Line Interface (CLI) Specification

```bash
# Check environment health, Ollama status, and models
python cli.py doctor

# Ingest and organize all pending files in the inbox
python cli.py ingest

# Search document records by keyword or category
python cli.py search --query "lease" --open

# Ask a contextual question using the Knowledge Graph
python cli.py ask "When does my car insurance expire?"
python cli.py ask "What was the deposit amount on my apartment in Cartagena?"
```

## 9. Apple iCloud Drive Migration Path

Once local testing in `./data/00_inbox/` and `./data/archive/` is verified, migrating to iCloud Drive requires changing two path constants in `src/config.py`:

```python
# Transition from local storage to native iCloud Drive
ICLOUD_BASE = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Documents"
INBOX_DIR = ICLOUD_BASE / "00_Inbox"
ARCHIVE_DIR = ICLOUD_BASE / "Archive"
```

Because macOS mirrors iCloud Drive as a standard local POSIX file system, the same file-locking, hashing, and moving logic operates without needing third-party cloud sync containers or expired API tokens.