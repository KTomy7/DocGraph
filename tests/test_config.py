"""Unit tests for filesystem initialization."""

from src import config


def test_init_filesystem_reports_success(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INBOX_DIR", tmp_path / "00_inbox")
    monkeypatch.setattr(config, "ARCHIVE_DIR", tmp_path / "archive")
    monkeypatch.setattr(config, "RAG_DIR", tmp_path / "rag")
    monkeypatch.setattr(config, "CORE_CATEGORIES", ["Identity", "Miscellaneous"])

    assert config.init_filesystem() is True
    assert (tmp_path / "00_inbox").is_dir()
    assert (tmp_path / "archive" / "Identity").is_dir()
    assert (tmp_path / "archive" / "Miscellaneous").is_dir()
    assert (tmp_path / "rag").is_dir()


def test_init_filesystem_reports_failure(tmp_path, monkeypatch):
    inbox_file = tmp_path / "00_inbox"
    inbox_file.write_text("not a directory")
    monkeypatch.setattr(config, "INBOX_DIR", inbox_file)
    monkeypatch.setattr(config, "ARCHIVE_DIR", tmp_path / "archive")
    monkeypatch.setattr(config, "RAG_DIR", tmp_path / "rag")

    assert config.init_filesystem() is False
