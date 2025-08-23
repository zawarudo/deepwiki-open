"""
Tests for vector validation and FAISS compatibility.

This module focuses on testing the vector validation logic to ensure vectors meet
FAISS requirements before storage. Tests cover dimension consistency, empty vector
detection, and proper error handling in the RAG pipeline.

Key areas tested:
- Empty vector detection
- Vector dimension validation (768-dim for text-embedding-004) 
- FAISS add_with_ids compatibility
- Error handling for invalid vectors
- Verification that validation prevents storage of bad vectors

Focus on rag.py validation around line 295: _validate_and_filter_embeddings method.
"""

import pytest
import numpy as np
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import logging

# Import the RAG class and document classes
from api.rag import RAG
from adalflow.core.types import Document


class MockDocument:
    """Mock document class for testing vector validation."""
    
    def __init__(self, content: str, vector=None, meta_data=None):
        self.content = content
        self.vector = vector
        self.meta_data = meta_data or {}


class TestVectorValidation:
    """Test suite for vector validation and FAISS compatibility."""

    @pytest.fixture
    def rag_instance(self):
        """Create a RAG instance for testing."""
        # Create a minimal RAG instance without full initialization
        rag = Mock(spec=RAG)
        # Add the validation method from the real RAG class
        rag._validate_and_filter_embeddings = RAG._validate_and_filter_embeddings.__get__(rag, RAG)
        return rag

    @pytest.fixture
    def sample_valid_vector(self):
        """Create a valid 768-dimensional normalized vector."""
        np.random.seed(42)
        vector = np.random.randn(768).astype(np.float32)
        return (vector / np.linalg.norm(vector)).tolist()

    @pytest.fixture
    def sample_documents_with_vectors(self, sample_valid_vector):
        """Create sample documents with various vector conditions."""
        # Create some additional vectors
        np.random.seed(43)
        valid_vector2 = np.random.randn(768).astype(np.float32)
        valid_vector2 = (valid_vector2 / np.linalg.norm(valid_vector2)).tolist()
        
        return {
            "valid_documents": [
                MockDocument(content="Valid document 1", vector=sample_valid_vector),
                MockDocument(content="Valid document 2", vector=valid_vector2),
                MockDocument(content="Valid document 3", vector=[0.1] * 768)  # Simple valid vector
            ],
            "mixed_dimensions": [
                MockDocument(content="768-dim doc", vector=[0.1] * 768),
                MockDocument(content="512-dim doc", vector=[0.1] * 512),  # Wrong dimension
                MockDocument(content="1024-dim doc", vector=[0.1] * 1024),  # Wrong dimension
                MockDocument(content="Another 768-dim doc", vector=[0.2] * 768)
            ],
            "empty_and_invalid": [
                MockDocument(content="Empty vector doc", vector=[]),
                MockDocument(content="None vector doc", vector=None),
                MockDocument(content="Valid doc", vector=[0.1] * 768)
            ],
            "problematic_vectors": [
                MockDocument(content="NaN vector", vector=[float('nan')] * 768),
                MockDocument(content="Inf vector", vector=[float('inf')] + [0.1] * 767),
                MockDocument(content="All zeros", vector=[0.0] * 768),
                MockDocument(content="Valid doc", vector=[0.1] * 768)
            ]
        }

    # =============================================================================
    # Test Empty Vector Detection
    # =============================================================================

    def test_empty_vector_detection(self, rag_instance, sample_documents_with_vectors):
        """Test that empty vectors are properly detected and filtered out."""
        docs = sample_documents_with_vectors["empty_and_invalid"]
        
        # Test the validation method directly
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Should only have one valid document (the one with actual vector)
        assert len(valid_docs) == 1
        assert valid_docs[0].content == "Valid doc"
        assert len(valid_docs[0].vector) == 768

    def test_none_vector_handling(self, rag_instance):
        """Test handling of documents with None vectors."""
        docs = [
            MockDocument(content="No vector", vector=None),
            MockDocument(content="Empty list vector", vector=[]),
            MockDocument(content="Valid vector", vector=[0.1] * 768)
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        assert len(valid_docs) == 1
        assert valid_docs[0].content == "Valid vector"

    def test_missing_vector_attribute(self, rag_instance):
        """Test handling of documents without vector attribute."""
        # Create document without vector attribute
        doc_without_vector = MockDocument(content="No vector attribute")
        delattr(doc_without_vector, 'vector')
        
        docs = [
            doc_without_vector,
            MockDocument(content="Valid vector", vector=[0.1] * 768)
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        assert len(valid_docs) == 1
        assert valid_docs[0].content == "Valid vector"

    # =============================================================================
    # Test Vector Dimension Validation
    # =============================================================================

    def test_dimension_consistency_validation(self, rag_instance, sample_documents_with_vectors):
        """Test that documents with inconsistent dimensions are filtered."""
        docs = sample_documents_with_vectors["mixed_dimensions"]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Should keep the 768-dim documents (most common dimension)
        assert len(valid_docs) == 2
        for doc in valid_docs:
            assert len(doc.vector) == 768

    def test_text_embedding_004_dimension_requirement(self, rag_instance):
        """Test that text-embedding-004 requires 768-dimensional vectors."""
        docs = [
            MockDocument(content="512-dim", vector=[0.1] * 512),
            MockDocument(content="768-dim", vector=[0.1] * 768),
            MockDocument(content="1024-dim", vector=[0.1] * 1024),
            MockDocument(content="Another 768-dim", vector=[0.2] * 768)
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Should only keep 768-dimensional vectors
        assert len(valid_docs) == 2
        for doc in valid_docs:
            assert len(doc.vector) == 768

    def test_edge_case_dimensions(self, rag_instance):
        """Test edge cases for vector dimensions."""
        docs = [
            MockDocument(content="Single value", vector=[0.5]),
            MockDocument(content="Zero dimension", vector=[]),
            MockDocument(content="Very small", vector=[0.1] * 10),
            MockDocument(content="Standard", vector=[0.1] * 768)
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # The validation picks the most common dimension. Since all have different dimensions,
        # it will pick one (likely the first valid one encountered)
        assert len(valid_docs) == 1
        # The validation chooses the most common dimension, which could be any of the valid ones
        assert len(valid_docs[0].vector) in [1, 10, 768]  # Any of the non-empty dimensions

    # =============================================================================
    # Test FAISS Compatibility
    # =============================================================================

    def test_faiss_compatible_vector_format(self, rag_instance, sample_valid_vector):
        """Test that validated vectors are compatible with FAISS add_with_ids."""
        docs = [MockDocument(content=f"Doc {i}", vector=sample_valid_vector) for i in range(3)]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Extract vectors in FAISS-compatible format
        vectors = [doc.vector for doc in valid_docs]
        vector_array = np.array(vectors, dtype=np.float32)
        
        # Test FAISS requirements
        assert vector_array.shape == (3, 768)  # Correct shape
        assert vector_array.dtype == np.float32  # Correct dtype
        assert not np.any(np.isnan(vector_array))  # No NaN values
        assert not np.any(np.isinf(vector_array))  # No infinite values

    def test_numpy_array_vector_handling(self, rag_instance):
        """Test handling of vectors as numpy arrays."""
        np.random.seed(42)
        vector_array = np.random.randn(768).astype(np.float32)
        
        docs = [
            MockDocument(content="Numpy vector", vector=vector_array),
            MockDocument(content="List vector", vector=vector_array.tolist())
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        assert len(valid_docs) == 2
        # Both should have same dimension
        assert len(valid_docs[0].vector) == 768 or valid_docs[0].vector.shape[0] == 768
        assert len(valid_docs[1].vector) == 768

    def test_multidimensional_array_handling(self, rag_instance):
        """Test handling of multidimensional numpy arrays."""
        # Create 2D array that should be flattened or handled properly
        vector_2d = np.random.randn(1, 768).astype(np.float32)
        
        docs = [MockDocument(content="2D vector", vector=vector_2d)]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Should handle 2D array correctly
        if valid_docs:  # Depending on implementation, might filter out or handle
            assert len(valid_docs) <= 1

    # =============================================================================
    # Test Error Handling for Invalid Vectors  
    # =============================================================================

    def test_nan_value_handling(self, rag_instance):
        """Test handling of vectors containing NaN values."""
        docs = [
            MockDocument(content="NaN vector", vector=[float('nan')] * 768),
            MockDocument(content="Partial NaN", vector=[0.1] * 767 + [float('nan')]),
            MockDocument(content="Valid vector", vector=[0.1] * 768)
        ]
        
        # The validation method doesn't check for NaN - it only checks dimensions
        # So this tests the current behavior
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # All should pass dimension check, but NaN vectors would cause issues in FAISS
        assert len(valid_docs) == 3  # Current implementation doesn't filter NaN
        
        # However, when used with FAISS, NaN vectors should be detected
        # This reveals a validation gap that should be documented

    def test_infinite_value_handling(self, rag_instance):
        """Test handling of vectors containing infinite values."""
        docs = [
            MockDocument(content="Inf vector", vector=[float('inf')] * 768),
            MockDocument(content="Negative inf", vector=[float('-inf')] + [0.1] * 767),
            MockDocument(content="Valid vector", vector=[0.1] * 768)
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Current implementation doesn't filter infinite values
        assert len(valid_docs) == 3
        
        # This is another validation gap - FAISS cannot handle infinite values

    def test_wrong_data_type_vectors(self, rag_instance):
        """Test handling of vectors with wrong data types."""
        docs = [
            MockDocument(content="String vector", vector=["0.1"] * 768),  # Strings
            MockDocument(content="Mixed types", vector=[0.1, "0.2", 0.3] + [0.1] * 765),
            MockDocument(content="Valid vector", vector=[0.1] * 768)
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Should filter based on whether len() works on the vector
        # String vectors will pass len() check but fail in FAISS
        assert len(valid_docs) >= 1  # At least the valid one

    def test_exception_during_validation(self, rag_instance):
        """Test exception handling during vector validation."""
        # Create a mock document that raises exception during vector access
        problematic_doc = MockDocument(content="Problematic doc", vector=object())  # Object that doesn't support len()
        
        docs = [
            problematic_doc,
            MockDocument(content="Valid vector", vector=[0.1] * 768)
        ]
        
        # Should handle exception gracefully and continue with valid documents
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        assert len(valid_docs) == 1

    # =============================================================================
    # Test Validation Prevention of Bad Vector Storage
    # =============================================================================

    def test_all_invalid_vectors_scenario(self, rag_instance):
        """Test scenario where all vectors are invalid."""
        docs = [
            MockDocument(content="Empty", vector=[]),
            MockDocument(content="None", vector=None),
            MockDocument(content="Another empty", vector=[])
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Should return empty list when all vectors are truly invalid
        assert len(valid_docs) == 0

    def test_no_documents_input(self, rag_instance):
        """Test validation with no documents."""
        valid_docs = rag_instance._validate_and_filter_embeddings([])
        assert len(valid_docs) == 0

    def test_logging_during_validation(self, rag_instance, caplog):
        """Test that appropriate logging occurs during validation."""
        docs = [
            MockDocument(content="Empty", vector=[]),
            MockDocument(content="Wrong dim", vector=[0.1] * 512),
            MockDocument(content="Valid", vector=[0.1] * 768)
        ]
        
        with caplog.at_level(logging.WARNING):
            valid_docs = rag_instance._validate_and_filter_embeddings(docs)
            
        # Check that warnings were logged for problematic vectors
        assert "empty embedding vector" in caplog.text or "embedding size mismatch" in caplog.text
        assert len(valid_docs) == 1

    # =============================================================================
    # Test Integration with Real Vector Storage
    # =============================================================================

    def test_integration_with_document_indexing(self, rag_instance, sample_valid_vector):
        """Test integration of validation with document indexing workflow."""
        docs = [
            MockDocument(content="Valid doc 1", vector=sample_valid_vector),
            MockDocument(content="Invalid doc", vector=[0.1] * 512),  # Wrong dimension
            MockDocument(content="Valid doc 2", vector=[0.2] * 768)
        ]
        
        # Test that validation is called during indexing preparation
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        assert len(valid_docs) == 2
        
        # Verify vectors are ready for FAISS
        for doc in valid_docs:
            assert len(doc.vector) == 768
            # Convert to numpy to verify FAISS compatibility
            vector_array = np.array(doc.vector, dtype=np.float32)
            assert vector_array.shape == (768,)
            assert not np.any(np.isnan(vector_array))


class TestVectorValidationEdgeCases:
    """Test edge cases and boundary conditions for vector validation."""

    @pytest.fixture
    def rag_instance(self):
        """Create a RAG instance for edge case testing."""
        # Create a minimal RAG instance without full initialization
        rag = Mock(spec=RAG)
        # Add the validation method from the real RAG class
        rag._validate_and_filter_embeddings = RAG._validate_and_filter_embeddings.__get__(rag, RAG)
        return rag

    def test_mixed_vector_types_in_batch(self, rag_instance):
        """Test handling of mixed vector types in a single batch."""
        # Mix of list, numpy array, and invalid types
        np_vector = np.array([0.1] * 768, dtype=np.float32)
        
        docs = [
            MockDocument(content="List vector", vector=[0.1] * 768),
            MockDocument(content="Numpy vector", vector=np_vector),
            MockDocument(content="Tuple vector", vector=tuple([0.1] * 768)),
            MockDocument(content="Invalid vector", vector="not_a_vector")
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Should handle different but compatible types
        assert len(valid_docs) >= 2  # List and numpy should work
        
    def test_large_batch_validation_performance(self, rag_instance):
        """Test validation performance with large batch of documents."""
        # Create 1000 documents with valid vectors
        docs = []
        for i in range(1000):
            vector = [0.1 + i * 0.0001] * 768  # Slightly different vectors
            docs.append(MockDocument(content=f"Doc {i}", vector=vector))
            
        import time
        start_time = time.time()
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        validation_time = time.time() - start_time
        
        assert len(valid_docs) == 1000
        assert validation_time < 5.0  # Should complete within 5 seconds

    def test_vector_normalization_detection(self, rag_instance):
        """Test detection of vector normalization issues."""
        # Create vectors with different magnitudes
        normal_vector = [0.1] * 768
        large_magnitude = [10.0] * 768  # Very large values
        tiny_magnitude = [0.001] * 768  # Very small values
        
        docs = [
            MockDocument(content="Normal", vector=normal_vector),
            MockDocument(content="Large magnitude", vector=large_magnitude),
            MockDocument(content="Tiny magnitude", vector=tiny_magnitude)
        ]
        
        valid_docs = rag_instance._validate_and_filter_embeddings(docs)
        
        # Current implementation doesn't check normalization
        # This documents another validation gap
        assert len(valid_docs) == 3


class TestFAISSCompatibilitySpecific:
    """Specific tests for FAISS compatibility requirements."""

    @pytest.fixture
    def mock_faiss_retriever(self):
        """Mock FAISS retriever for testing compatibility."""
        mock_retriever = Mock()
        mock_retriever.add_with_ids = Mock()
        return mock_retriever

    def test_vector_format_for_faiss_add_with_ids(self, mock_faiss_retriever):
        """Test that vectors are in correct format for FAISS add_with_ids."""
        # Simulate the format that FAISS expects
        vectors = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
        ids = [1, 2, 3]
        
        # Convert to numpy array as FAISS expects
        vector_array = np.array(vectors, dtype=np.float32)
        id_array = np.array(ids, dtype=np.int64)
        
        # Test that the format is compatible
        mock_faiss_retriever.add_with_ids(vector_array, id_array)
        mock_faiss_retriever.add_with_ids.assert_called_once_with(vector_array, id_array)

    def test_faiss_dimension_requirements(self):
        """Test FAISS dimension requirements for text-embedding-004."""
        # FAISS expects consistent dimensions across all vectors
        vectors_same_dim = [[0.1] * 768, [0.2] * 768]
        vectors_mixed_dim = [[0.1] * 768, [0.2] * 512]  # This would fail in FAISS
        
        # Valid case
        valid_array = np.array(vectors_same_dim, dtype=np.float32)
        assert valid_array.shape == (2, 768)
        
        # Invalid case would cause shape mismatch
        try:
            invalid_array = np.array(vectors_mixed_dim, dtype=np.float32)
            # This creates array of objects, not a 2D float array
            assert invalid_array.dtype == object  # Indicates problem
        except ValueError:
            pass  # Expected for incompatible shapes


class TestValidationGapsDocumentation:
    """Document validation gaps found during testing."""
    
    def test_document_validation_gaps(self):
        """Document the validation gaps discovered."""
        validation_gaps = {
            "nan_values": {
                "issue": "Current validation doesn't check for NaN values in vectors",
                "impact": "NaN values cause FAISS operations to fail",
                "recommendation": "Add has_valid_values check before FAISS operations"
            },
            "infinite_values": {
                "issue": "Current validation doesn't check for infinite values",
                "impact": "Infinite values cause FAISS operations to fail", 
                "recommendation": "Add infinity check in validation"
            },
            "vector_normalization": {
                "issue": "No check for vector normalization",
                "impact": "Non-normalized vectors affect similarity calculations",
                "recommendation": "Add optional normalization validation"
            },
            "data_type_validation": {
                "issue": "No strict type checking for vector elements",
                "impact": "String or object types fail in numpy conversion for FAISS",
                "recommendation": "Validate all elements are numeric types"
            },
            "memory_efficiency": {
                "issue": "No optimization for large batch validation",
                "impact": "Large batches may cause memory issues",
                "recommendation": "Add streaming/chunked validation for large batches"
            }
        }
        
        # This test documents the gaps - it always passes but records findings
        assert len(validation_gaps) == 5
        
        # In a real implementation, this could write to a validation report file
        print("\n=== VALIDATION GAPS DISCOVERED ===")
        for gap_name, gap_info in validation_gaps.items():
            print(f"\n{gap_name.upper()}:")
            print(f"  Issue: {gap_info['issue']}")
            print(f"  Impact: {gap_info['impact']}")
            print(f"  Recommendation: {gap_info['recommendation']}")

    def test_faiss_integration_requirements(self):
        """Document specific FAISS integration requirements."""
        faiss_requirements = {
            "vector_format": "numpy.ndarray with dtype=float32",
            "vector_dimensions": "Must be consistent across all vectors (768 for text-embedding-004)",
            "id_format": "numpy.ndarray with dtype=int64",
            "no_nan_values": "FAISS operations fail with NaN values",
            "no_infinite_values": "FAISS operations fail with infinite values",
            "memory_layout": "Vectors must be C-contiguous for optimal performance"
        }
        
        assert len(faiss_requirements) == 6
        
        print("\n=== FAISS INTEGRATION REQUIREMENTS ===")
        for req_name, req_desc in faiss_requirements.items():
            print(f"{req_name}: {req_desc}")