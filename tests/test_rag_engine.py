"""Unit tests for the Knowledge Graph Engine."""

from unittest.mock import AsyncMock
from src.rag_engine import index_document, query_graph

def test_index_document_mocked(mocker):
    """Verify document insertion correctly targets LightRAG."""
    mock_rag_instance = mocker.MagicMock()
    
    # Assign AsyncMocks to the native async methods
    mock_rag_instance.initialize_storages = AsyncMock()
    mock_rag_instance.ainsert = AsyncMock()
    
    mocker.patch("src.rag_engine.get_rag_instance", return_value=mock_rag_instance)
    
    index_document("Test contract payload", "2024-01-01_Contracts_Test_Agreement.pdf")
    
    expected_payload = "Source Document: 2024-01-01_Contracts_Test_Agreement.pdf\n\nTest contract payload"
    
    # Verify the storage was initialized and the payload was inserted
    mock_rag_instance.initialize_storages.assert_called_once()
    mock_rag_instance.ainsert.assert_called_once_with(expected_payload)


def test_index_document_empty():
    """Verify empty text aborts early without calling LightRAG."""
    # Will fail if LightRAG attempts initialization, proving the early exit works
    index_document("   \n  ", "empty.pdf")


def test_query_graph_mocked(mocker):
    """Verify hybrid queries are routed correctly to the engine."""
    mock_rag_instance = mocker.MagicMock()
    
    mock_rag_instance.initialize_storages = AsyncMock()
    mock_rag_instance.aquery = AsyncMock(return_value="Mocked Graph Answer")
    
    mocker.patch("src.rag_engine.get_rag_instance", return_value=mock_rag_instance)

    answer = query_graph("What was the deposit amount?", mode="hybrid")
    
    assert answer == "Mocked Graph Answer"
    mock_rag_instance.initialize_storages.assert_called_once()
    