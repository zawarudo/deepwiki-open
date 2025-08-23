"""
Comprehensive tests for Google Embedding Client to identify empty vector generation bug.

Tests focus on batch processing logic, error handling, and fallback mechanisms
that could lead to zero vectors. Uses real API calls to test actual behavior.
"""

import pytest
import os
import logging
import json
import numpy as np
from typing import List, Dict, Any
from unittest.mock import patch, Mock

# Import the Google embedding client
from api.google_embedding_client import GoogleEmbeddingClient
from adalflow.core.types import ModelType, EmbedderOutput, Embedding

# Configure logging for detailed test output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestGoogleEmbeddingClient:
    """Test suite for Google Embedding Client focusing on empty vector generation."""

    @pytest.fixture
    def client(self):
        """Create Google embedding client instance."""
        # Use real API key if available, otherwise skip tests that need it
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "test-google-api-key":
            pytest.skip("Real GOOGLE_API_KEY required for integration tests")
        
        return GoogleEmbeddingClient(api_key=api_key)

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for unit tests."""
        return GoogleEmbeddingClient(api_key="test-key")

    def test_client_initialization(self):
        """Test client initialization with various configurations."""
        # Test with explicit API key
        client = GoogleEmbeddingClient(api_key="test-key")
        assert client._api_key == "test-key"
        assert client.base_url == "https://generativelanguage.googleapis.com/v1beta"
        
        # Test with custom base URL
        client = GoogleEmbeddingClient(api_key="test-key", base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"
        
        # Test API key retrieval
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key"}):
            client = GoogleEmbeddingClient()
            assert client._get_api_key() == "env-key"

    def test_missing_api_key_error(self):
        """Test that missing API key raises appropriate error."""
        with patch.dict(os.environ, {}, clear=True):
            client = GoogleEmbeddingClient()
            with pytest.raises(ValueError, match="Environment variable GOOGLE_API_KEY must be set"):
                client._get_api_key()

    def test_convert_inputs_to_api_kwargs_single_string(self, mock_client):
        """Test input conversion for single string input."""
        result = mock_client.convert_inputs_to_api_kwargs(
            input="Test document content",
            model_type=ModelType.EMBEDDER
        )
        
        assert result["texts"] == ["Test document content"]
        assert result["model"] == "text-embedding-004"

    def test_convert_inputs_to_api_kwargs_list_of_strings(self, mock_client):
        """Test input conversion for list of strings."""
        texts = ["First document", "Second document", "Third document"]
        result = mock_client.convert_inputs_to_api_kwargs(
            input=texts,
            model_type=ModelType.EMBEDDER
        )
        
        assert result["texts"] == texts
        assert result["model"] == "text-embedding-004"

    def test_convert_inputs_to_api_kwargs_custom_model(self, mock_client):
        """Test input conversion with custom model."""
        result = mock_client.convert_inputs_to_api_kwargs(
            input="Test content",
            model_kwargs={"model": "custom-embedding-model"},
            model_type=ModelType.EMBEDDER
        )
        
        assert result["texts"] == ["Test content"]
        assert result["model"] == "custom-embedding-model"

    def test_convert_inputs_unsupported_model_type(self, mock_client):
        """Test that unsupported model types raise error."""
        with pytest.raises(ValueError, match="model_type ModelType.UNDEFINED is not supported"):
            mock_client.convert_inputs_to_api_kwargs(
                input="Test content",
                model_type=ModelType.UNDEFINED
            )

    def test_empty_input_handling(self, mock_client):
        """Test handling of empty input list."""
        result = mock_client.call(
            api_kwargs={"texts": [], "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert result.data == []
        assert result.error is None

    @patch('requests.post')
    def test_single_document_embedding_success(self, mock_post, mock_client):
        """Test successful single document embedding."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [
                {"values": [0.1] * 768}
            ]
        }
        mock_post.return_value = mock_response
        
        result = mock_client.call(
            api_kwargs={"texts": ["Test document"], "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 1
        assert len(result.data[0].embedding) == 768
        assert result.data[0].index == 0
        assert result.error is None

    @patch('requests.post')
    def test_batch_embedding_success(self, mock_post, mock_client):
        """Test successful batch embedding processing."""
        # Mock successful batch API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [
                {"values": [0.1] * 768},
                {"values": [0.2] * 768},
                {"values": [0.3] * 768}
            ]
        }
        mock_post.return_value = mock_response
        
        texts = ["First document", "Second document", "Third document"]
        result = mock_client.call(
            api_kwargs={"texts": texts, "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 3
        for i, embedding in enumerate(result.data):
            assert len(embedding.embedding) == 768
            assert embedding.index == i
        assert result.error is None

    @patch('requests.post')
    def test_batch_api_failure_with_single_fallback_success(self, mock_post, mock_client):
        """Test batch API failure with successful single API fallback."""
        # First call (batch) fails
        batch_response = Mock()
        batch_response.status_code = 400
        batch_response.text = "Batch request failed"
        
        # Subsequent single calls succeed
        single_response = Mock()
        single_response.status_code = 200
        single_response.json.return_value = {
            "embedding": {"values": [0.1] * 768}
        }
        
        mock_post.side_effect = [batch_response, single_response, single_response]
        
        texts = ["First document", "Second document"]
        result = mock_client.call(
            api_kwargs={"texts": texts, "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 2
        for i, embedding in enumerate(result.data):
            assert len(embedding.embedding) == 768
            assert embedding.index == i
        assert result.error is None

    @patch('requests.post')
    def test_batch_and_single_api_failures_create_empty_vectors(self, mock_post, mock_client):
        """Test that API failures create empty vectors - this is the bug we're investigating."""
        # All API calls fail
        failed_response = Mock()
        failed_response.status_code = 400
        failed_response.text = "API request failed"
        mock_post.return_value = failed_response
        
        texts = ["First document", "Second document"]
        result = mock_client.call(
            api_kwargs={"texts": texts, "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 2
        
        # THIS IS THE BUG: API failures result in empty vectors
        for i, embedding in enumerate(result.data):
            assert len(embedding.embedding) == 0  # Empty vector!
            assert embedding.index == i
        
        # Error should be reported but data still returned
        assert result.error is not None
        assert "failed" in result.error.lower()
        
        logger.error(f"EMPTY VECTOR BUG REPRODUCED: {result.error}")
        logger.error(f"Empty embeddings created: {[len(e.embedding) for e in result.data]}")

    @patch('requests.post')
    def test_mixed_success_failure_batch(self, mock_post, mock_client):
        """Test batch with mixed success/failure responses."""
        # Batch fails, then individual calls have mixed results
        batch_response = Mock()
        batch_response.status_code = 400
        batch_response.text = "Batch failed"
        
        # First single call succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "embedding": {"values": [0.1] * 768}
        }
        
        # Second single call fails
        failed_response = Mock()
        failed_response.status_code = 400
        failed_response.text = "Single request failed"
        
        mock_post.side_effect = [batch_response, success_response, failed_response]
        
        texts = ["Success document", "Failed document"]
        result = mock_client.call(
            api_kwargs={"texts": texts, "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 2
        
        # First embedding should have values
        assert len(result.data[0].embedding) == 768
        assert result.data[0].index == 0
        
        # Second embedding should be empty (the bug!)
        assert len(result.data[1].embedding) == 0
        assert result.data[1].index == 1
        
        # Error should be reported
        assert result.error is not None
        
        logger.error(f"MIXED SUCCESS/FAILURE BUG: Valid={len(result.data[0].embedding)}, Empty={len(result.data[1].embedding)}")

    @patch('requests.post')
    def test_malformed_json_response_creates_empty_vectors(self, mock_post, mock_client):
        """Test that malformed JSON responses create empty vectors."""
        # Mock response with malformed JSON
        malformed_response = Mock()
        malformed_response.status_code = 200
        malformed_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        mock_post.return_value = malformed_response
        
        result = mock_client.call(
            api_kwargs={"texts": ["Test document"], "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        # JSON parsing errors cause complete failure, no data returned
        assert len(result.data) == 0
        assert result.error is not None
        assert "Invalid JSON" in result.error
        
        logger.error(f"JSON PARSING BUG: Malformed response causes complete failure with no embeddings")

    @patch('requests.post')
    def test_missing_values_key_creates_empty_vectors(self, mock_post, mock_client):
        """Test that missing 'values' key in response creates empty vectors."""
        # Mock response missing 'values' key
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [
                {"embedding": {}}  # Missing 'values' key
            ]
        }
        mock_post.return_value = mock_response
        
        result = mock_client.call(
            api_kwargs={"texts": ["Test document"], "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 1
        assert len(result.data[0].embedding) == 0  # Empty due to missing values
        assert result.error is None  # No error reported for this case
        
        logger.error(f"MISSING VALUES BUG: Response without values creates empty vector")

    @patch('requests.post')
    def test_embedding_count_mismatch_creates_empty_vectors(self, mock_post, mock_client):
        """Test that embedding count mismatch creates empty vectors."""
        # Mock response with fewer embeddings than input texts
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [
                {"values": [0.1] * 768}  # Only 1 embedding for 3 texts
            ]
        }
        mock_post.return_value = mock_response
        
        texts = ["First document", "Second document", "Third document"]
        result = mock_client.call(
            api_kwargs={"texts": texts, "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 3
        
        # First embedding should have values
        assert len(result.data[0].embedding) == 768
        
        # Second and third embeddings should be empty (the bug!)
        assert len(result.data[1].embedding) == 0
        assert len(result.data[2].embedding) == 0
        
        # Error should be reported
        assert result.error is not None
        # The error may not contain "mismatch" in the summary, but the warning was logged
        
        logger.error(f"COUNT MISMATCH BUG: 1 valid, 2 empty vectors created")

    @patch('requests.post')
    def test_large_batch_chunking(self, mock_post, mock_client):
        """Test large batch processing and chunking logic."""
        # Mock successful response for all chunks
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [{"values": [0.1] * 768} for _ in range(100)]
        }
        mock_post.return_value = mock_response
        
        # Create 250 documents (should be split into 3 chunks: 100, 100, 50)
        texts = [f"Document {i}" for i in range(250)]
        result = mock_client.call(
            api_kwargs={"texts": texts, "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 250
        
        # Verify all embeddings have correct indices
        for i, embedding in enumerate(result.data):
            assert embedding.index == i
            assert len(embedding.embedding) == 768

    @pytest.mark.integration
    def test_real_single_document_embedding(self, client):
        """Test real API call with single document."""
        result = client.call(
            api_kwargs={"texts": ["This is a test document for embedding."], "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 1
        assert len(result.data[0].embedding) == 768
        assert result.data[0].index == 0
        assert result.error is None
        
        # Verify embedding contains valid float values
        embedding = result.data[0].embedding
        assert all(isinstance(v, (int, float)) for v in embedding)
        assert not any(np.isnan(v) for v in embedding)
        assert not any(np.isinf(v) for v in embedding)
        
        logger.info(f"Real API test successful: embedding dimension={len(embedding)}")

    @pytest.mark.integration
    def test_real_batch_embedding(self, client):
        """Test real API call with batch of documents."""
        texts = [
            "First test document for batch embedding.",
            "Second document with different content.",
            "Third document to verify batch processing."
        ]
        
        result = client.call(
            api_kwargs={"texts": texts, "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert isinstance(result, EmbedderOutput)
        assert len(result.data) == 3
        assert result.error is None
        
        for i, embedding_obj in enumerate(result.data):
            assert len(embedding_obj.embedding) == 768
            assert embedding_obj.index == i
            
            # Verify embedding contains valid values
            embedding = embedding_obj.embedding
            assert all(isinstance(v, (int, float)) for v in embedding)
            assert not any(np.isnan(v) for v in embedding)
            assert not any(np.isinf(v) for v in embedding)
        
        logger.info(f"Real batch API test successful: {len(result.data)} embeddings generated")

    @pytest.mark.integration
    def test_real_edge_case_documents(self, client, edge_case_documents):
        """Test real API calls with edge case documents."""
        edge_cases = [
            ("very_short", edge_case_documents["very_short"]["content"]),
            ("special_chars", edge_case_documents["special_chars"]["content"]),
            ("unicode", edge_case_documents["unicode"]["content"])
        ]
        
        for case_name, content in edge_cases:
            result = client.call(
                api_kwargs={"texts": [content], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            logger.info(f"Testing edge case: {case_name}")
            logger.info(f"Content length: {len(content)}")
            logger.info(f"Embedding length: {len(result.data[0].embedding) if result.data else 0}")
            logger.info(f"Error: {result.error}")
            
            # Document findings for each case
            if len(result.data) == 0 or len(result.data[0].embedding) == 0:
                logger.error(f"EMPTY VECTOR BUG FOUND: {case_name} produces empty vector")
            else:
                logger.info(f"SUCCESS: {case_name} produces valid embedding")

    @pytest.mark.integration  
    def test_real_empty_document_handling(self, client):
        """Test real API handling of empty documents."""
        edge_cases = ["", "   ", "  \n\t  "]
        
        for i, content in enumerate(edge_cases):
            logger.info(f"Testing empty document case {i+1}: repr='{repr(content)}'")
            
            result = client.call(
                api_kwargs={"texts": [content], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            logger.info(f"Result data length: {len(result.data)}")
            if result.data:
                logger.info(f"Embedding length: {len(result.data[0].embedding)}")
            logger.info(f"Error: {result.error}")
            
            # This is critical for identifying the empty vector bug
            if result.data and len(result.data[0].embedding) == 0:
                logger.error(f"CRITICAL BUG: Empty/whitespace content creates empty vector")
            elif not result.data:
                logger.error(f"CRITICAL BUG: Empty/whitespace content returns no data")

    def test_error_handling_preserves_indices(self, mock_client):
        """Test that error handling preserves correct indices for embeddings."""
        with patch('requests.post') as mock_post:
            # Mixed batch and single responses  
            batch_response = Mock()
            batch_response.status_code = 400
            batch_response.text = "Batch failed"
            
            responses = [batch_response]
            # 5 single requests: success, fail, success, fail, success
            for i in range(5):
                if i % 2 == 0:  # Success
                    success_resp = Mock()
                    success_resp.status_code = 200
                    success_resp.json.return_value = {"embedding": {"values": [0.1] * 768}}
                    responses.append(success_resp)
                else:  # Failure
                    fail_resp = Mock()
                    fail_resp.status_code = 400
                    fail_resp.text = "Failed"
                    responses.append(fail_resp)
            
            mock_post.side_effect = responses
            
            texts = [f"Document {i}" for i in range(5)]
            result = mock_client.call(
                api_kwargs={"texts": texts, "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            assert len(result.data) == 5
            
            # Verify indices are preserved correctly
            for i, embedding in enumerate(result.data):
                assert embedding.index == i
                if i % 2 == 0:  # Should have valid embedding
                    assert len(embedding.embedding) == 768
                else:  # Should have empty embedding
                    assert len(embedding.embedding) == 0
            
            logger.error(f"INDEX PRESERVATION: Valid at indices {[i for i in range(5) if i % 2 == 0]}")
            logger.error(f"INDEX PRESERVATION: Empty at indices {[i for i in range(5) if i % 2 == 1]}")


class TestEmbeddingBugScenarios:
    """Additional tests using the bug scenario fixtures."""

    @pytest.fixture
    def mock_client(self):
        return GoogleEmbeddingClient(api_key="test-key")

    @patch('requests.post')
    def test_empty_documents_scenario(self, mock_post, mock_client, embedding_bug_scenario_data):
        """Test embedding client with empty documents."""
        # Mock API returns error for empty content
        error_response = Mock()
        error_response.status_code = 400
        error_response.text = "Empty content not allowed"
        mock_post.return_value = error_response
        
        empty_docs = embedding_bug_scenario_data["empty_documents"]
        texts = [doc["content"] for doc in empty_docs]
        
        result = mock_client.call(
            api_kwargs={"texts": texts, "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        # All should result in empty vectors due to API errors
        assert len(result.data) == len(texts)
        for embedding in result.data:
            assert len(embedding.embedding) == 0
        
        logger.error(f"EMPTY DOCUMENTS BUG: {len(texts)} empty vectors created for empty/whitespace content")

    @patch('requests.post')
    def test_encoding_problematic_scenario(self, mock_post, mock_client, embedding_bug_scenario_data):
        """Test embedding client with problematic encoding."""
        # Mock mixed responses - some succeed, some fail
        responses = []
        for i in range(2):  # 2 documents with encoding issues
            if i == 0:  # First fails
                fail_resp = Mock()
                fail_resp.status_code = 400
                fail_resp.text = "Invalid encoding"
                responses.append(fail_resp)
            else:  # Second succeeds
                success_resp = Mock()
                success_resp.status_code = 200
                success_resp.json.return_value = {"embedding": {"values": [0.1] * 768}}
                responses.append(success_resp)
        
        # First call is batch (fails), then individual calls
        batch_fail = Mock()
        batch_fail.status_code = 400
        batch_fail.text = "Batch encoding error"
        mock_post.side_effect = [batch_fail] + responses
        
        encoding_docs = embedding_bug_scenario_data["encoding_problematic"] 
        texts = [doc["content"] for doc in encoding_docs]
        
        result = mock_client.call(
            api_kwargs={"texts": texts, "model": "text-embedding-004"},
            model_type=ModelType.EMBEDDER
        )
        
        assert len(result.data) == 2
        # First should be empty due to encoding error
        assert len(result.data[0].embedding) == 0
        # Second should have valid embedding
        assert len(result.data[1].embedding) == 768
        
        logger.error(f"ENCODING BUG: Mixed results - 1 empty, 1 valid embedding")

    def test_vector_dimension_validation(self, vector_dimension_mismatch_scenarios, vector_validator):
        """Test vector dimension validation scenarios."""
        scenarios = vector_dimension_mismatch_scenarios
        
        for vector in scenarios["mixed_dimensions"]:
            is_valid_dim = vector_validator["is_valid_dimension"](vector, 768)
            has_valid_values = vector_validator["has_valid_values"](vector)
            
            logger.info(f"Vector dim={len(vector)}, valid_dim={is_valid_dim}, valid_values={has_valid_values}")
            
            if not is_valid_dim:
                logger.error(f"DIMENSION BUG: Vector with {len(vector)} dimensions instead of 768")


# Additional utility functions for debugging

def analyze_embedding_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze embedding response for potential issues."""
    analysis = {
        "has_embeddings_key": "embeddings" in response_data,
        "has_embedding_key": "embedding" in response_data,
        "embedding_count": 0,
        "dimension_issues": [],
        "value_issues": []
    }
    
    if "embeddings" in response_data:
        embeddings = response_data["embeddings"]
        analysis["embedding_count"] = len(embeddings)
        
        for i, emb in enumerate(embeddings):
            if "values" in emb:
                values = emb["values"]
                if len(values) != 768:
                    analysis["dimension_issues"].append(f"Index {i}: {len(values)} dims")
                if not all(isinstance(v, (int, float)) for v in values):
                    analysis["value_issues"].append(f"Index {i}: Invalid value types")
    
    elif "embedding" in response_data:
        emb = response_data["embedding"]
        if "values" in emb:
            values = emb["values"] 
            analysis["embedding_count"] = 1
            if len(values) != 768:
                analysis["dimension_issues"].append(f"Single embedding: {len(values)} dims")
    
    return analysis


def log_empty_vector_conditions(client_instance: GoogleEmbeddingClient, texts: List[str], result: Any):
    """Log conditions that lead to empty vectors."""
    empty_count = sum(1 for emb in result.data if len(emb.embedding) == 0)
    valid_count = len(result.data) - empty_count
    
    logger.error(f"EMPTY VECTOR ANALYSIS:")
    logger.error(f"  Input texts: {len(texts)}")
    logger.error(f"  Valid embeddings: {valid_count}")
    logger.error(f"  Empty embeddings: {empty_count}")
    logger.error(f"  Error message: {result.error}")
    logger.error(f"  Text samples: {texts[:3]}")
    
    if empty_count > 0:
        empty_indices = [i for i, emb in enumerate(result.data) if len(emb.embedding) == 0]
        logger.error(f"  Empty at indices: {empty_indices}")