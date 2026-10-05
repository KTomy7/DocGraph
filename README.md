# DocGraph 📁🕸️

A private, local AI assistant that organizes your personal documents and lets you search them using a Knowledge Graph.

No cloud uploads, no subscriptions, and no leaked data. Everything runs 100% on your machine.

---

## What Does DocGraph Do?

1. **Sorts & Renames Files Automatically:**  
   Drop unorganized PDFs, receipts, or scans into an `Inbox` folder. DocGraph reads the text, figures out what the document is (e.g., identity card, university diploma, rental lease, tax filing), gives it a clean name like `2024-06-15_Housing_Landlord_LeaseAgreement.pdf`, and moves it into the right category folder.

2. **Connects Related Information (Knowledge Graph):**  
   Instead of just looking for matching keywords, DocGraph understands how your files connect over time. If you ask *"What was the deposit for my previous apartment?"*, it traverses the connection between you, your past lease, and the deposit clause inside that specific contract.

3. **Works with Local Folders & iCloud Drive:**  
   You can run and test it completely on your local drive, then point it to your Apple iCloud Drive folder whenever you are ready.

---

## How It Works (Simple Pipeline)

```text
[ 00_Inbox ] ──► Read Text & OCR ──► Local LLM Classifies ──► Move to Archive ──► Index to Graph
```

- **OCR & Extraction:** Reads digital text using PyMuPDF and scans images using Tesseract OCR.
- **Local AI (Ollama):** Uses `qwen2.5:7b-instruct` to extract document dates, issuers, and categories.
- **Search Engine (LightRAG):** Builds an entity-relationship graph so you can ask natural-language questions and get the exact file path back.

---

## Requirements

- **macOS** (optimized for Apple Silicon / M-series chips) or Linux
- **Python 3.11+**
- **[Ollama](https://ollama.com/)** installed and running
- **Tesseract OCR** (on macOS: `brew install tesseract`)

---

## Quickstart

### 1. Download Local AI Models
Open your terminal and pull the two free local models:
```bash
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

### 2. Set Up the Project
```bash
# Clone or create your project directory
cd docgraph

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Basic Commands

#### Check System Status
Make sure Ollama is reachable and your folders are ready:
```bash
python cli.py doctor
```

#### Organize Files (Ingest)
Place your PDFs into `data/00_inbox/` and run:
```bash
python cli.py ingest
```
DocGraph will process, classify, rename, and archive each document.
Archived documents are recorded in the local SQLite catalog at `data/state.db`;
files whose SHA-256 hash is already cataloged are logged and skipped.

#### Search by Keyword or Category
Quickly find where a file is saved on disk:
```bash
python cli.py search --query "lease" --open
```
*(The `--open` flag opens the document directly in your default PDF viewer).*

#### Ask Questions (AI Retrieval)
Ask multi-hop or detail questions across your stored documents:
```bash
python cli.py ask "When does my passport expire?"
python cli.py ask "What is my car insurance policy number?"
```

---

## Folder Layout

```text
docgraph/
├── data/
│   ├── 00_inbox/      # Put new, unorganized files here
│   ├── archive/       # Organized files sorted by category
│   │   ├── Identity/
│   │   ├── Academic/
│   │   ├── Housing/
│   │   ├── Contracts/
│   │   ├── Finance/
│   │   └── Vehicle/
│   ├── rag/           # Knowledge graph and vector indexes
│   └── state.db       # Local SQLite database tracking processed files
├── src/               # Core application code
├── cli.py             # Command line interface
└── README.md
```
