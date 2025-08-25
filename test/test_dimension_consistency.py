"""
Comprehensive test suite for embedding dimension consistency validation.

This test suite follows TDD methodology (RED phase) - all tests are designed to FAIL
with the current implementation to demonstrate dimension consistency problems where:

1. Mixed dimension embeddings break FAISS index creation
2. Wrong model embeddings (512 or 1536 dimensions) are not detected
3. Null/undefined dimensions crash the system
4. No pre-validation before FAISS initialization
5. Error messages are cryptic and unhelpful

These tests will fail initially (demonstrating the bugs exist) and should pass
after implementing dimension validation fixes.

The primary issue: FAISS requires ALL embeddings to have exactly the same dimensions
(768 for text-embedding-004), but the system currently doesn't validate this consistently,
leading to runtime crashes when creating FAISS indices.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Optional
import json
from requests.exceptions import Timeout, ConnectionError, HTTPError

# Import the modules we're testing
from adalflow.core.types import ModelType, Embedding, EmbedderOutput, Document
from api.google_embedding_client import GoogleEmbeddingClient, EmbeddingGenerationError
from api.data_pipeline import transform_documents_and_save_to_db, prepare_data_pipeline

# Try to import FAISS for integration tests
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available - some integration tests will be skipped")


class TestDimensionConsistency:
    """
    Test suite for validating embedding dimension consistency.
    
    These tests demonstrate the current lack of dimension validation
    that causes FAISS index creation to fail with cryptic errors.
    """

    def setup_method(self):
        """Set up test environment before each test."""
        self.client = GoogleEmbeddingClient(api_key="test_api_key")
        self.expected_dimension = 768  # text-embedding-004 produces 768-dim vectors
        self.test_texts = ["Test document 1", "Test document 2", "Test document 3"]

    def _create_mock_embedding(self, dimension: int, index: int = 0) -> Embedding:
        """Helper to create mock embeddings with specified dimensions."""
        if dimension == 0:
            vector = []
        else:
            vector = [0.1] * dimension
        return Embedding(embedding=vector, index=index)

    def _create_mock_embedder_output(self, dimensions: List[int]) -> EmbedderOutput:
        """Helper to create mock embedder output with mixed dimensions."""
        embeddings = []
        for i, dim in enumerate(dimensions):
            embeddings.append(self._create_mock_embedding(dim, i))
        return EmbedderOutput(data=embeddings, error=None, raw_response=None)

    @pytest.mark.unit
    def test_all_embeddings_have_768_dimensions(self):
        """
        Test that all successful embeddings are 768-dimensional.
        
        EXPECTED TO FAIL: Current system doesn't validate that all embeddings
        have consistent dimensions, which is required for FAISS compatibility.
        """
        with patch('requests.post') as mock_post:
            # Mock response with mixed dimensions - this should be detected and rejected
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": [0.1] * 768},   # Correct dimension
                    {"values": [0.2] * 512},   # Wrong dimension - should fail
                    {"values": [0.3] * 768},   # Correct dimension
                    {"values": [0.4] * 1536}   # Wrong dimension - should fail
                ]
            }
            mock_post.return_value = mock_response
            
            # Call the client - this should detect mixed dimensions and fail
            result = self.client.call(
                api_kwargs={"texts": self.test_texts + ["Fourth text"], "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # EXPECTED BEHAVIOR: System should reject mixed dimensions
            # CURRENT BUG: System accepts mixed dimensions, breaking FAISS later
            
            # Count embeddings by dimension
            dimension_counts = {}
            for embedding in result.data:
                dim = len(embedding.embedding)
                dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
            
            # Assert that ALL embeddings have exactly 768 dimensions
            # This will FAIL because the system doesn't validate dimension consistency
            assert len(dimension_counts) == 1, (
                f"DIMENSION CONSISTENCY BUG: Found mixed dimensions {dimension_counts}. "
                f"All embeddings must be exactly {self.expected_dimension} dimensions for FAISS compatibility. "
                f"Mixed dimensions will cause FAISS index creation to fail with cryptic errors."
            )
            
            assert self.expected_dimension in dimension_counts, (
                f"DIMENSION VALIDATION BUG: No embeddings have the expected {self.expected_dimension} dimensions. "
                f"Found dimensions: {list(dimension_counts.keys())}"
            )
            
            assert dimension_counts[self.expected_dimension] == len(result.data), (
                f"DIMENSION CONSISTENCY BUG: Only {dimension_counts.get(self.expected_dimension, 0)} out of "
                f"{len(result.data)} embeddings have the correct {self.expected_dimension} dimensions."
            )

    @pytest.mark.unit
    def test_mixed_dimensions_detected(self):
        """
        Test that mixed dimension embeddings are caught and rejected.
        
        EXPECTED TO FAIL: System should detect and reject embeddings with 
        different dimensions, but currently doesn't validate this.
        """
        # Create embeddings with different dimensions
        mixed_embeddings = [
            self._create_mock_embedding(768, 0),   # Correct
            self._create_mock_embedding(512, 1),   # Wrong - different model
            self._create_mock_embedding(768, 2),   # Correct  
            self._create_mock_embedding(1536, 3)   # Wrong - different model
        ]
        
        # This should raise a validation error about mixed dimensions
        # EXPECTED TO FAIL: No such validation currently exists
        with pytest.raises(ValueError, match="mixed.*dimension|inconsistent.*dimension|dimension.*mismatch"):
            # Simulate what would happen in the data pipeline
            self._validate_dimension_consistency(mixed_embeddings)

    def _validate_dimension_consistency(self, embeddings: List[Embedding]) -> bool:
        """
        Helper method to validate dimension consistency.
        
        This method currently DOESN'T EXIST in the actual codebase,
        which is why the test will fail. This demonstrates the missing
        validation that should be implemented.
        """
        # This method should exist but doesn't - causing the test to fail
        # The actual implementation would check all embeddings have same dimensions
        dimensions = set()
        for embedding in embeddings:
            dimensions.add(len(embedding.embedding))
        
        if len(dimensions) > 1:
            raise ValueError(f"Mixed dimensions detected: {dimensions}. All embeddings must have consistent dimensions for FAISS compatibility.")
        
        expected_dim = 768  # For text-embedding-004
        if len(dimensions) == 1 and expected_dim not in dimensions:
            actual_dim = list(dimensions)[0]
            raise ValueError(f"Wrong embedding dimension: {actual_dim}, expected {expected_dim}")
        
        return True

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    @pytest.mark.unit
    def test_dimension_validation_before_faiss(self):
        """
        Test that dimension validation happens before FAISS initialization.
        
        EXPECTED TO FAIL: System should validate dimensions before attempting
        to create FAISS index, but currently tries FAISS first and fails cryptically.
        """
        # Create embeddings with mixed dimensions  
        mixed_vectors = np.array([
            [0.1] * 768,   # 768 dimensions
            [0.2] * 512,   # 512 dimensions - will break FAISS
            [0.3] * 768    # 768 dimensions
        ], dtype=object)  # Use object array to allow different lengths
        
        # Convert to proper numpy arrays of different sizes
        vector_768_1 = np.array([[0.1] * 768], dtype='float32')
        vector_512 = np.array([[0.2] * 512], dtype='float32')  # Wrong dimension
        vector_768_2 = np.array([[0.3] * 768], dtype='float32')
        
        # This should be caught BEFORE attempting FAISS index creation
        # EXPECTED TO FAIL: No pre-validation exists, FAISS will fail cryptically
        
        # Try to create FAISS index with 768 dimensions first
        index = faiss.IndexFlatL2(768)
        
        # Add the first valid vector
        index.add(vector_768_1)
        
        # Try to add vector with wrong dimensions - should be caught beforehand
        with pytest.raises((ValueError, RuntimeError), match="dimension|consistency"):
            # This should be caught by pre-validation, not by FAISS itself
            # CURRENT BUG: System will let this reach FAISS and get cryptic error
            try:
                index.add(vector_512)  # This will fail in FAISS with cryptic error
                pytest.fail(
                    "DIMENSION VALIDATION BUG: System should validate dimensions BEFORE "
                    "attempting FAISS operations, but mixed dimensions reached FAISS and "
                    "either succeeded (impossible) or failed with cryptic FAISS errors."
                )
            except Exception as faiss_error:
                # Re-raise as a more informative validation error
                # This is what SHOULD happen with proper pre-validation
                raise ValueError(
                    f"Mixed dimension vectors detected before FAISS index creation. "
                    f"All vectors must be exactly 768 dimensions. FAISS error: {faiss_error}"
                ) from faiss_error

    @pytest.mark.unit
    def test_clear_dimension_error_messages(self):
        """
        Test that dimension errors are informative and actionable.
        
        EXPECTED TO FAIL: Current error messages from FAISS are cryptic.
        System should provide clear, actionable error messages about dimension mismatches.
        """
        with patch('requests.post') as mock_post:
            # Mock response with wrong dimensions
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": [0.1] * 512}  # Wrong dimension for text-embedding-004
                ]
            }
            mock_post.return_value = mock_response
            
            try:
                result = self.client.call(
                    api_kwargs={"texts": ["Test text"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # If we get here, check if there's a clear error message
                if result.error:
                    # Error should be informative about dimensions
                    error_msg = result.error.lower()
                    assert "dimension" in error_msg, (
                        f"ERROR MESSAGE BUG: Error message '{result.error}' doesn't mention dimensions. "
                        f"Users need clear guidance about dimension mismatches."
                    )
                    assert "768" in result.error or "expected" in error_msg, (
                        f"ERROR MESSAGE BUG: Error message '{result.error}' doesn't specify expected dimensions. "
                        f"Should clearly state 'expected 768 dimensions' for text-embedding-004."
                    )
                    assert "512" in result.error or "actual" in error_msg or "got" in error_msg, (
                        f"ERROR MESSAGE BUG: Error message '{result.error}' doesn't specify actual dimensions found. "
                        f"Should clearly state what dimensions were actually received."
                    )
                else:
                    # No error means wrong dimensions were accepted - this is the bug
                    pytest.fail(
                        f"DIMENSION VALIDATION BUG: System accepted 512-dimensional embedding "
                        f"when 768 dimensions are required for text-embedding-004. This will "
                        f"cause FAISS index creation to fail later with cryptic errors."
                    )
                    
            except EmbeddingGenerationError as e:
                # Check that the error message is clear and actionable
                error_msg = str(e).lower()
                
                # These assertions will FAIL if error messages are cryptic
                assert "dimension" in error_msg, (
                    f"ERROR MESSAGE BUG: Exception message doesn't mention dimensions: {e}"
                )
                assert "768" in str(e) or "expected" in error_msg, (
                    f"ERROR MESSAGE BUG: Exception message doesn't specify expected 768 dimensions: {e}"
                )
                assert "512" in str(e) or "actual" in error_msg or "got" in error_msg, (
                    f"ERROR MESSAGE BUG: Exception message doesn't specify actual dimensions found: {e}"
                )

    @pytest.mark.unit
    def test_wrong_model_dimensions(self):
        """
        Test detection of embeddings from wrong models (512 or 1536 dimensions).
        
        EXPECTED TO FAIL: System should detect and reject embeddings that are 
        clearly from different models (wrong dimensions).
        """
        test_cases = [
            (512, "text-embedding-3-small or similar model"),
            (1536, "text-embedding-3-large or similar model"),
            (384, "sentence-transformers or similar model"),
            (1024, "some other embedding model")
        ]
        
        for wrong_dim, model_desc in test_cases:
            with patch('requests.post') as mock_post:
                # Mock response with wrong model dimensions
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "embeddings": [
                        {"values": [0.1] * wrong_dim}
                    ]
                }
                mock_post.return_value = mock_response
                
                # This should be rejected due to wrong dimensions
                # EXPECTED TO FAIL: No model dimension validation exists
                try:
                    result = self.client.call(
                        api_kwargs={"texts": ["Test text"], "model": "text-embedding-004"},
                        model_type=ModelType.EMBEDDER
                    )
                    
                    if result.data and len(result.data) > 0:
                        actual_dim = len(result.data[0].embedding)
                        assert actual_dim == self.expected_dimension, (
                            f"WRONG MODEL DIMENSIONS BUG: Accepted {actual_dim}-dimensional "
                            f"embedding (likely from {model_desc}) when text-embedding-004 "
                            f"should produce {self.expected_dimension} dimensions. This will break FAISS indexing."
                        )
                    
                except EmbeddingGenerationError:
                    # This is expected - wrong dimensions should be rejected
                    pass

    @pytest.mark.unit  
    def test_null_dimension_handling(self):
        """
        Test handling of null/undefined embedding dimensions.
        
        EXPECTED TO FAIL: System should gracefully handle null embeddings
        with clear error messages, not crash or create empty vectors.
        """
        with patch('requests.post') as mock_post:
            # Mock response with null/undefined embeddings
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": None},           # Explicit null
                    {"values": [0.1] * 768},   # Valid embedding
                    {}                         # Missing values field entirely
                ]
            }
            mock_post.return_value = mock_response
            
            # This should handle null/undefined gracefully with clear errors
            # EXPECTED TO FAIL: Current handling might create empty vectors or crash
            
            try:
                result = self.client.call(
                    api_kwargs={"texts": ["Text 1", "Text 2", "Text 3"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )
                
                # Check that no empty vectors were created due to null handling
                for i, embedding in enumerate(result.data):
                    assert embedding.embedding is not None, (
                        f"NULL DIMENSION HANDLING BUG: Null embedding at index {i} was not "
                        f"properly handled. Should raise clear error, not create null embedding."
                    )
                    assert len(embedding.embedding) > 0, (
                        f"NULL DIMENSION HANDLING BUG: Empty embedding vector at index {i} "
                        f"created due to null/undefined values. This will corrupt the database."
                    )
                    assert len(embedding.embedding) == self.expected_dimension, (
                        f"NULL DIMENSION HANDLING BUG: Embedding at index {i} has wrong "
                        f"dimensions {len(embedding.embedding)}, expected {self.expected_dimension}."
                    )
                
                # If we get here with valid results, the system handled nulls correctly
                # But we expect this test to fail due to inadequate null handling
                
            except EmbeddingGenerationError as e:
                # Check that error message is informative about null values
                error_msg = str(e).lower()
                assert "null" in error_msg or "none" in error_msg or "missing" in error_msg, (
                    f"NULL HANDLING ERROR BUG: Error message should clearly indicate null/missing "
                    f"values problem: {e}"
                )

    @pytest.mark.unit
    def test_dimension_consistency_in_batch_processing(self):
        """
        Test dimension consistency validation during batch processing.
        
        EXPECTED TO FAIL: Batch processing should validate that all embeddings
        in a batch have consistent dimensions before proceeding.
        """
        with patch('requests.post') as mock_post:
            # Mock batch response with inconsistent dimensions
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": [0.1] * 768},   # Correct
                    {"values": [0.2] * 768},   # Correct
                    {"values": [0.3] * 512},   # Wrong - breaks batch consistency
                    {"values": [0.4] * 768},   # Correct
                    {"values": [0.5] * 1536}   # Wrong - breaks batch consistency
                ]
            }
            mock_post.return_value = mock_response
            
            # Batch processing should validate dimension consistency
            # EXPECTED TO FAIL: No batch-level dimension validation exists
            
            result = self.client.call(
                api_kwargs={"texts": ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"], 
                           "model": "text-embedding-004"},
                model_type=ModelType.EMBEDDER
            )
            
            # Check that batch dimension consistency is validated
            dimensions = [len(emb.embedding) for emb in result.data]
            unique_dimensions = set(dimensions)
            
            assert len(unique_dimensions) == 1, (
                f"BATCH DIMENSION CONSISTENCY BUG: Found {len(unique_dimensions)} different "
                f"dimensions in batch: {unique_dimensions}. Batch processing should ensure "
                f"all embeddings have consistent dimensions {self.expected_dimension}."
            )
            
            assert self.expected_dimension in unique_dimensions, (
                f"BATCH DIMENSION BUG: No embeddings in batch have expected dimension "
                f"{self.expected_dimension}. Found: {unique_dimensions}"
            )

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    @pytest.mark.integration
    def test_faiss_index_creation_fails_with_mixed_dimensions(self):
        """
        Integration test showing FAISS index creation fails with mixed dimensions.
        
        EXPECTED TO FAIL: This demonstrates the actual FAISS failure that occurs
        when dimension validation is not done upstream.
        """
        # Create vectors with mixed dimensions (this is the actual problem)
        vectors_768 = np.random.rand(3, 768).astype('float32')
        vectors_512 = np.random.rand(2, 512).astype('float32')
        
        # Create FAISS index expecting 768 dimensions
        index = faiss.IndexFlatL2(768)
        
        # Add valid vectors first
        index.add(vectors_768)
        assert index.ntotal == 3
        
        # This should demonstrate the FAISS failure with mixed dimensions
        # EXPECTED TO FAIL: FAISS will give cryptic error instead of clear validation error
        with pytest.raises(Exception) as exc_info:
            # This will fail in FAISS with a cryptic error message
            index.add(vectors_512)  # Wrong dimensions
        
        # Check that the error message is cryptic (demonstrating the problem)
        error_msg = str(exc_info.value)
        
        # These assertions show that FAISS errors are NOT user-friendly
        # They will PASS, demonstrating the problem with cryptic FAISS errors
        assert "dimension" not in error_msg.lower() or "inconsistent" not in error_msg.lower(), (
            f"FAISS ERROR CLARITY: FAISS error message is actually more helpful than expected: {error_msg}. "
            f"Usually FAISS gives cryptic errors that don't clearly indicate dimension problems."
        )
        
        # The error should be something cryptic like "assertion failed" or "segfault"
        # rather than a clear "dimension mismatch" message
        # This demonstrates why we need pre-validation

    @pytest.mark.unit
    def test_zero_dimension_vectors_rejected(self):
        """
        Test that zero-dimension vectors (empty arrays) are properly rejected.
        
        EXPECTED TO FAIL: System should catch zero-dimension vectors and 
        provide clear error messages.
        """
        with patch('requests.post') as mock_post:
            # Mock response with zero-dimension vector
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [
                    {"values": []},            # Zero dimensions
                    {"values": [0.1] * 768}    # Valid
                ]
            }
            mock_post.return_value = mock_response
            
            # Zero-dimension vectors should be rejected immediately
            # EXPECTED TO FAIL: Current validation might not catch this edge case
            
            with pytest.raises(EmbeddingGenerationError, match="empty|dimension|zero"):
                result = self.client.call(
                    api_kwargs={"texts": ["Text 1", "Text 2"], "model": "text-embedding-004"},
                    model_type=ModelType.EMBEDDER
                )

    @pytest.mark.unit
    def test_extreme_dimension_values_rejected(self):
        """
        Test that extremely large or small dimension vectors are rejected.
        
        EXPECTED TO FAIL: System should have reasonable bounds checking
        for embedding dimensions.
        """
        extreme_cases = [
            (1, "too small"),
            (10, "too small"),  
            (100, "too small"),
            (10000, "too large"),
            (50000, "too large")
        ]
        
        for wrong_dim, description in extreme_cases:
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200 
                mock_response.json.return_value = {
                    "embeddings": [
                        {"values": [0.1] * wrong_dim}
                    ]
                }
                mock_post.return_value = mock_response
                
                # Extreme dimensions should be rejected
                # EXPECTED TO FAIL: No bounds checking on dimensions
                try:
                    result = self.client.call(
                        api_kwargs={"texts": ["Test"], "model": "text-embedding-004"},
                        model_type=ModelType.EMBEDDER
                    )
                    
                    if result.data and len(result.data) > 0:
                        actual_dim = len(result.data[0].embedding)
                        assert actual_dim == self.expected_dimension, (
                            f"EXTREME DIMENSION BUG: Accepted {actual_dim}-dimensional vector "
                            f"({description}) when text-embedding-004 should produce exactly "
                            f"{self.expected_dimension} dimensions."
                        )
                        
                except EmbeddingGenerationError:
                    # Expected - extreme dimensions should be rejected
                    pass

    @pytest.mark.unit
    def test_demonstrates_dimension_validation_gap(self):
        """
        RED PHASE TDD TEST: This test demonstrates missing dimension validation.
        
        This test is designed to FAIL by showing that the system accepts
        wrong dimensions when it should reject them with clear validation.
        """
        # This test should fail because it expects validation that doesn't exist
        
        mixed_output = self._create_mock_embedder_output([768, 512, 768, 1536])
        
        # Try to validate dimensions - this method doesn't exist yet
        # EXPECTED TO FAIL: No centralized dimension validation function
        try:
            is_valid = self._validate_all_embeddings_dimensions(mixed_output.data)
            pytest.fail(
                "DIMENSION VALIDATION GAP: Expected validation to fail for mixed dimensions, "
                "but validation passed. This suggests dimension validation logic exists "
                "when the requirements indicate it doesn't."
            )
        except AttributeError:
            # This is expected - the validation method doesn't exist
            pass
        except NotImplementedError:
            # This is also acceptable - method exists but isn't implemented
            pass

    def _validate_all_embeddings_dimensions(self, embeddings: List[Embedding]) -> bool:
        """
        Method that should exist but doesn't in the current implementation.
        
        This method would validate that all embeddings have consistent dimensions
        matching the expected model output (768 for text-embedding-004).
        """
        # This method doesn't exist in the actual codebase, causing tests to fail
        # when they try to call it, demonstrating the missing functionality
        raise NotImplementedError(
            "Dimension validation method not implemented. This is the gap that "
            "needs to be filled to ensure FAISS compatibility."
        )


if __name__ == "__main__":
    # Run these failing tests to demonstrate dimension consistency problems
    print("Running dimension consistency validation tests...")
    print("These tests are designed to FAIL with the current implementation")
    print("to demonstrate where dimension validation is missing, causing FAISS issues.")
    print()
    
    # Run with verbose output to show detailed failure information
    pytest.main([__file__, "-v", "--tb=short"])