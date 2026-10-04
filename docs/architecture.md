# DocGrahp: Local Graph-RAG Personal Document Management System

## 1. System Philosophy & Objectives
- **Local-First & Air-Gapped:** Zero external API calls. All OCR, metadata classification, graph extraction, and vector searches run on local Apple Silicon hardware.
- **Relational Intelligence:** Uses Knowledge Graphs (LightRAG) over pure vector chunking to answer multi-hop personal queries across entities, assets, and temporal milestones.
- **Deterministic File Organization:** Strict JSON schema validation for automated categorization, canonical renaming, and relocation into structured directories (with direct iCloud Drive compatibility).
- **Lightweight Architecture:** Eliminates heavy external daemon suites (e.g., Paperless-ngx) in favor of a lean, scriptable CLI tool using SQLite, NetworkX, and NanoVectorDB.

---

## 2. Technology Stack & Sizing

| Component | Technology | Role & Justification |
|---|---|---|
| **Runtime** | Python 3.11+ | Native support for machine learning, graph math, and system automation. |
| **CLI Framework** | `Typer` + `Rich` | Type-safe CLI commands, interactive progress displays, and formatted terminal outputs. |
| **PDF & Text Extraction** | `PyMuPDF` (`fitz`) | Fast digital text parsing. |
| **OCR Fallback** | `pytesseract` | Optical character recognition for scanned receipts, certificates, and ID cards. |
| **Inference Engine** | `Ollama` | Local LLM host leveraging Apple Silicon Metal GPU acceleration. |
| **Language Model (LLM)**| `qwen2.5:7b-instruct` | High-precision instruction following, strict JSON formatting, and multilingual extraction. |
| **Embedding Model** | `nomic-embed-text` | Compact footprint (137M parameters), 8k token context window. |
| **Graph RAG Engine** | `LightRAG` (`lightrag-hku`) | Incremental dual-level graph construction (Entity/Relation + Chunk embeddings). |
| **Graph Store** | `NetworkX` | Embedded, file-based GraphML persistence (`.graphml`). |
| **Vector Store** | `NanoVectorDB` | Embedded, zero-configuration local vector storage. |
| **State Tracking** | `SQLite3` | Hash deduplication, ingestion states, and physical path indices. |

---

## 3. Directory Layout

```text
DocGraph/
├── data/
│   ├── 00_inbox/                  # Local staging folder (future iCloud Inbox)
│   ├── archive/                   # Deterministic long-term storage
│   │   ├── Identity/              # Passports, IDs, Birth Certificates
│   │   ├── Academic/              # Diplomas, Transcripts, Certifications
│   │   ├── Housing/               # Leases, Tenancy Agreements, Utilities
│   │   ├── Contracts/             # Employment, NDAs, Service Agreements
│   │   ├── Finance/               # Taxes, Invoices, Bank Statements
│   │   └── Vehicle/               # Insurance, Registration, Inspection
│   ├── rag/                       # LightRAG internal stores
│   │   ├── graph_chunk_entity_relation.graphml
│   │   ├── vdb_chunks.json
│   │   └── vdb_entities.json
│   └── state.db                   # SQLite file-tracking database
│
├── src/
│   ├── __init__.py
│   ├── config.py                  # Storage paths, Ollama models, and constants
│   ├── db.py                      # SQLite state management and deduplication
│   ├── extractor.py               # PyMuPDF digital parser + Tesseract OCR fallback
│   ├── classifier.py              # Ollama structured JSON extractor
│   ├── mover.py                   # Atomic file rename and directory dispatch
│   └── rag_engine.py              # LightRAG initialization, indexing, and querying
│
├── cli.py                         # Typer CLI application entry point
├── requirements.txt
└── README.md
```

---


## 4. Ingestion Mechanism & File State Machine
To guarantee file integrity, files follow an atomic lifecycle:

```text
[Inbox PDF] 
     │
     ▼
[Step 1: Ingestion Guard]
  ├─ Check file is not active/locked
  ├─ Calculate SHA-256
  └─ Query SQLite: If hash exists -> Log duplicate & SKIP
     │
     ▼
[Step 2: Text Extraction]
  ├─ Try native digital text extraction via PyMuPDF
  └─ If text length < 50 chars -> Trigger Tesseract OCR
     │
     ▼
[Step 3: Strict Metadata Classification]
  └─ Send snippet (first 3000 chars) to Ollama with JSON schema:
     {
       "category": "Academic",
       "document_type": "Diploma",
       "issuer": "TU_Cluj_Napoca",
       "document_date": "2024-07-15",
       "canonical_filename": "2024-07-15_Academic_TU_Cluj_Napoca_Diploma.pdf"
     }
     │
     ▼
[Step 4: Atomic Physical Move]
  ├─ Target: ./data/archive/{category}/{canonical_filename}
  ├─ Copy file to destination -> Verify integrity -> Remove from ./00_inbox/
  └─ Insert record into SQLite (hash, original_name, archive_path, timestamp)
     │
     ▼
[Step 5: Incremental Graph RAG Indexing]
  └─ Pass extracted text and metadata into LightRAG (inserts nodes, edges, vectors)
```

---

## 5.Retrieval & Search Mechanism
The CLI supports two distinct query workflows:

### A. Exact Attribute & Path Lookup (`search`)
For finding physical files without invoking heavy LLM reasoning.

- **Command:**

```bash
python cli.py search --category Academic --year 2024
```

- **Mechanism:** Direct SQLite query returning a Rich-formatted table of file paths, issuers, and dates. Includes an `--open` flag to launch the file directly in the system viewer (e.g., Preview on macOS).

### B. Relational Graph-RAG Query (`ask`)
For answering multi-hop, contextual, or detail-oriented questions.

- **Command:**

```bash
python cli.py ask "What was my deposit for the apartment in Cartagena?"
```

- **Mechanism:**

1. LightRAG extracts query entities (Apartment, Cartagena, Deposit).

2. Traverses the graph to resolve relationships: - Cartagena -> Apartment Lease Contract -> Deposit Clause

3. Pulls vector text chunks linked to those graph nodes.

4. Returns the synthesized answer along with the exact source file path and an option to open the document immediately.

---

## 6. CLI Command Specification

```bash
# Process all pending documents in data/00_inbox
python cli.py ingest

# Ask a contextual / relational question across documents
python cli.py ask "When does my car insurance expire?"

# Search document metadata directly
python cli.py search --query "passport" --open

# Inspect system status: Ollama connectivity, index stats, and file counts
python cli.py doctor
```