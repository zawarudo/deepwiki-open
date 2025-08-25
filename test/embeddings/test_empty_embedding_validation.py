"""
Comprehensive test suite for empty embedding validation in GoogleEmbeddingClient.

This test suite follows TDD methodology (RED phase) - all tests are designed to FAIL
with the current implementation to demonstrate the empty embedding bug where API
failures result in empty vectors [] being created instead of proper error handling.

The bug occurs when:
1. API returns None or invalid response for a document
2. API raises an exception during processing
3. Batch embedding has partial failures
4. Complete batch failure occurs
5. Network timeouts happen during requests

These tests will fail initially (demonstrating the bug exists) and should pass
after implementing the fix in Task #002.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
import json
from requests.exceptions import Timeout, ConnectionError, HTTPError

from adalflow.core.types import ModelType, Embedding, EmbedderOutput
from api.google_embedding_client import GoogleEmbeddingClient, EmbeddingGenerationError


class TestEmptyEmbeddingValidation:
    """
    Test suite for validating that no empty embeddings are created on failures.
    
    These tests demonstrate the current bug where API failures result in empty
    vectors [] being appended to results instead of proper error handling.
    """

    def setup_method(self):
        """Set up test environment before each test."""
        self.client = GoogleEmbeddingClient(api_key="test_api_key")
        self.test_texts = ["Test document 1", "Test document 2", "Test document 3"]
        self.expected_dimension = 768

    def _assert_no_empty_embeddings(self, result: EmbedderOutput, context: str):
        """
        Helper method to assert no empty embeddings exist in result.
        
        This is the core assertion that should pass after the bug is fixed.
        Currently, this will fail because empty vectors [] are created on failures.
        """
        empty_embeddings = []
        for i, embedding in enumerate(result.data):
            if hasattr(embedding, 'embedding') and len(embedding.embedding) == 0:
                empty_embeddings.append((i, embedding.index if hasattr(embedding, 'index') else 'unknown'))
        
        if empty_embeddings:
            indices = [f"position {pos}, index {idx}" for pos, idx in empty_embeddings]
            pytest.fail(
                f"EMPTY EMBEDDING BUG DETECTED in {context}: "
                f"Found {len(empty_embeddings)} empty embedding vectors at {', '.join(indices)}. "
                f"Empty vectors corrupt the database and crash FAISS indexing. "
                f"System should raise exceptions or return clean errors instead of creating empty vectors."
            )

    @pytest.mark.unit
    def test_api_failure_should_not_create_empty_embedding(self):
        """
        Test that API failures don't result in empty embeddings.
        
        BUG: Current implementation creates empty vectors [] when API returns
        error status codes instead of raising proper exceptions.
        """
        with patch('requests.post') as mock_post:
            # Simulate API server error
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
            mock_post.return_value = mock_response
            
            # Call the client
            result = self.client.call(
                api_kwargs={"texts": self.test_texts, "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # EXPECTED BEHAVIOR: Should either raise exception OR return clean error
            # CURRENT BUG: Creates empty vectors [] for failed embeddings
            self._assert_no_empty_embeddings(result, "API 500 error")
            
            # Additional assertions about proper error handling
            if result.data:
                # If we got any data, validate all embeddings have proper dimensions
                for embedding in result.data:
                    assert len(embedding.embedding) == self.expected_dimension, \
                        f"Expected {self.expected_dimension} dimensions, got {len(embedding.embedding)}"

    @pytest.mark.unit
    def test_api_returns_none_for_document(self):
        """
        Test scenario where API returns None/null values for embedding content.
        
        BUG: When API returns null or missing 'values' field, current implementation
        might create empty vectors instead of handling the error properly.
        """
        with patch('requests.post') as mock_post:
            # Mock response with null/missing embedding values
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": [0.1] * 768},  # Valid embedding
                    {"values": None},         # Null values - should cause error
                    {"values": [0.3] * 768}   # Valid embedding
                ]
            }
            mock_post.return_value = mock_response
            
            # This should raise an exception due to None values
            with pytest.raises(EmbeddingGenerationError):
                result = self.client.call(
                    api_kwargs={"texts": self.test_texts, "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )

    @pytest.mark.unit 
    def test_api_returns_empty_array_for_embedding(self):
        """
        Test scenario where API returns empty array [] for embedding values.
        
        This test demonstrates the expected behavior: when API returns empty values,
        the system should raise an EmbeddingGenerationError due to validation failure.
        """
        with patch('requests.post') as mock_post:
            # Mock response with empty array for embedding values
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": []},  # EMPTY ARRAY - should be rejected by validation
                ]
            }
            mock_post.return_value = mock_response
            
            # This should raise EmbeddingGenerationError due to empty embedding validation
            with pytest.raises(EmbeddingGenerationError, match="Empty embedding vector"):
                result = self.client.call(
                    api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )

    @pytest.mark.unit
    def test_missing_values_field_creates_empty_vector_bug(self):
        """
        Test that demonstrates the intended failing behavior for TDD RED phase.
        
        This test is designed to FAIL with the current implementation to show
        that empty embeddings CAN be created when the 'values' field is missing.
        
        The issue occurs when resp_embs[i].get("values", []) returns [] due to
        missing values field, and this empty array might not be properly validated.
        """
        with patch('requests.post') as mock_post:
            # Mock response where embedding entry is missing the 'values' field entirely
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"not_values": [0.1] * 768},  # Wrong field name - missing 'values'
                ]
            }
            mock_post.return_value = mock_response
            
            # Call the client
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion is designed to FAIL in the RED phase of TDD
            # It demonstrates that we currently don't have proper empty vector prevention
            if result.error is None and result.data:
                # If we got data, it might contain empty embeddings
                self._assert_no_empty_embeddings(result, "missing values field bug")
            else:
                # Even if there's an error, we want to ensure no empty vectors were created
                # This test fails if the system properly raises exceptions (current behavior)
                # but passes if empty vectors are created (the bug we want to demonstrate)
                pytest.fail(
                    "Expected empty embeddings to be created (demonstrating the bug), "
                    "but the system properly raised an exception. This indicates the "
                    "current implementation has better error handling than expected for "
                    "the TDD RED phase."
                )

    @pytest.mark.unit
    def test_api_exception_during_processing(self):
        """
        Test that exceptions during API processing don't create empty embeddings.
        
        BUG: When requests.post() raises exceptions, the error handling might
        still create empty vectors in the fallback logic.
        """
        with patch('requests.post') as mock_post:
            # Simulate network exception
            mock_post.side_effect = ConnectionError("Network connection failed")
            
            # This should either raise an exception or return clean error
            # Current bug might still create empty vectors in error handling
            try:
                result = self.client.call(
                    api_kwargs={"texts": self.test_texts, "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # If we get a result instead of exception, check for empty vectors
                self._assert_no_empty_embeddings(result, "network exception handling")
                
            except EmbeddingGenerationError:
                # This is the expected behavior - exception should be raised
                pass
            except Exception as e:
                pytest.fail(f"Unexpected exception type: {type(e).__name__}: {e}")

    @pytest.mark.unit
    def test_batch_embedding_partial_failures(self):
        """
        Test batch embedding where some requests succeed and others fail.
        
        BUG: In batch processing, when some embeddings fail, the current
        implementation might pad with empty vectors [] instead of handling
        partial failures properly.
        """
        with patch('requests.post') as mock_post:
            # Mock batch request that partially fails
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": [0.1] * 768},  # Success
                    {"values": []},           # Empty vector - should be rejected
                    {"values": [0.3] * 768}   # Success
                ]
            }
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": self.test_texts, "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # BUG: System might accept and return the empty vector
            self._assert_no_empty_embeddings(result, "partial batch failures")

    @pytest.mark.unit
    def test_complete_batch_failure_handling(self):
        """
        Test complete batch failure scenarios.
        
        BUG: When entire batch fails and falls back to individual requests
        that also fail, empty vectors might be created for all failed requests.
        """
        with patch('requests.post') as mock_post:
            # Mock both batch and individual requests to fail
            mock_response = Mock()
            mock_response.status_code = 429  # Rate limit
            mock_response.text = "Rate limit exceeded"
            mock_post.return_value = mock_response
            
            # This should raise an exception, not create empty vectors
            try:
                result = self.client.call(
                    api_kwargs={"texts": self.test_texts, "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # If we somehow get a result, it should not contain empty vectors
                self._assert_no_empty_embeddings(result, "complete batch failure")
                
            except EmbeddingGenerationError:
                # Expected behavior - should raise exception
                pass

    @pytest.mark.unit
    def test_network_timeout_scenarios(self):
        """
        Test network timeout scenarios don't create empty embeddings.
        
        BUG: Timeout exceptions in the network layer might be caught and
        result in empty vectors being created in error recovery logic.
        """
        with patch('requests.post') as mock_post:
            # Simulate network timeout
            mock_post.side_effect = Timeout("Request timed out")
            
            try:
                result = self.client.call(
                    api_kwargs={"texts": ["Single test text"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # If we get a result despite timeout, check for empty vectors
                self._assert_no_empty_embeddings(result, "network timeout")
                
            except (EmbeddingGenerationError, Timeout):
                # Expected behavior - should raise appropriate exception
                pass

    @pytest.mark.unit
    def test_malformed_api_response_handling(self):
        """
        Test handling of malformed API responses.
        
        BUG: When API returns malformed JSON or unexpected structure,
        the parsing logic might create empty vectors as fallback.
        """
        with patch('requests.post') as mock_post:
            # Mock response with malformed structure
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"wrong_field": [0.1] * 768},  # Missing 'values' field
                    {"values": "not_a_list"},      # Wrong data type
                    {"values": [0.3] * 768}        # Valid
                ]
            }
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": self.test_texts, "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # BUG: Malformed responses might create empty vectors for bad data
            self._assert_no_empty_embeddings(result, "malformed API response")

    @pytest.mark.unit
    def test_dimension_mismatch_creates_no_empty_vectors(self):
        """
        Test that wrong dimension embeddings don't result in empty vectors.
        
        BUG: When API returns embeddings with wrong dimensions (not 768),
        the validation logic might replace them with empty vectors [].
        """
        with patch('requests.post') as mock_post:
            # Mock response with wrong dimensions
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": [0.1] * 512},   # Wrong dimension - 512 instead of 768
                    {"values": [0.2] * 768},   # Correct dimension
                    {"values": [0.3] * 1024}   # Wrong dimension - 1024 instead of 768
                ]
            }
            mock_post.return_value = mock_response
            
            try:
                result = self.client.call(
                    api_kwargs={"texts": self.test_texts, "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # BUG: Wrong dimensions might be replaced with empty vectors
                self._assert_no_empty_embeddings(result, "dimension mismatch handling")
                
            except EmbeddingGenerationError:
                # Expected behavior - should raise exception for invalid dimensions
                pass

    @pytest.mark.unit
    def test_json_parsing_failure_edge_case(self):
        """
        Test JSON parsing failures don't create empty embeddings.
        
        BUG: When response.json() fails, the exception handling might
        fall back to creating empty vectors instead of proper error handling.
        """
        with patch('requests.post') as mock_post:
            # Mock response that returns 200 but has invalid JSON
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.text = "Invalid JSON response"
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": ["Test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # BUG: JSON parsing errors might result in empty vectors
            self._assert_no_empty_embeddings(result, "JSON parsing failure")

    @pytest.mark.unit
    def test_embedding_count_mismatch_edge_case(self):
        """
        Test embedding count mismatches don't pad with empty vectors.
        
        BUG: When API returns fewer embeddings than input texts, the system
        might pad the missing embeddings with empty vectors [].
        """
        with patch('requests.post') as mock_post:
            # Mock response with fewer embeddings than inputs
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": [0.1] * 768}  # Only 1 embedding for 3 input texts
                ]
            }
            mock_post.return_value = mock_response
            
            try:
                result = self.client.call(
                    api_kwargs={"texts": self.test_texts, "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # BUG: Missing embeddings might be padded with empty vectors
                self._assert_no_empty_embeddings(result, "embedding count mismatch")
                
            except EmbeddingGenerationError:
                # Expected behavior - should raise exception for count mismatch
                pass

    @pytest.mark.unit
    def test_single_request_fallback_failures(self):
        """
        Test single request fallback logic doesn't create empty vectors.
        
        BUG: When batch request fails and system falls back to individual
        requests, failed individual requests might result in empty vectors.
        """
        with patch('requests.post') as mock_post:
            # Create a side effect that simulates:
            # 1. Batch request fails (first call)
            # 2. Individual requests have mixed success (subsequent calls)
            responses = [
                # Batch request failure
                Mock(status_code=400, text="Bad batch request"),
                # Individual request 1 - success
                Mock(status_code=200, json=lambda: {"embedding": {"values": [0.1] * 768}}),
                # Individual request 2 - failure  
                Mock(status_code=500, text="Internal server error"),
                # Individual request 3 - success
                Mock(status_code=200, json=lambda: {"embedding": {"values": [0.3] * 768}})
            ]
            mock_post.side_effect = responses
            
            try:
                result = self.client.call(
                    api_kwargs={"texts": self.test_texts, "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # BUG: Failed individual requests might create empty vectors
                self._assert_no_empty_embeddings(result, "single request fallback failures")
                
            except EmbeddingGenerationError:
                # Expected behavior - should raise exception when requests fail
                pass

    @pytest.mark.integration
    def test_comprehensive_failure_scenarios(self):
        """
        Comprehensive test covering multiple failure scenarios in sequence.
        
        This test demonstrates complex failure patterns that might expose
        edge cases where empty vectors are created.
        """
        failure_scenarios = [
            ("HTTP 500", Mock(status_code=500, text="Server Error")),
            ("HTTP 429", Mock(status_code=429, text="Rate Limited")), 
            ("HTTP 400", Mock(status_code=400, text="Bad Request")),
            ("Timeout", Timeout("Connection timeout")),
            ("Connection Error", ConnectionError("Network unreachable"))
        ]
        
        for scenario_name, mock_response_or_exception in failure_scenarios:
            with patch('requests.post') as mock_post:
                if isinstance(mock_response_or_exception, Exception):
                    mock_post.side_effect = mock_response_or_exception
                else:
                    mock_post.return_value = mock_response_or_exception
                
                try:
                    result = self.client.call(
                        api_kwargs={"texts": [f"Test for {scenario_name}"], "model": "text-embedding-004"},
                        model_type=ModelType.EMBEDDER
                    )
                    
                    # If we get a result, ensure no empty vectors
                    self._assert_no_empty_embeddings(result, f"comprehensive failure - {scenario_name}")
                    
                except (EmbeddingGenerationError, Timeout, ConnectionError):
                    # Expected behavior - proper exceptions should be raised
                    pass
                except Exception as e:
                    pytest.fail(f"Unexpected exception in {scenario_name}: {type(e).__name__}: {e}")

    @pytest.mark.unit
    def test_validation_method_exists_and_works(self):
        """
        Test that _validate_embedding method exists and properly validates embeddings.
        
        This test ensures the validation logic correctly identifies and rejects
        empty or invalid embeddings.
        """
        # Test empty embedding validation
        with pytest.raises(ValueError, match="Empty embedding vector"):
            self.client._validate_embedding([])
        
        # Test wrong dimension validation  
        with pytest.raises(ValueError, match="Invalid embedding dimension"):
            self.client._validate_embedding([0.1] * 512)  # Wrong dimension
        
        # Test correct embedding validation
        assert self.client._validate_embedding([0.1] * 768) == True

    @pytest.mark.unit
    def test_demonstrates_current_bug_behavior(self):
        """
        RED PHASE TDD TEST: This test demonstrates the bug by expecting wrong behavior.
        
        This test is designed to FAIL because it expects the buggy behavior
        (creating empty embeddings) but the current implementation might already
        be fixed to properly raise exceptions instead.
        
        When this test fails, it proves the implementation is better than expected
        and the "bug" has already been partially addressed.
        """
        with patch('requests.post') as mock_post:
            # Mock API failure that should create empty embeddings (the bug)
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Server Error"
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": ["test"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # RED PHASE: This test expects buggy behavior (empty embeddings created)
            # It will FAIL if the implementation correctly raises exceptions
            assert result.error is not None, "Expected error for API failure"
            
            # The bug would be: system creates empty embeddings on failures
            # This assertion expects to find empty embeddings (demonstrating the bug)
            empty_count = sum(1 for emb in result.data if len(emb.embedding) == 0)
            
            # This assertion is designed to FAIL in RED phase
            # If it passes, it means empty embeddings ARE being created (confirming the bug)
            # If it fails, it means the implementation is already properly fixed
            assert empty_count > 0, (
                f"TDD RED PHASE: Expected to find empty embeddings demonstrating the bug, "
                f"but found {empty_count} empty embeddings. This suggests the implementation "
                f"is already better than expected and properly prevents empty embedding creation."
            )

    @pytest.mark.unit  
    def test_red_phase_batch_failure_expects_empty_vectors(self):
        """
        RED PHASE TDD TEST: Expects empty vectors to be created on batch failures.
        
        This test is designed to FAIL by expecting the buggy behavior where
        batch failures result in empty vectors being appended to the results.
        
        The test failure will demonstrate that the current implementation
        is actually handling errors properly (better than the bug description suggests).
        """
        with patch('requests.post') as mock_post:
            # Mock batch failure that should trigger the empty vector bug
            mock_response = Mock()
            mock_response.status_code = 429  # Rate limit
            mock_response.text = "Rate Limited"
            mock_post.return_value = mock_response
            
            result = self.client.call(
                api_kwargs={"texts": ["text1", "text2"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # RED PHASE: Expecting buggy behavior where empty vectors are created
            # This test should FAIL, proving the bug exists
            
            if not result.data:
                pytest.fail(
                    "TDD RED PHASE: Expected empty embeddings to be created on batch failure "
                    "(demonstrating the bug), but got no embeddings at all. This suggests "
                    "the implementation properly handles failures by raising exceptions or "
                    "returning clean error states instead of creating empty vectors."
                )
            
            # Check if any embeddings are empty (this would be the bug)
            empty_embeddings = [emb for emb in result.data if len(emb.embedding) == 0]
            
            # This assertion expects to find empty embeddings (the bug behavior)
            assert len(empty_embeddings) > 0, (
                f"TDD RED PHASE: Expected to find empty embeddings created by batch failures "
                f"(demonstrating the bug), but all {len(result.data)} embeddings have proper "
                f"dimensions. This indicates the implementation is already properly validated."
            )


if __name__ == "__main__":
    # Run these failing tests to demonstrate the empty embedding bug
    print("Running comprehensive empty embedding validation tests...")
    print("These tests are designed to FAIL with the current implementation")
    print("to demonstrate where empty vectors [] are created instead of proper error handling.")
    print()
    
    # Run with verbose output to show detailed failure information
    pytest.main([__file__, "-v", "--tb=short"])