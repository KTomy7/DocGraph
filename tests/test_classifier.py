"""Tests for Pydantic schema validation and Ollama classification."""

import pytest
from src.classifier import DocumentMetadata, classify_document, sanitize_filename

def test_sanitize_filename():
    assert sanitize_filename("2024-05/Contract*Name?.pdf") == "2024-05_Contract_Name_.pdf"

def test_metadata_category_validation(mocker):
    # Mock the active categories so "Housing" is recognized as valid during the test
    mocker.patch("src.classifier.get_active_categories", return_value=["Housing", "Contracts"])
    
    meta = DocumentMetadata(
        category="housing", 
        document_type="Lease",
        issuer="Landlord",
        document_date="2024-01-01",
        canonical_filename="test.pdf",
    )
    assert meta.category == "Housing"

    # Test the fallback mechanism directly
    meta_misc = DocumentMetadata(
        category="UnknownRandomCategory", 
        document_type="Lease",
        issuer="Landlord",
        document_date="2024-01-01",
        canonical_filename="test.pdf",
    )
    assert meta_misc.category == "Miscellaneous"

def test_classify_document_mocked(mocker):
    # 1. Force the system to accept "Housing" as a valid category
    mocker.patch("src.classifier.get_active_categories", return_value=["Housing"])
    
    # 2. Mock the exact Ollama Client instance your code creates
    mock_client_instance = mocker.MagicMock()
    mocker.patch("src.classifier.ollama.Client", return_value=mock_client_instance)
    
    # 3. Provide the expected payload
    json_payload = '{"category": "Housing", "document_type": "Agreement", "issuer": "TechCorp", "document_date": "2024-05-01", "canonical_filename": "2024-05-01_Housing_TechCorp_Agreement.pdf"}'
    mock_client_instance.chat.return_value = {
        "message": {"content": json_payload}
    }

    meta = classify_document("Fake contract text", "contract.pdf")
    
    assert meta.category == "Housing"
    assert meta.issuer == "TechCorp"
    assert meta.canonical_filename == "2024-05-01_Housing_TechCorp_Agreement.pdf"

def test_classify_document_exceptions(mocker):
    """Test that the classifier correctly raises ValueErrors on bad LLM responses."""
    mock_client_instance = mocker.MagicMock()
    mocker.patch("src.classifier.ollama.Client", return_value=mock_client_instance)
    mocker.patch("src.classifier.get_active_categories", return_value=["Housing"])
    
    # Test missing message content
    mock_client_instance.chat.return_value = {}
    with pytest.raises(ValueError, match="did not contain message content"):
        classify_document("text", "doc.pdf")
        
    # Test invalid JSON format
    mock_client_instance.chat.return_value = {"message": {"content": "{bad_json..."}}
    with pytest.raises(ValueError, match="invalid JSON"):
        classify_document("text", "doc.pdf")
        