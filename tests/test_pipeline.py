"""Unit tests for the core document processing pipeline."""

from pathlib import Path
import pytest
from src.pipeline import process_document
from src.classifier import DocumentMetadata


class TestPipeline:
    """Test suite for the pipeline orchestration logic."""

    def test_process_document_success(self, tmp_path, mocker):
        """Verify the pipeline orchestrates all modules in the correct sequence."""
        # 1. Setup a dummy physical file so `file_path.exists()` passes
        source_file = tmp_path / "raw_contract.pdf"
        source_file.touch()

        # 2. Setup mock return values for all dependencies
        mock_text = "Mocked extracted text"
        mock_method = "digital"
        
        mock_metadata = DocumentMetadata(
            category="Legal",
            document_type="Contract",
            issuer="TechCorp",
            document_date="2024-01-15",
            canonical_filename="2024-01-15_Legal_TechCorp_Contract.pdf"
        )
        
        dest_path = tmp_path / "archive" / mock_metadata.canonical_filename

        # 3. Apply the monkeypatches
        mock_extract = mocker.patch("src.pipeline.extract_text", return_value=(mock_text, mock_method))
        mock_classify = mocker.patch("src.pipeline.classify_document", return_value=mock_metadata)
        mock_relocate = mocker.patch("src.pipeline.relocate_file", return_value=dest_path)
        mock_index = mocker.patch("src.pipeline.index_document")

        # 4. Execute the pipeline
        result_path, result_meta, result_method = process_document(source_file)

        # 5. Verify the return values match what the pipeline assembled
        assert result_path == dest_path
        assert result_meta == mock_metadata
        assert result_method == mock_method

        # 6. Verify every underlying function was called with the exact right arguments
        mock_extract.assert_called_once_with(source_file)
        mock_classify.assert_called_once_with(mock_text, "raw_contract.pdf")
        mock_relocate.assert_called_once_with(
            source_path=source_file,
            metadata=mock_metadata,
            extraction_method=mock_method
        )
        mock_index.assert_called_once_with(mock_text, mock_metadata.canonical_filename)

    def test_process_document_file_not_found(self):
        """Verify pipeline safely aborts if the input file does not exist."""
        fake_path = Path("/does/not/exist.pdf")
        
        with pytest.raises(FileNotFoundError, match="Document not found"):
            process_document(fake_path)
            