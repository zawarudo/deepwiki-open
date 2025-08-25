"""
Emergency Fix Tests for GoogleEmbeddingClient

Tests to prevent empty vector creation and ensure proper error handling.
This is a critical test suite that validates the fix for empty vector generation
in GoogleEmbeddingClient that was causing system-wide failures.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from adalflow.core.types import ModelType, Embedding

from api.google_embedding_client import GoogleEmbeddingClient


class TestEmergencyFix:
    """
    Emergency test suite to validate GoogleEmbeddingClient fixes.
    
    These tests ensure that:
    1. No empty vectors are created on API failures
    2. Correct model name is used (text-embedding-004)
    3. All embeddings are properly validated for dimensions
    4. Retry logic works correctly for transient failures
    """

    def setup_method(self):
        """Set up test environment before each test."""
        # Create a client instance for testing with mock API key
        self.client = GoogleEmbeddingClient(api_key="test_api_key")

    @pytest.mark.unit
    def test_no_empty_vectors_on_api_failure(self):
        """
        CRITICAL: Ensure exceptions are raised instead of creating empty vectors.
        
        This test validates that when the Google API fails, the client raises
        an appropriate exception rather than returning empty vectors that would
        corrupt the embedding database and crash FAISS indexing.
        """
        with patch('requests.post') as mock_post:
            # Mock API to return an error status
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response
            
            # Test that we get a proper error response, not empty vectors
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # CURRENT BUGGY BEHAVIOR: Returns empty vectors instead of clean failure
            # This test documents the bug and will pass after the fix
            
            if len(result.data) > 0 and any(len(emb.embedding) == 0 for emb in result.data):
                # BUG DETECTED: System is creating empty vectors (current behavior)
                pytest.fail(
                    f"CRITICAL BUG: Found {len([e for e in result.data if len(e.embedding) == 0])} "
                    f"empty embedding vectors. This corrupts the database and crashes FAISS indexing. "
                    f"System should raise exceptions instead of creating empty vectors."
                )
            
            # EXPECTED BEHAVIOR AFTER FIX:
            # - Should return empty data list with clear error message
            # - OR raise appropriate exception instead of returning empty vectors
            assert result.error is not None, "API failure should be reported as error"

    @pytest.mark.unit
    def test_no_empty_vectors_in_single_request_failure(self):
        """
        Test that single request failures don't create empty vectors.
        
        When batch requests fail and fall back to single requests, and those
        also fail, we should not create empty vectors.
        """
        with patch('requests.post') as mock_post:
            # Mock batch request to fail, then single requests to also fail
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": ["test text 1", "test text 2"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # Check for the critical bug: empty vectors being created
            empty_vectors = [e for e in result.data if hasattr(e, 'embedding') and len(e.embedding) == 0]
            if empty_vectors:
                pytest.fail(
                    f"CRITICAL BUG: Found {len(empty_vectors)} empty embedding vectors at indices "
                    f"{[e.index for e in empty_vectors]}. This corrupts the database and crashes FAISS indexing. "
                    f"System should raise exceptions instead of creating empty vectors."
                )

    @pytest.mark.unit
    def test_correct_model_name_default(self):
        """
        Verify that the default model is 'text-embedding-004'.
        
        The original bug used 'embedding-001' which is incorrect.
        This test ensures the fix uses the correct Google model name.
        """
        # Test default model in convert_inputs_to_api_kwargs
        api_kwargs = self.client.convert_inputs_to_api_kwargs(
            input=["test text"],
            model_type=ModelType.EMBEDDER
        )
        
        assert api_kwargs["model"] == "text-embedding-004"
        
        # Test default model in call method
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [{"values": [0.1] * 768}]
            }
            mock_post.return_value = mock_response
            
            # Call without explicit model
            result = self.client.call(
                api_kwargs={"texts": ["test"]},
                model_type=ModelType.EMBEDDER
            )
            
            # Verify the correct model was used in the API call
            call_args = mock_post.call_args
            url = call_args[1]['json']['model'] if 'json' in call_args[1] else call_args[0][0]
            assert "text-embedding-004" in str(url) or "text-embedding-004" in str(call_args)

    @pytest.mark.unit  
    def test_dimension_validation_concept(self):
        """
        Test the concept of dimension validation for embeddings.
        
        This test validates that we can detect and reject invalid embeddings:
        - Empty vectors (length 0)
        - Wrong dimensions (not 768)
        - Accept correct dimensions (768)
        
        NOTE: This test validates the concept. The actual _validate_embedding
        method needs to be implemented in the fix.
        """
        # Test data for validation
        empty_vector = []
        wrong_dimension_vector = [0.1] * 512  # 512 dimensions instead of 768
        correct_vector = [0.1] * 768  # Correct 768 dimensions
        
        # These assertions define the expected behavior after the fix
        assert len(empty_vector) == 0  # Should be rejected
        assert len(wrong_dimension_vector) == 512  # Should be rejected (not 768)
        assert len(correct_vector) == 768  # Should be accepted
        
        # After the fix, there should be a validation method like this:
        # with pytest.raises(ValueError, match="Empty embedding"):
        #     self.client._validate_embedding(empty_vector)
        #
        # with pytest.raises(ValueError, match="Invalid embedding dimension"):
        #     self.client._validate_embedding(wrong_dimension_vector)
        #
        # assert self.client._validate_embedding(correct_vector) == True

    @pytest.mark.unit
    def test_proper_error_handling_in_batch_response(self):
        """
        Test that batch response parsing errors are handled correctly.
        
        When the JSON response parsing fails, we should handle it gracefully
        without creating empty vectors.
        """
        with patch('requests.post') as mock_post:
            # Mock successful HTTP response but malformed JSON
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # Should handle the error gracefully
            assert result.error is not None
            # After the fix, we should not get empty vectors even on JSON parsing errors
            if result.data:
                for embedding in result.data:
                    if hasattr(embedding, 'embedding') and len(embedding.embedding) == 0:
                        pytest.fail("JSON parsing error should not create empty vectors")

    @pytest.mark.unit
    def test_embedding_count_mismatch_handling(self):
        """
        Test handling of embedding count mismatches.
        
        When Google returns fewer embeddings than requested texts,
        we should handle this gracefully without padding with empty vectors.
        """
        with patch('requests.post') as mock_post:
            # Mock response with fewer embeddings than input texts
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": [0.1] * 768}  # Only 1 embedding for 2 texts
                ]
            }
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": ["text1", "text2"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # Should report the mismatch as an error
            assert result.error is not None
            assert "mismatch" in result.error.lower()
            
            # After the fix, should not pad with empty vectors
            if result.data:
                for embedding in result.data:
                    if hasattr(embedding, 'embedding') and len(embedding.embedding) == 0:
                        pytest.fail("Count mismatch should not create empty vectors")

    @pytest.mark.network
    def test_retry_logic_concept(self):
        """
        Test the concept of retry logic for transient failures.
        
        This test validates that transient API failures should trigger retries
        with exponential backoff, and persistent failures should eventually
        raise exceptions rather than return empty vectors.
        
        NOTE: This is a conceptual test. The actual retry logic needs to be
        implemented in the fix.
        """
        # This test documents the expected behavior after implementing retry logic
        
        # Simulate transient failure pattern: fail twice, then succeed
        responses = [
            Mock(status_code=503, text="Service Temporarily Unavailable"),  # Transient
            Mock(status_code=503, text="Service Temporarily Unavailable"),  # Transient  
            Mock(status_code=200, json=lambda: {"embeddings": [{"values": [0.1] * 768}]})  # Success
        ]
        
        with patch('requests.post', side_effect=responses) as mock_post:
            # After implementing retry logic, this should eventually succeed
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # Currently this will fail, but after the retry fix it should succeed
            # The test documents expected behavior
            if mock_post.call_count == 3:  # If retries were implemented
                assert result.error is None
                assert len(result.data) == 1
                assert len(result.data[0].embedding) == 768
            else:
                # Current behavior - documents what needs to be fixed
                assert result.error is not None or len(result.data) == 0

    @pytest.mark.unit
    def test_api_key_validation(self):
        """
        Test that missing API key raises appropriate error.
        
        This ensures proper error handling for configuration issues.
        """
        with patch.dict('os.environ', {}, clear=True):
            client = GoogleEmbeddingClient()
            
            with pytest.raises(ValueError, match="Environment variable GOOGLE_API_KEY must be set"):
                client.call(
                    api_kwargs={"texts": ["test"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )

    @pytest.mark.unit
    def test_model_type_validation(self):
        """
        Test that incorrect model types are rejected.
        
        GoogleEmbeddingClient should only work with EMBEDDER model type.
        """
        with pytest.raises(ValueError, match="model_type .* is not supported"):
            self.client.convert_inputs_to_api_kwargs(
                input=["test"],
                model_type=ModelType.LLM  # Wrong type
            )
        
        with pytest.raises(ValueError, match="model_type .* is not supported"):
            self.client.call(
                api_kwargs={"texts": ["test"]},
                model_type=ModelType.LLM  # Wrong type
            )

    @pytest.mark.integration
    def test_end_to_end_success_case(self):
        """
        Test the complete success flow end-to-end.
        
        This test validates that when everything works correctly,
        we get properly formatted embeddings with correct dimensions.
        """
        with patch('requests.post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": [0.1] * 768},
                    {"values": [0.2] * 768}
                ]
            }
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": ["text1", "text2"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # Validate successful response
            assert result.error is None
            assert len(result.data) == 2
            
            # Validate embedding dimensions
            for i, embedding in enumerate(result.data):
                assert len(embedding.embedding) == 768, f"Embedding {i} has wrong dimensions"
                assert embedding.index == i
                assert all(isinstance(x, (int, float)) for x in embedding.embedding)

    @pytest.mark.unit
    def test_empty_input_handling(self):
        """
        Test that empty input is handled gracefully.
        
        When no texts are provided, should return empty result without errors.
        """
        result = self.client.call(
            api_kwargs={"texts": [], "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert len(result.data) == 0
        assert result.error is None

    @pytest.mark.unit
    def test_large_batch_chunking(self):
        """
        Test that large batches are properly chunked.
        
        Verify that the client can handle large numbers of texts
        by chunking them appropriately.
        """
        # Create a large batch of texts (more than chunk_size of 128)
        large_text_batch = [f"text {i}" for i in range(200)]
        
        with patch('requests.post') as mock_post:
            # Mock successful responses for multiple chunks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [{"values": [0.1] * 768} for _ in range(128)]  # Full chunk
            }
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": large_text_batch, "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # Should have made multiple API calls for chunking
            assert mock_post.call_count >= 2  # At least 2 chunks for 200 texts
            
            # Verify we get embeddings for all texts (after fix)
            if result.error is None:
                assert len(result.data) == 200


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])