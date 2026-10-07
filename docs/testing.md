# Testing and Verification Guide

This guide details the testing architecture, environment configuration, command-line usage, and automated continuous integration (CI) guardrails for the DocGraph project.

---

## 1. Test Architecture & Structure

DocGraph separates fast, deterministic offline tests from resource-heavy local LLM inference to maintain high testing speeds and allow seamless cloud CI execution.

```text
tests/
├── check_env.py             # Pre-flight environment check (Milestone 1)
├── test_catalog.py          # SQLite database schema, CRUD, deduplication, search
├── test_classifier.py       # Pydantic schema validation, date sanitization, dynamic categories
├── test_extractor.py        # Native digital PDF parsing and high-res OCR fallback
├── test_mover.py            # Atomic relocation and SHA-256 pre/post integrity checks
└── test_classifier_mover.py # End-to-end integration test (requires local Ollama)
```

### Test Tiers

1. **Unit Tests (Fast & CI-Safe):**
   * **`test_catalog.py`**: Verifies table schemas, duplicate hash detection via SHA-256, atomic inserts, and keyword/category search queries.
   * **`test_extractor.py`**: Validates digital extraction via PyMuPDF, whitespace/null-byte cleanup, and Tesseract 300 DPI OCR fallback across Romanian, Hungarian, Spanish, and English.
   * **`test_mover.py`**: Validates safe atomic copy, conflict renaming (`_1`, `_2`), source deletion only upon verified checksum match, and corruption abort logic.
   * **`test_classifier.py`**: Validates Pydantic schema generation, filename sanitization, date normalization, and fallback to `Miscellaneous`.

2. **Integration Tests (`@pytest.mark.integration`):**
   * Verifies live inference against Ollama (`qwen2.5:14b`).
   * Automatically excluded on headless CI runners lacking GPU acceleration or local Ollama daemons.

---

## 2. Configuration & Setup

### Environment Dependencies
Make sure test and coverage packages are installed in your active virtual environment:

```bash
pip install pytest pytest-cov pytest-mock
```

Ensure they are locked in `requirements.txt`:
```text
pytest>=8.0.0
pytest-cov>=5.0.0
pytest-mock>=3.14.0
```

### Pytest Configuration (`pytest.ini`)
The project root must contain `pytest.ini` with standard execution settings:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
pythonpath = .
norecursedirs = .venv data dist build
addopts = -ra -q --strict-markers
markers =
    integration: tests requiring a live Ollama instance and local models
```

---

## 3. Running Tests Locally

Always ensure your virtual environment is active before running tests:

```bash
source .venv/bin/activate
```

### Run All Standard Unit Tests (Recommended)
Excludes heavy Ollama LLM integration tests:
```bash
pytest -m "not integration"
```

### Run Full Test Suite (Including Live Ollama)
Ensure `ollama serve` is running and `qwen2.5:14b` is pulled:
```bash
pytest
```

### Run a Single Test File
```bash
pytest tests/test_catalog.py
pytest tests/test_extractor.py
pytest tests/test_mover.py
```

### Run Specific Tests by Name or Pattern
```bash
pytest -k "test_catalog_lifecycle"
pytest -k "ocr"
```

### Verbose Execution with Print Statements
```bash
pytest -s -v tests/test_catalog.py
```

---

## 4. Code Coverage Verification

DocGraph enforces a minimum code coverage target of **80%** across the `src/` codebase.

### Run with Terminal Coverage Output
Displays coverage percentages and specific un-covered lines:
```bash
pytest -m "not integration" --cov=src --cov-report=term-missing tests/
```

### Enforce Coverage Threshold Locally
Fails with a non-zero exit code if coverage is below 80%:
```bash
pytest -m "not integration" --cov=src --cov-fail-under=80 tests/
```

### Generate and View HTML Coverage Report
```bash
pytest -m "not integration" --cov=src --cov-report=html:coverage_html tests/
open coverage_html/index.html
```

---

## 5. Automated CI Workflow (GitHub Actions)

Continuous integration is handled by `.github/workflows/coverage-guard.yml` on every `push` and `pull_request` to `main` or `master`.

### Automated Pipeline Tasks
1. Provision an Ubuntu runner with Python 3.12.
2. Install system packages: `tesseract-ocr`, `tesseract-ocr-ron`, `tesseract-ocr-hun`, and `tesseract-ocr-spa`.
3. Run unit tests with `pytest -m "not integration"`.
4. Enforce `--cov-fail-under=80` (build fails if coverage drops).
5. Append a Markdown summary table to the GitHub Actions Job Summary.
6. Upload the HTML coverage report as a downloadable build artifact (retained for 14 days).

---

## 6. Pre-Flight System Check (`check_env.py`)

To check the host environment outside of pytest (such as verifying Homebrew paths, Ollama connectivity, and model availability):

```bash
python tests/check_env.py
```

A return code of `0` indicates the host machine has all storage paths, Tesseract binaries, and local LLM models ready for ingestion.