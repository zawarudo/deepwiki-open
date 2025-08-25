"""
Test Batch Retry Logic for GoogleEmbeddingClient

This test suite validates retry logic for transient API failures.
These tests are designed to FAIL initially (RED phase of TDD) to demonstrate
the need for implementing robust retry mechanisms.

Tests cover:
1. Transient failures trigger retries
2. Exponential backoff timing
3. Max retry limits are enforced
4. Partial batch success preservation
5. Rate limiting (429) handling
6. Network timeout handling
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, call, MagicMock
from typing import List, Dict, Any

from adalflow.core.types import ModelType, Embedding, EmbedderOutput

from api.google_embedding_client import GoogleEmbeddingClient, EmbeddingGenerationError


class TestBatchRetryLogic:
    """
    Test suite for batch embedding retry logic.
    
    These tests are designed to FAIL initially to demonstrate the need
    for implementing retry logic in the GoogleEmbeddingClient.
    """

    def setup_method(self):
        """Set up test environment before each test."""
        self.client = GoogleEmbeddingClient(api_key="test_api_key")

    @pytest.mark.unit
    def test_transient_failure_triggers_retry(self):
        """
        Test that transient API failures trigger retries.
        
        EXPECTED TO FAIL: Current implementation doesn't retry on failures.
        """
        # Simulate API failure followed by success
        responses = [
            Mock(status_code=503, text="Service Unavailable"),  # First attempt fails
            Mock(status_code=503, text="Service Unavailable"),  # Second attempt fails  
            Mock(status_code=200, json=lambda: {  # Third attempt succeeds
                "embeddings": [{"values": [0.1] * 768}]
            })
        ]
        
        with patch('requests.post', side_effect=responses) as mock_post:
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't retry
            # After implementing retry logic, this should pass
            assert mock_post.call_count == 3, (
                f"Expected 3 API calls (2 failures + 1 success), got {mock_post.call_count}. "
                f"Current implementation doesn't retry transient failures."
            )
            
            # Should eventually succeed after retries
            assert result.error is None, "Retries should eventually succeed"
            assert len(result.data) == 1, "Should return one embedding after retry success"
            assert len(result.data[0].embedding) == 768, "Embedding should have correct dimensions"

    @pytest.mark.unit
    def test_exponential_backoff_timing(self):
        """
        Test exponential backoff between retries (1, 2, 4, 8 seconds).
        
        EXPECTED TO FAIL: Current implementation has no backoff logic.
        """
        # Mock time.sleep to capture backoff timing
        responses = [
            Mock(status_code=503, text="Service Unavailable"),  # 1st attempt
            Mock(status_code=503, text="Service Unavailable"),  # 2nd attempt (after 1s)
            Mock(status_code=503, text="Service Unavailable"),  # 3rd attempt (after 2s)
            Mock(status_code=200, json=lambda: {  # 4th attempt succeeds (after 4s)
                "embeddings": [{"values": [0.1] * 768}]
            })
        ]
        
        with patch('requests.post', side_effect=responses) as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't implement backoff
            expected_sleep_calls = [call(1), call(2), call(4)]
            assert mock_sleep.call_count == 3, (
                f"Expected 3 sleep calls for exponential backoff, got {mock_sleep.call_count}. "
                f"Current implementation has no backoff logic."
            )
            
            # Verify exponential backoff pattern: 1, 2, 4 seconds
            actual_calls = mock_sleep.call_args_list
            assert actual_calls == expected_sleep_calls, (
                f"Expected exponential backoff pattern [1, 2, 4], got {[c[0][0] for c in actual_calls]}. "
                f"Current implementation doesn't implement exponential backoff."
            )

    @pytest.mark.unit
    def test_max_retry_limit_enforced(self):
        """
        Test that retries stop after max attempts (3 retries total).
        
        EXPECTED TO FAIL: Current implementation doesn't limit retries.
        """
        # Create API responses that always fail
        failing_response = Mock(status_code=503, text="Service Unavailable")
        
        with patch('requests.post', return_value=failing_response) as mock_post:
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't retry
            # Should make exactly 1 initial attempt + 3 retries = 4 total calls
            max_retries = 3
            expected_calls = 1 + max_retries
            assert mock_post.call_count == expected_calls, (
                f"Expected {expected_calls} API calls (1 initial + {max_retries} retries), "
                f"got {mock_post.call_count}. Current implementation doesn't implement retry limits."
            )
            
            # Should report error after max retries exhausted
            assert result.error is not None, "Should report error after max retries exceeded"
            assert "retry" in result.error.lower() or "attempt" in result.error.lower(), (
                "Error message should indicate retry exhaustion"
            )

    @pytest.mark.unit
    def test_partial_batch_success_preserved(self):
        """
        Test that successful embeddings in batch are kept during retries.
        
        EXPECTED TO FAIL: Current implementation doesn't preserve partial success.
        """
        # First call: batch fails, fallback to single requests
        # Single requests: first succeeds, second fails initially then succeeds on retry
        batch_response = Mock(status_code=503, text="Service Unavailable")
        
        single_responses = [
            # First text succeeds immediately
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.1] * 768}}),
            # Second text fails then succeeds
            Mock(status_code=503, text="Service Unavailable"),
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.2] * 768}})
        ]
        
        with patch('requests.post', side_effect=[batch_response] + single_responses) as mock_post:
            result = self.client.call(
                api_kwargs={"texts": ["text1", "text2"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't preserve partial success
            # Should have called batch + 2 single requests + 1 retry for second text = 4 total
            assert mock_post.call_count == 4, (
                f"Expected 4 API calls (1 batch + 2 single + 1 retry), got {mock_post.call_count}. "
                f"Current implementation doesn't preserve partial success during retries."
            )
            
            # Should return both embeddings after retries succeed
            assert len(result.data) == 2, (
                f"Expected 2 embeddings after partial retry, got {len(result.data)}. "
                f"Current implementation doesn't preserve successful embeddings during retries."
            )
            
            # Verify both embeddings are valid
            for i, embedding in enumerate(result.data):
                assert len(embedding.embedding) == 768, f"Embedding {i} should have 768 dimensions"
                assert embedding.index == i, f"Embedding {i} should have correct index"

    @pytest.mark.unit
    def test_rate_limit_429_retry(self):
        """
        Test that 429 (Rate Limited) errors trigger retries with longer backoff.
        
        EXPECTED TO FAIL: Current implementation doesn't handle 429 errors specially.
        """
        responses = [
            Mock(status_code=429, text="Rate limit exceeded", headers={"Retry-After": "5"}),
            Mock(status_code=429, text="Rate limit exceeded", headers={"Retry-After": "10"}),
            Mock(status_code=200, json=lambda: {"embeddings": [{"values": [0.1] * 768}]})
        ]
        
        with patch('requests.post', side_effect=responses) as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't retry 429 errors
            assert mock_post.call_count == 3, (
                f"Expected 3 API calls for 429 retry handling, got {mock_post.call_count}. "
                f"Current implementation doesn't retry rate limit errors."
            )
            
            # Should respect Retry-After headers for 429 errors
            expected_sleep_calls = [call(5), call(10)]
            assert mock_sleep.call_count == 2, (
                f"Expected 2 sleep calls for 429 backoff, got {mock_sleep.call_count}. "
                f"Current implementation doesn't handle Retry-After headers."
            )
            
            actual_calls = mock_sleep.call_args_list
            assert actual_calls == expected_sleep_calls, (
                f"Expected sleep calls respecting Retry-After: [5, 10], got {[c[0][0] for c in actual_calls]}. "
                f"Current implementation doesn't respect rate limit headers."
            )

    @pytest.mark.unit
    def test_network_timeout_retry(self):
        """
        Test that network timeouts trigger retries.
        
        EXPECTED TO FAIL: Current implementation doesn't retry on timeouts.
        """
        import requests.exceptions
        
        # Simulate timeout followed by success
        side_effects = [
            requests.exceptions.Timeout("Request timed out"),
            requests.exceptions.Timeout("Request timed out"),
            Mock(status_code=200, json=lambda: {"embeddings": [{"values": [0.1] * 768}]})
        ]
        
        with patch('requests.post', side_effect=side_effects) as mock_post:
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't retry timeouts
            assert mock_post.call_count == 3, (
                f"Expected 3 API calls for timeout retry, got {mock_post.call_count}. "
                f"Current implementation doesn't retry network timeouts."
            )
            
            # Should eventually succeed after timeout retries
            assert result.error is None, (
                "Network timeout retries should eventually succeed"
            )
            assert len(result.data) == 1, "Should return embedding after timeout retry success"

    @pytest.mark.unit  
    def test_connection_error_retry(self):
        """
        Test that connection errors trigger retries.
        
        EXPECTED TO FAIL: Current implementation doesn't retry connection errors.
        """
        import requests.exceptions
        
        side_effects = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.ConnectionError("Connection failed"), 
            Mock(status_code=200, json=lambda: {"embeddings": [{"values": [0.1] * 768}]})
        ]
        
        with patch('requests.post', side_effect=side_effects) as mock_post:
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't retry connections
            assert mock_post.call_count == 3, (
                f"Expected 3 API calls for connection retry, got {mock_post.call_count}. "
                f"Current implementation doesn't retry connection errors."
            )
            
            assert result.error is None, "Connection error retries should eventually succeed"
            assert len(result.data) == 1, "Should return embedding after connection retry success"

    @pytest.mark.unit
    def test_mixed_transient_and_permanent_errors(self):
        """
        Test handling of mixed error types - some retryable, some not.
        
        EXPECTED TO FAIL: Current implementation doesn't distinguish error types.
        """
        # 400 errors should NOT be retried (permanent), 503 errors should be retried
        responses = [
            Mock(status_code=503, text="Service Unavailable"),  # Retryable
            Mock(status_code=400, text="Bad Request")           # Not retryable - should fail fast
        ]
        
        with patch('requests.post', side_effect=responses) as mock_post:
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't distinguish error types
            # Should retry 503, then encounter 400 and stop (2 calls total)
            assert mock_post.call_count == 2, (
                f"Expected 2 API calls (503 retry, then 400 stop), got {mock_post.call_count}. "
                f"Current implementation doesn't distinguish between retryable and permanent errors."
            )
            
            # Should report the permanent error (400), not the transient one (503)
            assert result.error is not None, "Should report the permanent error"
            assert "400" in result.error or "Bad Request" in result.error, (
                "Error message should reflect the permanent 400 error, not the transient 503"
            )

    @pytest.mark.unit
    def test_retry_preserves_embedding_indices(self):
        """
        Test that retry logic preserves correct embedding indices.
        
        EXPECTED TO FAIL: Current implementation doesn't track indices during retries.
        """
        # Batch fails, single requests: first fails then succeeds, second succeeds immediately
        batch_response = Mock(status_code=503, text="Service Unavailable")
        single_responses = [
            Mock(status_code=503, text="Service Unavailable"),  # First text fails
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.1] * 768}}),  # First text retry succeeds
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.2] * 768}})   # Second text succeeds
        ]
        
        with patch('requests.post', side_effect=[batch_response] + single_responses) as mock_post:
            result = self.client.call(
                api_kwargs={"texts": ["text1", "text2"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't preserve indices during retries
            assert len(result.data) == 2, "Should return 2 embeddings after retries"
            
            # Verify indices are preserved correctly
            indices = [emb.index for emb in result.data]
            assert indices == [0, 1], (
                f"Expected embedding indices [0, 1], got {indices}. "
                f"Current implementation doesn't preserve indices during retry logic."
            )

    @pytest.mark.unit
    def test_retry_configuration_respected(self):
        """
        Test that retry configuration (max attempts, backoff) can be configured.
        
        EXPECTED TO FAIL: Current implementation has no retry configuration.
        """
        # This test assumes a future retry configuration mechanism
        custom_max_retries = 2  # Different from default of 3
        custom_base_delay = 0.5  # Different from default of 1
        
        # Mock the client with custom retry config (this interface doesn't exist yet)
        # In the future implementation, this might look like:
        # self.client.retry_config = {"max_retries": custom_max_retries, "base_delay": custom_base_delay}
        
        failing_response = Mock(status_code=503, text="Service Unavailable")
        
        with patch('requests.post', return_value=failing_response) as mock_post, \
             patch('time.sleep') as mock_sleep:
            
            result = self.client.call(
                api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't support retry configuration
            expected_calls = 1 + custom_max_retries  # 1 initial + 2 retries = 3 total
            assert mock_post.call_count == expected_calls, (
                f"Expected {expected_calls} API calls with custom max_retries={custom_max_retries}, "
                f"got {mock_post.call_count}. Current implementation doesn't support retry configuration."
            )
            
            # Verify custom backoff delays
            expected_delays = [custom_base_delay, custom_base_delay * 2]  # 0.5, 1.0
            if mock_sleep.call_count > 0:
                actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
                assert actual_delays == expected_delays, (
                    f"Expected custom backoff delays {expected_delays}, got {actual_delays}. "
                    f"Current implementation doesn't support configurable backoff."
                )

    @pytest.mark.unit
    def test_concurrent_retry_safety(self):
        """
        Test that retry logic is safe for concurrent operations.
        
        EXPECTED TO FAIL: Current implementation doesn't handle concurrency in retries.
        """
        # This test would verify that multiple concurrent calls with retries
        # don't interfere with each other's state
        
        import threading
        import concurrent.futures
        
        responses = [
            Mock(status_code=503, text="Service Unavailable"),
            Mock(status_code=200, json=lambda: {"embeddings": [{"values": [0.1] * 768}]})
        ]
        
        results = []
        call_counts = []
        
        def make_embedding_call():
            with patch('requests.post', side_effect=responses) as mock_post:
                result = self.client.call(
                    api_kwargs={"texts": ["test text"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                results.append(result)
                call_counts.append(mock_post.call_count)
                return result
        
        # Run multiple concurrent embedding calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_embedding_call) for _ in range(3)]
            concurrent.futures.wait(futures)
        
        # This assertion WILL FAIL because current implementation doesn't implement retry safety
        # Each call should have made 2 requests (1 fail + 1 retry success)
        for i, count in enumerate(call_counts):
            assert count == 2, (
                f"Concurrent call {i} expected 2 API calls (1 + 1 retry), got {count}. "
                f"Current implementation doesn't handle concurrent retry operations safely."
            )
        
        # All calls should eventually succeed
        assert len(results) == 3, "Should have 3 concurrent results"
        for i, result in enumerate(results):
            assert result.error is None, f"Concurrent call {i} should succeed after retry"
            assert len(result.data) == 1, f"Concurrent call {i} should return 1 embedding"


if __name__ == "__main__":
    # Run the tests to demonstrate failures (RED phase)
    pytest.main([__file__, "-v", "--tb=short"])