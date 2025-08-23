"""
Test to validate that all fixtures work correctly together.

This comprehensive test ensures that all fixtures in conftest.py and fixture modules
function properly and can be used together in realistic test scenarios.
"""

import pytest
import pytest_asyncio
import numpy as np
from typing import Dict, List, Any
from httpx import AsyncClient

# Import fixture modules
from api.tests.fixtures.embedding_bug_scenarios import *


@pytest.mark.asyncio
class TestFixtureValidation:
    """Comprehensive fixture validation tests."""
    
    async def test_async_clients_work(self, async_client: AsyncClient, authenticated_async_client: AsyncClient):
        """Test that async client fixtures are properly configured."""
        assert async_client is not None
        assert authenticated_async_client is not None
        assert async_client.base_url == "http://test"
        assert async_client.timeout.read == 30.0
    
    def test_document_fixtures(self, sample_document: Dict, sample_documents: List[Dict], edge_case_documents: Dict):
        """Test that document fixtures provide correct data structures."""
        # Test single document fixture
        assert "content" in sample_document
        assert "metadata" in sample_document
        assert "chunks" in sample_document
        assert len(sample_document["content"]) > 0
        assert sample_document["metadata"]["title"] == "Sample Document"
        
        # Test multiple documents fixture
        assert len(sample_documents) == 3
        for doc in sample_documents:
            assert "content" in doc
            assert "metadata" in doc
            assert len(doc["content"]) > 0
        
        # Test edge case documents
        assert "empty" in edge_case_documents
        assert "unicode" in edge_case_documents
        assert "very_long" in edge_case_documents
        assert edge_case_documents["empty"]["content"] == ""
        assert len(edge_case_documents["very_long"]["content"]) > 10000
    
    def test_document_chunks_fixture(self, document_chunks: Dict):
        """Test that document chunks fixture provides proper chunk data."""
        assert "normal_chunks" in document_chunks
        assert "overlapping_chunks" in document_chunks
        assert "varying_sizes" in document_chunks
        
        # Validate chunk structure
        for chunk_type, chunks in document_chunks.items():
            assert isinstance(chunks, list)
            assert len(chunks) > 0
            for chunk in chunks:
                assert isinstance(chunk, str)
                assert len(chunk) > 0
    
    def test_embedding_vector_fixtures(self, sample_embedding_vector: List[float], batch_embedding_vectors: List[List[float]]):
        """Test that embedding vector fixtures provide correct dimensions and data."""
        # Test single vector
        assert len(sample_embedding_vector) == 768
        assert all(isinstance(v, float) for v in sample_embedding_vector)
        assert not any(np.isnan(v) or np.isinf(v) for v in sample_embedding_vector)
        
        # Test batch vectors
        assert len(batch_embedding_vectors) == 5
        for vector in batch_embedding_vectors:
            assert len(vector) == 768
            assert all(isinstance(v, float) for v in vector)
            assert not any(np.isnan(v) or np.isinf(v) for v in vector)
    
    def test_invalid_embedding_vectors_fixture(self, invalid_embedding_vectors: Dict):
        """Test that invalid embedding vectors fixture provides various error cases."""
        assert "empty" in invalid_embedding_vectors
        assert "wrong_dimension" in invalid_embedding_vectors
        assert "contains_nan" in invalid_embedding_vectors
        assert "contains_inf" in invalid_embedding_vectors
        
        # Validate specific invalid cases
        assert len(invalid_embedding_vectors["empty"]) == 0
        assert len(invalid_embedding_vectors["wrong_dimension"]) != 768
        assert np.isnan(invalid_embedding_vectors["contains_nan"][-1])
        assert np.isinf(invalid_embedding_vectors["contains_inf"][-1])
    
    def test_vector_validator_fixture(self, vector_validator: Dict, sample_embedding_vector: List[float]):
        """Test that vector validation utilities work correctly."""
        assert "is_valid_dimension" in vector_validator
        assert "is_normalized" in vector_validator
        assert "has_valid_values" in vector_validator
        assert "cosine_similarity" in vector_validator
        
        # Test validation functions
        assert vector_validator["is_valid_dimension"](sample_embedding_vector, 768)
        assert not vector_validator["is_valid_dimension"](sample_embedding_vector, 512)
        assert vector_validator["has_valid_values"](sample_embedding_vector)
        
        # Test cosine similarity
        similarity = vector_validator["cosine_similarity"](sample_embedding_vector, sample_embedding_vector)
        assert abs(similarity - 1.0) < 1e-6  # Self-similarity should be 1
    
    def test_mock_clients(self, mock_google_embedding_client, mock_embedding_service):
        """Test that mock clients provide expected interfaces."""
        assert mock_google_embedding_client is not None
        assert mock_embedding_service is not None
        
        # Test mock client response
        response = mock_google_embedding_client.call()
        assert response.status_code == 200
        assert "embedding" in response.json.return_value
        assert "values" in response.json.return_value["embedding"]
    
    def test_embedding_response_mocks(self, embedding_response_mock: Dict, batch_embedding_response_mock: Dict):
        """Test that embedding response mocks have correct structure."""
        assert "embedding" in embedding_response_mock
        assert "values" in embedding_response_mock["embedding"]
        assert len(embedding_response_mock["embedding"]["values"]) == 768
        
        assert "embeddings" in batch_embedding_response_mock
        assert len(batch_embedding_response_mock["embeddings"]) == 3
        for embedding in batch_embedding_response_mock["embeddings"]:
            assert "values" in embedding
            assert len(embedding["values"]) == 768
    
    def test_test_data_generator(self, test_data_generator: Dict):
        """Test that data generator utilities work correctly."""
        assert "generate_documents" in test_data_generator
        assert "generate_embedding_vectors" in test_data_generator
        assert "generate_chunks" in test_data_generator
        
        # Test document generation
        docs = test_data_generator["generate_documents"](3)
        assert len(docs) == 3
        for i, doc in enumerate(docs):
            assert f"Document {i}" in doc["content"]
            assert doc["metadata"]["id"] == f"doc{i}"
        
        # Test vector generation
        vectors = test_data_generator["generate_embedding_vectors"](2, 512)
        assert len(vectors) == 2
        for vector in vectors:
            assert len(vector) == 512
        
        # Test chunk generation
        chunks = test_data_generator["generate_chunks"]("This is a test document.", 10, 2)
        assert len(chunks) > 1
        assert all(len(chunk) <= 10 for chunk in chunks)
    
    def test_wiki_fixtures_compatibility(self, sample_wiki_page: Dict, sample_wiki_structure: Dict, sample_repo_info: Dict):
        """Test that existing wiki fixtures still work with new fixtures."""
        assert "id" in sample_wiki_page
        assert "title" in sample_wiki_page
        assert "content" in sample_wiki_page
        
        assert "pages" in sample_wiki_structure
        assert sample_wiki_structure["pages"][0]["id"] == sample_wiki_page["id"]
        
        assert "owner" in sample_repo_info
        assert "repo" in sample_repo_info


@pytest.mark.asyncio 
class TestEmbeddingBugFixtures:
    """Test embedding bug-specific fixtures."""
    
    def test_embedding_bug_scenario_data(self, embedding_bug_scenario_data: Dict):
        """Test that embedding bug scenarios provide comprehensive test data."""
        assert "empty_documents" in embedding_bug_scenario_data
        assert "encoding_problematic" in embedding_bug_scenario_data
        assert "large_batch" in embedding_bug_scenario_data
        assert "token_limit_exceeded" in embedding_bug_scenario_data
        assert "concurrent_batches" in embedding_bug_scenario_data
        
        # Validate specific scenarios
        empty_docs = embedding_bug_scenario_data["empty_documents"]
        assert len(empty_docs) >= 3
        assert any(doc["content"] == "" for doc in empty_docs)
        
        large_batch = embedding_bug_scenario_data["large_batch"]
        assert len(large_batch) == 100
        
        concurrent = embedding_bug_scenario_data["concurrent_batches"]
        assert "batch_1" in concurrent
        assert "batch_2" in concurrent
        assert "batch_3" in concurrent
    
    def test_embedding_api_failure_scenarios(self, embedding_api_failure_scenarios: Dict):
        """Test that API failure scenarios cover common error cases."""
        assert "rate_limit" in embedding_api_failure_scenarios
        assert "quota_exceeded" in embedding_api_failure_scenarios
        assert "timeout" in embedding_api_failure_scenarios
        assert "invalid_request" in embedding_api_failure_scenarios
        
        # Validate response structures
        rate_limit = embedding_api_failure_scenarios["rate_limit"]
        assert rate_limit.status_code == 429
        assert "error" in rate_limit.json.return_value
    
    def test_malformed_embedding_responses(self, malformed_embedding_responses: Dict):
        """Test that malformed response fixtures cover parsing edge cases."""
        assert "missing_values" in malformed_embedding_responses
        assert "wrong_structure" in malformed_embedding_responses
        assert "invalid_dimensions" in malformed_embedding_responses
        assert "mixed_types" in malformed_embedding_responses
        
        # Validate specific malformations
        missing_values = malformed_embedding_responses["missing_values"]
        assert "embedding" in missing_values
        assert "values" not in missing_values["embedding"]
        
        invalid_dims = malformed_embedding_responses["invalid_dimensions"]
        assert len(invalid_dims["embedding"]["values"]) == 512  # Wrong dimension
    
    def test_batch_processing_edge_cases(self, batch_processing_edge_cases: Dict):
        """Test that batch processing edge cases are comprehensive."""
        assert "mixed_lengths" in batch_processing_edge_cases
        assert "duplicates" in batch_processing_edge_cases
        assert "exact_limit_batch" in batch_processing_edge_cases
        assert "single_item" in batch_processing_edge_cases
        
        # Validate edge cases
        mixed_lengths = batch_processing_edge_cases["mixed_lengths"]
        lengths = [len(doc["content"]) for doc in mixed_lengths]
        assert min(lengths) < 20  # Short document
        assert max(lengths) > 1000  # Long document
        
        exact_limit = batch_processing_edge_cases["exact_limit_batch"]
        assert len(exact_limit) == 500  # Exact batch size limit
        
        single_item = batch_processing_edge_cases["single_item"]
        assert len(single_item) == 1
    
    def test_vector_dimension_mismatch_scenarios(self, vector_dimension_mismatch_scenarios: Dict):
        """Test that dimension mismatch scenarios cover various error cases."""
        assert "text_embedding_004" in vector_dimension_mismatch_scenarios
        assert "mixed_dimensions" in vector_dimension_mismatch_scenarios
        assert "zero_dimension" in vector_dimension_mismatch_scenarios
        
        # Validate dimension scenarios
        te004 = vector_dimension_mismatch_scenarios["text_embedding_004"]
        assert te004["expected_dim"] == 768
        assert len(te004["actual_vectors"]) >= 3
        
        mixed_dims = vector_dimension_mismatch_scenarios["mixed_dimensions"]
        dimensions = [len(vector) for vector in mixed_dims]
        assert len(set(dimensions)) > 1  # Multiple different dimensions
        
        zero_dim = vector_dimension_mismatch_scenarios["zero_dimension"]
        assert len(zero_dim) == 0
    
    def test_memory_pressure_scenarios(self, memory_pressure_scenarios: Dict):
        """Test that memory pressure scenarios provide stress testing data."""
        assert "large_documents" in memory_pressure_scenarios
        assert "many_small_documents" in memory_pressure_scenarios
        assert "mixed_size_stress_test" in memory_pressure_scenarios
        
        # Validate memory pressure scenarios
        large_docs = memory_pressure_scenarios["large_documents"]
        assert len(large_docs) >= 20
        assert all(len(doc["content"]) > 100000 for doc in large_docs)  # Large documents
        
        small_docs = memory_pressure_scenarios["many_small_documents"]
        assert len(small_docs) >= 10000  # Many documents
        
        mixed_test = memory_pressure_scenarios["mixed_size_stress_test"]
        assert len(mixed_test) > 1000  # Large number of mixed documents
    
    def test_embedding_validation_scenarios(self, embedding_validation_scenarios: Dict):
        """Test that embedding validation scenarios provide comprehensive validation data."""
        assert "valid_embeddings" in embedding_validation_scenarios
        assert "invalid_embeddings" in embedding_validation_scenarios
        assert "mixed_batch" in embedding_validation_scenarios
        
        # Validate validation scenarios
        valid = embedding_validation_scenarios["valid_embeddings"]
        assert len(valid) == 10
        for vector in valid:
            assert len(vector) == 768
            assert not any(np.isnan(v) or np.isinf(v) for v in vector)
        
        invalid = embedding_validation_scenarios["invalid_embeddings"]
        assert "contains_nan" in invalid
        assert "contains_inf" in invalid
        assert "all_zeros" in invalid
        
        mixed = embedding_validation_scenarios["mixed_batch"]
        assert len(mixed) == 5  # Mix of valid and invalid vectors


@pytest.mark.asyncio
class TestFixtureIntegration:
    """Test that fixtures work together in realistic integration scenarios."""
    
    async def test_document_to_embedding_pipeline(
        self, 
        async_client: AsyncClient,
        sample_documents: List[Dict],
        vector_validator: Dict,
        mock_google_embedding_client
    ):
        """Test complete document processing pipeline using fixtures."""
        # This test demonstrates how fixtures work together
        # in a realistic embedding processing scenario
        
        # Use sample documents
        assert len(sample_documents) > 0
        
        # Validate each document can be processed
        for doc in sample_documents:
            assert len(doc["content"]) > 0
            assert "metadata" in doc
        
        # Use vector validator to check mock embeddings
        mock_response = mock_google_embedding_client.call()
        mock_vector = mock_response.json.return_value["embedding"]["values"]
        
        assert vector_validator["is_valid_dimension"](mock_vector, 768)
        assert vector_validator["has_valid_values"](mock_vector)
    
    def test_bug_scenario_with_validation(
        self,
        embedding_bug_scenario_data: Dict,
        vector_validator: Dict,
        malformed_embedding_responses: Dict
    ):
        """Test that bug scenarios can be validated using validation utilities."""
        # Get problematic documents
        empty_docs = embedding_bug_scenario_data["empty_documents"]
        
        # Test that validation catches malformed responses
        malformed = malformed_embedding_responses["invalid_dimensions"]
        invalid_vector = malformed["embedding"]["values"]
        
        # Validator should catch dimension mismatch
        assert not vector_validator["is_valid_dimension"](invalid_vector, 768)
        assert vector_validator["is_valid_dimension"](invalid_vector, 512)
    
    def test_comprehensive_edge_case_handling(
        self,
        edge_case_documents: Dict,
        batch_processing_edge_cases: Dict,
        test_data_generator: Dict
    ):
        """Test that edge cases from different fixtures complement each other."""
        # Combine edge case documents with batch edge cases
        all_edge_cases = []
        
        # Add document edge cases
        for key, doc in edge_case_documents.items():
            all_edge_cases.append(doc)
        
        # Add batch processing edge cases
        all_edge_cases.extend(batch_processing_edge_cases["single_item"])
        all_edge_cases.extend(batch_processing_edge_cases["mixed_lengths"])
        
        # Generate additional edge cases
        generated_docs = test_data_generator["generate_documents"](5, "Generated edge case {i}")
        all_edge_cases.extend(generated_docs)
        
        # Validate we have comprehensive coverage
        assert len(all_edge_cases) > 10
        
        # Check various content types are covered
        contents = [doc["content"] for doc in all_edge_cases]
        assert any(len(c) == 0 for c in contents)  # Empty content
        assert any(len(c) < 10 for c in contents)  # Very short content
        assert any(len(c) > 1000 for c in contents)  # Long content
        assert any("Generated" in c for c in contents)  # Generated content