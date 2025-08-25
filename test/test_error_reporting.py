"""
Test Error Reporting Quality for Google Embedding Client and Data Pipeline

This test suite validates error message quality and user experience.
These tests are designed to FAIL initially (RED phase of TDD) to demonstrate
the need for implementing better error reporting.

Tests cover:
1. Error messages include document identification
2. Failure reasons are specific and actionable
3. Batch processing provides failure summaries
4. API errors provide actionable guidance
5. Quota/auth/size errors are informative
6. Network/timeout errors suggest retries

These tests check that current error messages are generic and unhelpful,
failing to identify which documents caused issues or provide actionable guidance.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
import requests.exceptions

from adalflow.core.types import ModelType, Document, Embedding, EmbedderOutput
from api.google_embedding_client import GoogleEmbeddingClient, EmbeddingGenerationError
from api.data_pipeline import transform_documents_and_save_to_db, prepare_data_pipeline


class TestErrorReporting:
    """
    Test suite for error reporting quality and user experience.
    
    These tests are designed to FAIL initially to demonstrate the need
    for implementing better error messages in GoogleEmbeddingClient and data pipeline.
    """

    def setup_method(self):
        """Set up test environment before each test."""
        self.client = GoogleEmbeddingClient(api_key="test_api_key")
        self.sample_documents = [
            Document(
                text="First document content about Python programming",
                meta_data={"file_path": "src/main.py", "type": "py", "is_code": True}
            ),
            Document(
                text="Second document content about JavaScript functions", 
                meta_data={"file_path": "js/utils.js", "type": "js", "is_code": True}
            ),
            Document(
                text="Third document content about API documentation",
                meta_data={"file_path": "docs/api.md", "type": "md", "is_code": False}
            )
        ]

    @pytest.mark.unit
    def test_error_message_includes_document_info(self):
        """
        Test that errors identify which document failed processing.
        
        EXPECTED TO FAIL: Current implementation doesn't identify failing documents.
        """
        # Mock API failure for specific document in batch processing
        responses = [
            Mock(status_code=400, text='{"error": {"message": "Invalid input"}}'),
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.1] * 768}}),
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.2] * 768}})
        ]
        
        with patch('requests.post', side_effect=responses):
            result = self.client.call(
                api_kwargs={"texts": ["invalid content", "valid content", "more valid content"], 
                           "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current error messages don't identify documents
            assert result.error is not None, "Should report error for failed document"
            
            # Error should identify which document failed (index 0)
            assert "document" in result.error.lower() or "index" in result.error.lower(), (
                f"Error message should identify which document failed. Got: '{result.error}'. "
                f"Current implementation doesn't identify failing documents in error messages."
            )
            
            # Error should include document snippet or identifier
            assert "invalid content" in result.error or "index 0" in result.error, (
                f"Error message should include document identifier or snippet. Got: '{result.error}'. "
                f"Users need to know which specific document caused the failure."
            )

    @pytest.mark.unit
    def test_failure_reason_specificity(self):
        """
        Test that failure reasons are specific rather than generic.
        
        EXPECTED TO FAIL: Current implementation provides generic error messages.
        """
        test_cases = [
            {
                "status_code": 429, 
                "response_text": '{"error": {"message": "Quota exceeded"}}',
                "expected_keywords": ["quota", "rate limit", "per minute"],
                "scenario": "API quota exceeded"
            },
            {
                "status_code": 401,
                "response_text": '{"error": {"message": "Invalid API key"}}', 
                "expected_keywords": ["api key", "authentication", "credentials"],
                "scenario": "Invalid credentials"
            },
            {
                "status_code": 413,
                "response_text": '{"error": {"message": "Request too large"}}',
                "expected_keywords": ["too large", "size limit", "content length"],
                "scenario": "Content too large"
            }
        ]
        
        for case in test_cases:
            with patch('requests.post', return_value=Mock(status_code=case["status_code"], 
                                                        text=case["response_text"])):
                result = self.client.call(
                    api_kwargs={"texts": ["test content"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # This assertion WILL FAIL because current errors are generic
                assert result.error is not None, f"Should report error for {case['scenario']}"
                
                # Error should contain specific keywords indicating the failure reason
                error_lower = result.error.lower()
                has_specific_keywords = any(keyword in error_lower for keyword in case["expected_keywords"])
                assert has_specific_keywords, (
                    f"Error message for {case['scenario']} should contain specific keywords {case['expected_keywords']}. "
                    f"Got: '{result.error}'. Current implementation provides generic error messages."
                )

    @pytest.mark.unit
    def test_batch_failure_summary(self):
        """
        Test that batch processing provides failure summary with counts.
        
        EXPECTED TO FAIL: Current implementation doesn't provide batch summaries.
        """
        # Simulate batch with mixed success/failure: batch fails, single requests have mixed results
        batch_response = Mock(status_code=503, text="Service Unavailable")
        single_responses = [
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.1] * 768}}),  # Success
            Mock(status_code=400, text='{"error": {"message": "Invalid input"}}'),        # Fail
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.2] * 768}}),  # Success
            Mock(status_code=429, text='{"error": {"message": "Rate limited"}}'),        # Fail
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.3] * 768}})   # Success
        ]
        
        with patch('requests.post', side_effect=[batch_response] + single_responses):
            result = self.client.call(
                api_kwargs={"texts": ["text1", "text2", "text3", "text4", "text5"], 
                           "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current implementation doesn't provide summaries
            assert result.error is not None, "Should report error summary for batch failures"
            
            # Error should include batch summary with counts
            summary_keywords = ["total", "successful", "failed", "processed"]
            has_summary = any(keyword in result.error.lower() for keyword in summary_keywords)
            assert has_summary, (
                f"Error message should include batch summary with counts. Got: '{result.error}'. "
                f"Current implementation doesn't provide batch processing summaries."
            )
            
            # Should indicate which specific documents failed
            assert "index" in result.error.lower() or "document" in result.error.lower(), (
                f"Error message should identify which documents failed. Got: '{result.error}'. "
                f"Users need to know which specific documents in the batch failed."
            )

    @pytest.mark.unit
    def test_actionable_error_guidance(self):
        """
        Test that errors provide actionable next steps for resolution.
        
        EXPECTED TO FAIL: Current implementation doesn't provide actionable guidance.
        """
        guidance_cases = [
            {
                "status_code": 429,
                "response_text": '{"error": {"message": "Rate limit exceeded"}}',
                "expected_guidance": ["retry", "wait", "reduce", "later"],
                "scenario": "Rate limiting"
            },
            {
                "status_code": 401, 
                "response_text": '{"error": {"message": "Invalid API key"}}',
                "expected_guidance": ["check", "verify", "api key", "credentials"],
                "scenario": "Authentication failure"
            },
            {
                "status_code": 413,
                "response_text": '{"error": {"message": "Payload too large"}}', 
                "expected_guidance": ["reduce", "split", "smaller", "chunk"],
                "scenario": "Content too large"
            }
        ]
        
        for case in guidance_cases:
            with patch('requests.post', return_value=Mock(status_code=case["status_code"],
                                                        text=case["response_text"])):
                result = self.client.call(
                    api_kwargs={"texts": ["test content"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # This assertion WILL FAIL because current errors lack actionable guidance
                assert result.error is not None, f"Should report error for {case['scenario']}"
                
                error_lower = result.error.lower()
                has_guidance = any(guide in error_lower for guide in case["expected_guidance"])
                assert has_guidance, (
                    f"Error message for {case['scenario']} should provide actionable guidance "
                    f"containing keywords {case['expected_guidance']}. Got: '{result.error}'. "
                    f"Current implementation doesn't provide actionable guidance for error resolution."
                )

    @pytest.mark.unit
    def test_api_quota_error_message(self):
        """
        Test that API quota errors are informative about limits and timing.
        
        EXPECTED TO FAIL: Current quota errors lack specific guidance.
        """
        quota_response = Mock(
            status_code=429,
            text='{"error": {"message": "Quota exceeded for requests per minute"}}',
            headers={"Retry-After": "60"}
        )
        
        with patch('requests.post', return_value=quota_response):
            result = self.client.call(
                api_kwargs={"texts": ["test content"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current quota errors lack detail
            assert result.error is not None, "Should report quota error"
            
            error_lower = result.error.lower()
            
            # Should mention specific quota type
            assert "quota" in error_lower or "rate limit" in error_lower, (
                f"Error should mention quota/rate limiting. Got: '{result.error}'. "
                f"Current implementation doesn't specify quota type."
            )
            
            # Should provide timing guidance
            timing_keywords = ["minute", "retry", "wait", "60", "later"]
            has_timing = any(keyword in error_lower for keyword in timing_keywords)
            assert has_timing, (
                f"Error should provide timing guidance for quota recovery. Got: '{result.error}'. "
                f"Current implementation doesn't provide retry timing information."
            )

    @pytest.mark.unit
    def test_invalid_credentials_error(self):
        """
        Test that authentication errors provide clear guidance.
        
        EXPECTED TO FAIL: Current auth errors are generic.
        """
        auth_response = Mock(
            status_code=401,
            text='{"error": {"message": "API key not valid. Please pass a valid API key."}}'
        )
        
        with patch('requests.post', return_value=auth_response):
            result = self.client.call(
                api_kwargs={"texts": ["test content"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current auth errors lack guidance
            assert result.error is not None, "Should report authentication error"
            
            error_lower = result.error.lower()
            
            # Should clearly indicate authentication issue
            auth_keywords = ["api key", "authentication", "credentials", "unauthorized"]
            has_auth_info = any(keyword in error_lower for keyword in auth_keywords)
            assert has_auth_info, (
                f"Error should clearly indicate authentication issue. Got: '{result.error}'. "
                f"Current implementation doesn't clearly identify authentication problems."
            )
            
            # Should provide resolution steps
            resolution_keywords = ["check", "verify", "environment", "variable", "set"]
            has_resolution = any(keyword in error_lower for keyword in resolution_keywords)
            assert has_resolution, (
                f"Error should provide resolution steps for authentication. Got: '{result.error}'. "
                f"Current implementation doesn't guide users on fixing authentication issues."
            )

    @pytest.mark.unit
    def test_document_too_large_error(self):
        """
        Test that document size limit errors provide helpful guidance.
        
        EXPECTED TO FAIL: Current size errors don't provide splitting guidance.
        """
        size_response = Mock(
            status_code=413,
            text='{"error": {"message": "Request payload is too large"}}'
        )
        
        with patch('requests.post', return_value=size_response):
            result = self.client.call(
                api_kwargs={"texts": ["x" * 10000], "model": "text-embedding-004"},  # Large content
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current size errors lack guidance
            assert result.error is not None, "Should report size limit error"
            
            error_lower = result.error.lower()
            
            # Should identify size issue
            size_keywords = ["large", "size", "limit", "payload", "too big"]
            has_size_info = any(keyword in error_lower for keyword in size_keywords)
            assert has_size_info, (
                f"Error should identify size/limit issue. Got: '{result.error}'. "
                f"Current implementation doesn't clearly identify size limit problems."
            )
            
            # Should suggest splitting/chunking
            solution_keywords = ["split", "chunk", "smaller", "reduce", "break up"]
            has_solution = any(keyword in error_lower for keyword in solution_keywords)
            assert has_solution, (
                f"Error should suggest splitting large documents. Got: '{result.error}'. "
                f"Current implementation doesn't provide guidance on handling large documents."
            )

    @pytest.mark.unit
    def test_network_error_guidance(self):
        """
        Test that network errors suggest retry strategies.
        
        EXPECTED TO FAIL: Current network errors don't suggest retries.
        """
        network_errors = [
            requests.exceptions.Timeout("Request timed out"),
            requests.exceptions.ConnectionError("Failed to establish connection"),
            requests.exceptions.HTTPError("HTTP Error")
        ]
        
        for error in network_errors:
            with patch('requests.post', side_effect=error):
                result = self.client.call(
                    api_kwargs={"texts": ["test content"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # This assertion WILL FAIL because current network errors lack retry guidance
                assert result.error is not None, f"Should report network error for {type(error).__name__}"
                
                error_lower = result.error.lower()
                
                # Should identify network issue
                network_keywords = ["network", "connection", "timeout", "unreachable"]
                has_network_info = any(keyword in error_lower for keyword in network_keywords)
                assert has_network_info, (
                    f"Error should identify network issue for {type(error).__name__}. Got: '{result.error}'. "
                    f"Current implementation doesn't clearly identify network problems."
                )
                
                # Should suggest retry strategy
                retry_keywords = ["retry", "try again", "later", "temporary", "transient"]
                has_retry_suggestion = any(keyword in error_lower for keyword in retry_keywords)
                assert has_retry_suggestion, (
                    f"Error should suggest retry for {type(error).__name__}. Got: '{result.error}'. "
                    f"Current implementation doesn't suggest retry strategies for network errors."
                )

    @pytest.mark.unit 
    def test_data_pipeline_error_context(self):
        """
        Test that data pipeline errors include context about document processing.
        
        EXPECTED TO FAIL: Current pipeline errors lack document context.
        """
        # Mock embedding failure in data pipeline
        with patch.object(self.client, 'call', return_value=EmbedderOutput(
            data=[], 
            error="Embedding generation failed",
            raw_response=None
        )):
            try:
                # This should fail during transform_documents_and_save_to_db
                transform_documents_and_save_to_db(
                    self.sample_documents, 
                    "/tmp/test_db.pkl", 
                    is_ollama_embedder=False
                )
                pytest.fail("Expected transformation to fail with embedding error")
            except Exception as e:
                error_msg = str(e)
                
                # This assertion WILL FAIL because pipeline errors lack document context
                # Should include information about which documents were being processed
                doc_context_keywords = ["document", "processing", "file", "total", "failed"]
                has_doc_context = any(keyword in error_msg.lower() for keyword in doc_context_keywords)
                assert has_doc_context, (
                    f"Pipeline error should include document processing context. Got: '{error_msg}'. "
                    f"Current implementation doesn't provide context about document processing failures."
                )
                
                # Should mention specific files or counts
                has_specifics = any(doc.meta_data.get("file_path", "") in error_msg 
                                  for doc in self.sample_documents)
                assert has_specifics, (
                    f"Pipeline error should mention specific files being processed. Got: '{error_msg}'. "
                    f"Current implementation doesn't identify which documents failed during pipeline processing."
                )

    @pytest.mark.unit
    def test_batch_partial_failure_reporting(self):
        """
        Test that partial batch failures report both success and failure counts.
        
        EXPECTED TO FAIL: Current implementation doesn't provide detailed batch reporting.
        """
        # Simulate mixed batch results (some succeed, some fail)
        batch_response = Mock(status_code=503, text="Service Unavailable")  # Force fallback
        single_responses = [
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.1] * 768}}),  # Doc 0: Success
            Mock(status_code=400, text='{"error": {"message": "Invalid input"}}'),        # Doc 1: Fail  
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.2] * 768}}),  # Doc 2: Success
        ]
        
        with patch('requests.post', side_effect=[batch_response] + single_responses):
            result = self.client.call(
                api_kwargs={"texts": ["doc1 content", "invalid doc2", "doc3 content"], 
                           "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # Should have partial results with error summary
            assert len(result.data) > 0, "Should have some successful embeddings"
            assert result.error is not None, "Should report error summary for partial failures"
            
            # This assertion WILL FAIL because current implementation doesn't provide detailed summaries
            error_lower = result.error.lower()
            
            # Should report success/failure counts
            count_keywords = ["successful", "failed", "processed", "total", "2", "1"]  # 2 success, 1 failure
            has_counts = any(keyword in error_lower for keyword in count_keywords)
            assert has_counts, (
                f"Error should report success/failure counts for partial batch failures. Got: '{result.error}'. "
                f"Current implementation doesn't provide detailed batch processing statistics."
            )
            
            # Should identify which specific document failed
            assert "1" in result.error or "index" in error_lower, (
                f"Error should identify which document failed (index 1). Got: '{result.error}'. "
                f"Current implementation doesn't identify specific failing documents in batch operations."
            )

    @pytest.mark.unit
    def test_embedding_validation_error_details(self):
        """
        Test that embedding validation errors provide specific dimension details.
        
        EXPECTED TO FAIL: Current validation errors are generic.
        """
        # Mock API returning invalid embedding dimensions
        invalid_response = Mock(
            status_code=200,
            json=lambda: {"embeddings": [{"values": [0.1] * 512}]}  # Wrong dimension (512 instead of 768)
        )
        
        with patch('requests.post', return_value=invalid_response):
            result = self.client.call(
                api_kwargs={"texts": ["test content"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # This assertion WILL FAIL because current validation errors lack dimension details
            assert result.error is not None or len(result.data) == 0, (
                "Should report validation error for wrong dimensions"
            )
            
            if result.error:
                error_lower = result.error.lower()
                
                # Should mention specific dimensions
                dimension_keywords = ["dimension", "512", "768", "expected", "invalid"]
                has_dimension_info = any(keyword in error_lower for keyword in dimension_keywords)
                assert has_dimension_info, (
                    f"Validation error should include dimension details. Got: '{result.error}'. "
                    f"Current implementation doesn't provide specific dimension validation information."
                )


if __name__ == "__main__":
    # Run the tests to demonstrate failures (RED phase)
    pytest.main([__file__, "-v", "--tb=short"])