# Testing and Verification Guide

This guide details the testing architecture, environment configuration, command-line usage, and automated continuous integration (CI) guardrails for the DocGraph project.

---

## 1. Test Architecture & Structure

DocGraph strictly separates fast, deterministic offline unit tests from resource-heavy local LLM inference and live database operations. This maintains high testing speeds and allows seamless cloud CI execution on headless runners.

```text
tests/
├── check_env.py             # Pre-flight environment check (Milestone 1)
├── test_catalog.py          # SQLite DB operations using isolated temporary databases
├── test_classifier.py       # Pydantic validation and "Nuclear Mocked" Ollama inference
├── test_extractor.py        # Mocked digital PDF parsing and Tesseract OCR fallback
├── test_mover.py            # Atomic relocation, hash verification, and DB rollback handling
└── test_integration.py      # End-to-end live testing (requires Ollama)
```

### Test Tiers

1. **Unit Tests (Fast & CI-Safe):**
   * **`test_catalog.py`**: Validates schema creation, deduplication, and search queries against dynamically generated temporary databases to prevent state leakage.
   * **`test_classifier.py`**: Intercepts all network/client calls to the Ollama API using aggressive mocking. Validates Pydantic schema coercion, date sanitization, and fallback to `Miscellaneous` on LLM failure.
   * **`test_extractor.py`**: Uses `pytest-mock` to simulate PyMuPDF contexts and Tesseract OCR, verifying string cleanup without requiring local binary dependencies.
   * **`test_mover.py`**: Tests the `os.replace` atomic copy logic, SHA-256 integrity checks, duplicate skips, and database rollback triggers within a temporary filesystem.

2. **Integration Tests (`@pytest.mark.integration`):**
   * **`test_integration.py`**: Verifies the actual end-to-end pipeline. It sends real text to the local `qwen2.5:14b` model via Ollama, evaluates the live JSON response, and executes a real atomic file move into a local archive.
   * Automatically skips execution if the local Ollama daemon is unresponsive.

---

## 2. Configuration & Setup

### Environment Dependencies
Ensure test and coverage packages are installed in your active virtual environment:

```bash
pip install pytest pytest-cov pytest-mock pylint requests
```

### Pytest Configuration (`pytest.ini`)
The project root must contain `pytest.ini` to register markers and suppress third-party SWIG warnings:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
pythonpath = .
norecursedirs = .venv data dist build
addopts = -ra -q --strict-markers
markers =
    integration: tests requiring a live Ollama instance and local models
filterwarnings =
    ignore:.*SwigPy.*:DeprecationWarning
    ignore:.*swigvarlink.*:DeprecationWarning
```

---

## 3. Running Tests Locally

Always ensure your virtual environment is active: `source .venv/bin/activate`

### Run All Standard Unit Tests (Recommended for Active Development)
Executes the fast, offline mock suite and skips the live LLM:
```bash
pytest -m "not integration"
```

### Run the Full Suite (Unit + Live Integration)
Requires `ollama serve` to be running with the target model pulled:
```bash
pytest -v
```

### Run ONLY the Live Integration Tests
```bash
pytest -m "integration" -v
```

### Run a Single File or Specific Test
```bash
pytest tests/test_mover.py
pytest -k "test_relocate_file_atomic_success"
```

---

## 4. Code Coverage Verification

DocGraph enforces a strict minimum code coverage target of **80%** across the `src/` codebase.

### Run with Terminal Coverage Output
Displays coverage percentages and specific un-covered lines for the offline suite:
```bash
pytest -m "not integration" --cov=src --cov-report=term-missing tests/
```

### Enforce Coverage Threshold Locally
Fails with a non-zero exit code if coverage drops below the 80% guardrail:
```bash
pytest -m "not integration" --cov=src --cov-fail-under=80 tests/
```

---

## 5. Automated CI Workflow (GitHub Actions)

Continuous integration is handled by `.github/workflows/coverage-guard.yml` on every `push` and `pull_request` to `main`.

### Pipeline Stages:
1. **Provision Environment:** Boots an Ubuntu runner with Python 3.12.
2. **Install Dependencies:** Installs `pytest`, `pytest-mock`, `pylint`, and local requirements.
3. **Static Analysis:** Runs `pylint src/ tests/ --disable=C,R` to catch syntax and import errors immediately.
4. **Offline Test Suite:** Executes `pytest -m "not integration"`.
5. **Coverage Guardrail:** Enforces `--cov-fail-under=80`. If coverage drops, the build fails.
6. **Artifact Generation:** Appends a Markdown coverage table to the GitHub Actions Job Summary and uploads the full HTML report as a downloadable artifact.

---

## 6. Pre-Flight System Check (`check_env.py`)

To check the host environment outside of pytest (such as verifying Homebrew paths, Ollama connectivity, and model availability)[cite: 1]:

```bash
python tests/check_env.py
```

A return code of `0` indicates the host machine has all storage paths, Tesseract binaries, and local LLM models ready for ingestion.