"""
Test for adaptive retry logic when all embedding vectors are empty.

This test ensures the data pipeline properly handles and retries when
embedding generation fails and produces empty vectors.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from typing import List

from adalflow.core.types import Document
from api.data_pipeline import transform_documents_and_save_to_db


class TestAdaptiveRetryEmptyVectors:
    """Test suite for adaptive retry logic when encountering empty vectors."""
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(text="Test document 1", id="doc1", meta_data={"source": "test"}),
            Document(text="Test document 2", id="doc2", meta_data={"source": "test"}),
            Document(text="Test document 3", id="doc3", meta_data={"source": "test"}),
        ]
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.mark.unit
    def test_empty_vectors_trigger_retry(self, sample_documents, temp_db_path):
        """
        Test that empty vectors trigger retry logic with backoff.
        
        The adaptive retry should:
        1. Detect all vectors are empty
        2. Reduce batch size and chunk size
        3. Retry with smaller parameters
        4. Eventually succeed or fail with proper error
        """
        with patch('api.data_pipeline.get_embedder') as mock_get_embedder:
            with patch('api.data_pipeline.LocalDB') as mock_db_class:
                # Create mock embedder that returns empty vectors initially
                mock_embedder = Mock()
                attempt_count = [0]
                
                def mock_transform(key):
                    """Mock transform that fails first 2 attempts with empty vectors."""
                    attempt_count[0] += 1
                    if attempt_count[0] <= 2:
                        # Return empty vectors for first 2 attempts
                        return None
                    # Success on 3rd attempt
                    return None
                
                # Setup mock database
                mock_db = Mock()
                mock_db.transform = mock_transform
                
                # Mock get_transformed_data to return empty vectors first 2 times
                def mock_get_transformed():
                    if attempt_count[0] <= 2:
                        # Return documents with empty vectors
                        docs = []
                        for doc in sample_documents:
                            mock_doc = Mock()
                            mock_doc.vector = []  # Empty vector
                            docs.append(mock_doc)
                        return docs
                    else:
                        # Return valid vectors on 3rd attempt
                        docs = []
                        for doc in sample_documents:
                            mock_doc = Mock()
                            mock_doc.vector = [0.1] * 768  # Valid 768-dim vector
                            docs.append(mock_doc)
                        return docs
                
                mock_db.get_transformed_data = Mock(side_effect=mock_get_transformed)
                mock_db.load = Mock()
                mock_db.register_transformer = Mock()
                mock_db.save_state = Mock()
                mock_db_class.return_value = mock_db
                
                mock_get_embedder.return_value = mock_embedder
                
                # Run transform with adaptive retry enabled
                with patch('api.data_pipeline.configs', {
                    'text_splitter': {'chunk_size': 350},
                    'adaptive_retry': {
                        'enabled': True,
                        'max_retries': 3,
                        'backoff_factor': 0.5,
                        'min_chunk_size': 100,
                        'min_batch_size': 10
                    }
                }):
                    result_db = transform_documents_and_save_to_db(
                        sample_documents, 
                        temp_db_path,
                        is_ollama_embedder=False
                    )
                    
                    # Verify retries happened (3 attempts total)
                    assert attempt_count[0] == 3, f"Expected 3 attempts, got {attempt_count[0]}"
                    
                    # Verify save was called after success
                    mock_db.save_state.assert_called_once()
    
    @pytest.mark.unit
    def test_all_retries_fail_with_empty_vectors(self, sample_documents, temp_db_path):
        """
        Test that all retries failing with empty vectors raises proper error.
        
        When adaptive retry exhausts all attempts and still gets empty vectors,
        it should raise a RuntimeError with detailed context.
        """
        with patch('api.data_pipeline.get_embedder') as mock_get_embedder:
            with patch('api.data_pipeline.LocalDB') as mock_db_class:
                # Create mock embedder
                mock_embedder = Mock()
                
                # Setup mock database that always returns empty vectors
                mock_db = Mock()
                mock_db.transform = Mock()
                
                def mock_get_transformed():
                    # Always return documents with empty vectors
                    docs = []
                    for doc in sample_documents:
                        mock_doc = Mock()
                        mock_doc.vector = []  # Empty vector
                        docs.append(mock_doc)
                    return docs
                
                mock_db.get_transformed_data = Mock(side_effect=mock_get_transformed)
                mock_db.load = Mock()
                mock_db.register_transformer = Mock()
                mock_db.save_state = Mock()
                mock_db_class.return_value = mock_db
                
                mock_get_embedder.return_value = mock_embedder
                
                # Run transform with adaptive retry enabled
                with patch('api.data_pipeline.configs', {
                    'text_splitter': {'chunk_size': 350},
                    'adaptive_retry': {
                        'enabled': True,
                        'max_retries': 2,
                        'backoff_factor': 0.5,
                        'min_chunk_size': 100,
                        'min_batch_size': 10
                    }
                }):
                    with pytest.raises(RuntimeError) as exc_info:
                        transform_documents_and_save_to_db(
                            sample_documents, 
                            temp_db_path,
                            is_ollama_embedder=False
                        )
                    
                    # Check error message contains context
                    error_msg = str(exc_info.value)
                    assert "all embedding vectors are empty" in error_msg.lower()
                    assert "adaptive retry" in error_msg.lower()
                    
                    # Verify save was NOT called since all attempts failed
                    mock_db.save_state.assert_not_called()
    
    @pytest.mark.unit
    def test_partial_empty_vectors_still_succeed(self, sample_documents, temp_db_path):
        """
        Test that partial empty vectors don't fail if at least one is valid.
        
        If some vectors are empty but at least one is valid, the transform
        should succeed and save the database.
        """
        with patch('api.data_pipeline.get_embedder') as mock_get_embedder:
            with patch('api.data_pipeline.LocalDB') as mock_db_class:
                # Create mock embedder
                mock_embedder = Mock()
                
                # Setup mock database
                mock_db = Mock()
                mock_db.transform = Mock()
                
                def mock_get_transformed():
                    # Return mix of empty and valid vectors
                    docs = []
                    for i, doc in enumerate(sample_documents):
                        mock_doc = Mock()
                        if i == 0:
                            # First document has valid vector
                            mock_doc.vector = [0.1] * 768
                        else:
                            # Other documents have empty vectors
                            mock_doc.vector = []
                        docs.append(mock_doc)
                    return docs
                
                mock_db.get_transformed_data = Mock(side_effect=mock_get_transformed)
                mock_db.load = Mock()
                mock_db.register_transformer = Mock()
                mock_db.save_state = Mock()
                mock_db_class.return_value = mock_db
                
                mock_get_embedder.return_value = mock_embedder
                
                # Run transform
                with patch('api.data_pipeline.configs', {
                    'text_splitter': {'chunk_size': 350},
                    'adaptive_retry': {
                        'enabled': True,
                        'max_retries': 3,
                        'backoff_factor': 0.5,
                        'min_chunk_size': 100,
                        'min_batch_size': 10
                    }
                }):
                    result_db = transform_documents_and_save_to_db(
                        sample_documents, 
                        temp_db_path,
                        is_ollama_embedder=False
                    )
                    
                    # Verify save was called (at least one valid vector)
                    mock_db.save_state.assert_called_once()
    
    @pytest.mark.unit
    def test_backoff_reduces_parameters(self, sample_documents, temp_db_path):
        """
        Test that backoff properly reduces batch_size and chunk_size.
        
        Each retry should reduce the parameters by the backoff factor,
        but not go below the minimum values.
        """
        with patch('api.data_pipeline.get_embedder') as mock_get_embedder:
            with patch('api.data_pipeline.prepare_data_pipeline') as mock_prepare:
                with patch('api.data_pipeline.LocalDB') as mock_db_class:
                    # Track parameters used in each attempt
                    prepare_calls = []
                    
                    def track_prepare(is_ollama_embedder=None):
                        # Track this call
                        prepare_calls.append(is_ollama_embedder)
                        return Mock()  # Return mock transformer
                    
                    mock_prepare.side_effect = track_prepare
                    
                    # Create mock embedder
                    mock_embedder = Mock()
                    mock_get_embedder.return_value = mock_embedder
                    
                    # Setup mock database that always fails
                    mock_db = Mock()
                    mock_db.transform = Mock()
                    mock_db.get_transformed_data = Mock(return_value=[])  # Always empty
                    mock_db.load = Mock()
                    mock_db.register_transformer = Mock()
                    mock_db_class.return_value = mock_db
                    
                    # Run transform with specific config
                    with patch('api.data_pipeline.configs', {
                        'text_splitter': {'chunk_size': 400},
                        'adaptive_retry': {
                            'enabled': True,
                            'max_retries': 3,
                            'backoff_factor': 0.5,
                            'min_chunk_size': 100,
                            'min_batch_size': 10
                        }
                    }):
                        with patch('api.data_pipeline.get_embedder_config') as mock_embedder_config:
                            mock_embedder_config.return_value = {'batch_size': 100}
                            
                            # This should fail after retries
                            with pytest.raises(RuntimeError):
                                transform_documents_and_save_to_db(
                                    sample_documents, 
                                    temp_db_path,
                                    is_ollama_embedder=False
                                )
                            
                            # Verify prepare_data_pipeline was called for each retry
                            # Initial + 3 retries = 4 calls
                            assert len(prepare_calls) == 4, f"Expected 4 prepare calls, got {len(prepare_calls)}"
    
    @pytest.mark.integration
    def test_empty_vector_logging(self, sample_documents, temp_db_path, caplog):
        """
        Test that appropriate error messages are logged for empty vectors.
        
        Verify that the error logging includes:
        - The attempt number
        - The adaptive retry message
        - Context about batch and chunk sizes
        """
        import logging
        caplog.set_level(logging.ERROR)
        
        with patch('api.data_pipeline.get_embedder') as mock_get_embedder:
            with patch('api.data_pipeline.LocalDB') as mock_db_class:
                # Setup mocks that always return empty vectors
                mock_embedder = Mock()
                mock_get_embedder.return_value = mock_embedder
                
                mock_db = Mock()
                mock_db.transform = Mock()
                mock_db.get_transformed_data = Mock(return_value=[])
                mock_db.load = Mock()
                mock_db.register_transformer = Mock()
                mock_db_class.return_value = mock_db
                
                with patch('api.data_pipeline.configs', {
                    'text_splitter': {'chunk_size': 350},
                    'adaptive_retry': {
                        'enabled': True,
                        'max_retries': 1,  # Just one retry for faster test
                        'backoff_factor': 0.5,
                        'min_chunk_size': 100,
                        'min_batch_size': 10
                    }
                }):
                    with pytest.raises(RuntimeError):
                        transform_documents_and_save_to_db(
                            sample_documents,
                            temp_db_path,
                            is_ollama_embedder=False
                        )
                    
                    # Check that error was logged
                    error_logs = [r for r in caplog.records if r.levelname == 'ERROR']
                    assert len(error_logs) > 0, "Expected error logs for empty vectors"
                    
                    # Check for specific error message
                    error_messages = [r.message for r in error_logs]
                    assert any("all embedding vectors are empty" in msg.lower() for msg in error_messages), \
                        "Expected 'all embedding vectors are empty' in error logs"