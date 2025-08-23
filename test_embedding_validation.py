#!/usr/bin/env python3
"""
Test suite for embedding validation issues.
This test reproduces the "No valid document embeddings found" error
and validates fixes for the embedding pipeline.
"""

import asyncio
import json
import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import the modules we're testing
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.google_embedding_client import GoogleEmbeddingClient
from adalflow.core.types import Document, EmbedderOutput


class TestEmbeddingValidation:
    """Test suite for embedding validation and error handling."""
    
    @pytest.mark.asyncio
    async def test_empty_embeddings_not_added_to_results(self):
        """
        Test 1: Verify that empty embeddings are NOT added to results.
        This should FAIL with current implementation.
        """
        client = GoogleEmbeddingClient()
        
        # Mock the API response to simulate a failure
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.text = asyncio.coroutine(lambda: '{"error": "Invalid request"}')()
        
        documents = [
            Document(text="Test document 1", id="1"),
            Document(text="Test document 2", id="2"),
        ]
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            result = await client.acall(
                input=documents,
                model_kwargs={"model": "models/text-embedding-004"},
                model_type="embedder"
            )
            
            # This test should FAIL initially because current code adds empty embeddings
            assert isinstance(result, EmbedderOutput)
            embeddings = result.data
            
            # Check that NO empty embeddings exist
            for i, embedding in enumerate(embeddings):
                assert len(embedding) > 0, f"Document {i} has empty embedding!"
                assert len(embedding) == 768, f"Document {i} has invalid dimension: {len(embedding)}"
    
    @pytest.mark.asyncio
    async def test_dimension_consistency_validation(self):
        """
        Test 2: Verify all embeddings have consistent dimensions.
        This should FAIL when mixed dimensions are returned.
        """
        client = GoogleEmbeddingClient()
        
        # Simulate mixed response - some successful, some failed
        documents = [
            Document(text="Test document 1", id="1"),
            Document(text="Test document 2", id="2"),
            Document(text="Test document 3", id="3"),
        ]
        
        # Mock response with inconsistent embeddings
        mock_embeddings = [
            [0.1] * 768,  # Valid embedding
            [],           # Empty embedding (failure)
            [0.2] * 768,  # Valid embedding
        ]
        
        with patch.object(client, '_process_batch_request', return_value=mock_embeddings):
            result = await client.acall(
                input=documents,
                model_kwargs={"model": "models/text-embedding-004"},
                model_type="embedder"
            )
            
            embeddings = result.data
            
            # All embeddings should have the same dimension
            if embeddings:
                expected_dim = len(embeddings[0])
                for i, embedding in enumerate(embeddings):
                    assert len(embedding) == expected_dim, \
                        f"Dimension mismatch at index {i}: expected {expected_dim}, got {len(embedding)}"
    
    @pytest.mark.asyncio
    async def test_batch_failure_triggers_retry(self):
        """
        Test 3: Verify batch failures trigger retry logic.
        This should FAIL initially as retry is not implemented.
        """
        client = GoogleEmbeddingClient()
        
        documents = [Document(text=f"Test document {i}", id=str(i)) for i in range(10)]
        
        # Track call count
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # First call fails, second succeeds
            if call_count == 1:
                mock_resp = MagicMock()
                mock_resp.status = 503  # Service unavailable
                mock_resp.text = asyncio.coroutine(lambda: '{"error": "Service unavailable"}')()
                return mock_resp
            else:
                # Success response
                mock_resp = MagicMock()
                mock_resp.status = 200
                embeddings = [[0.1] * 768 for _ in range(10)]
                mock_resp.text = asyncio.coroutine(
                    lambda: json.dumps({"embeddings": embeddings})
                )()
                return mock_resp
        
        with patch('aiohttp.ClientSession.post', side_effect=mock_post):
            result = await client.acall(
                input=documents,
                model_kwargs={"model": "models/text-embedding-004"},
                model_type="embedder"
            )
            
            # Should have retried at least once
            assert call_count > 1, "Batch request was not retried on failure"
            
            # Should eventually get valid embeddings
            assert result.data
            assert all(len(emb) == 768 for emb in result.data)
    
    @pytest.mark.asyncio
    async def test_partial_batch_success_handling(self):
        """
        Test 4: Verify partial batch success is handled correctly.
        Some documents succeed, some fail - should handle gracefully.
        """
        client = GoogleEmbeddingClient()
        
        documents = [
            Document(text="Valid text 1", id="1"),
            Document(text="", id="2"),  # Empty text might fail
            Document(text="Valid text 3", id="3"),
        ]
        
        # Mock partial success response
        mock_response = MagicMock()
        mock_response.status = 200
        partial_response = {
            "embeddings": [
                {"values": [0.1] * 768},  # Success
                {"error": "Empty content"},  # Failure
                {"values": [0.3] * 768},  # Success
            ]
        }
        mock_response.text = asyncio.coroutine(lambda: json.dumps(partial_response))()
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            result = await client.acall(
                input=documents,
                model_kwargs={"model": "models/text-embedding-004"},
                model_type="embedder"
            )
            
            # Should handle partial success gracefully
            embeddings = result.data
            
            # Should only have valid embeddings
            valid_count = sum(1 for emb in embeddings if len(emb) == 768)
            assert valid_count >= 2, "Should have at least 2 valid embeddings"
            
            # No empty embeddings should be present
            assert all(len(emb) > 0 for emb in embeddings if emb)
    
    @pytest.mark.asyncio
    async def test_error_messages_are_informative(self):
        """
        Test 5: Verify error messages are informative and actionable.
        """
        client = GoogleEmbeddingClient()
        
        documents = [
            Document(text="Test document", id="1"),
        ]
        
        # Mock complete failure
        mock_response = MagicMock()
        mock_response.status = 400
        error_detail = {
            "error": {
                "code": 400,
                "message": "Invalid model name format: expected 'models/text-embedding-004'",
                "details": "The model name 'text-embedding-004' is not in the correct format"
            }
        }
        mock_response.text = asyncio.coroutine(lambda: json.dumps(error_detail))()
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            with patch('api.google_embedding_client.logger') as mock_logger:
                result = await client.acall(
                    input=documents,
                    model_kwargs={"model": "text-embedding-004"},  # Wrong format
                    model_type="embedder"
                )
                
                # Should log informative error
                mock_logger.error.assert_called()
                error_args = mock_logger.error.call_args[0][0]
                
                # Error should mention the specific issue
                assert "model" in error_args.lower() or "format" in error_args.lower(), \
                    "Error message should mention model format issue"


def test_embedding_dimension_validator():
    """
    Test the embedding dimension validator function.
    This should be added to data_pipeline.py
    """
    # Test data with mixed dimensions
    embeddings = [
        [0.1] * 768,  # Valid
        [],           # Empty - invalid
        [0.2] * 768,  # Valid
        [0.3] * 512,  # Wrong dimension
    ]
    
    # This function should be implemented in data_pipeline.py
    def validate_embedding_dimensions(embeddings: List[List[float]]) -> tuple[List[List[float]], List[int]]:
        """
        Validate embeddings have consistent dimensions.
        Returns (valid_embeddings, failed_indices)
        """
        if not embeddings:
            return [], []
        
        # Find the expected dimension from first valid embedding
        expected_dim = None
        for emb in embeddings:
            if emb and len(emb) > 0:
                expected_dim = len(emb)
                break
        
        if expected_dim is None:
            return [], list(range(len(embeddings)))
        
        valid_embeddings = []
        failed_indices = []
        
        for i, emb in enumerate(embeddings):
            if emb and len(emb) == expected_dim:
                valid_embeddings.append(emb)
            else:
                failed_indices.append(i)
        
        return valid_embeddings, failed_indices
    
    # Test the validator
    valid, failed = validate_embedding_dimensions(embeddings)
    
    assert len(valid) == 2, f"Expected 2 valid embeddings, got {len(valid)}"
    assert len(failed) == 2, f"Expected 2 failed indices, got {len(failed)}"
    assert failed == [1, 3], f"Expected failed indices [1, 3], got {failed}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])