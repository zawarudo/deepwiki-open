"""
Fixtures specifically for testing the embedding bug scenarios.

These fixtures recreate the exact conditions that cause the embedding pipeline
to fail, including batch processing issues, dimension mismatches, and API errors.
"""

import pytest
import numpy as np
from typing import List, Dict, Any
from unittest.mock import Mock


@pytest.fixture
def embedding_bug_scenario_data():
    """
    Create data that reproduces the embedding bug conditions.
    
    Returns:
        dict: Test data that causes the embedding bug
    """
    return {
        # Scenario 1: Empty or very short documents
        "empty_documents": [
            {"content": "", "metadata": {"id": "empty1"}},
            {"content": "   ", "metadata": {"id": "whitespace"}},
            {"content": "a", "metadata": {"id": "single_char"}},
        ],
        
        # Scenario 2: Documents with problematic encoding
        "encoding_problematic": [
            {
                "content": "Document with null bytes\x00and control chars\x01\x02",
                "metadata": {"id": "null_bytes"}
            },
            {
                "content": "Mixed encoding: café résumé naïve 北京 東京",
                "metadata": {"id": "mixed_encoding"}
            },
        ],
        
        # Scenario 3: Large batch processing that might cause memory issues
        "large_batch": [
            {
                "content": f"This is document number {i} with repeated content. " * 50,
                "metadata": {"id": f"large_doc_{i}"}
            }
            for i in range(100)  # Large batch size
        ],
        
        # Scenario 4: Documents that exceed token limits
        "token_limit_exceeded": [
            {
                "content": "Very long document. " * 5000,  # Extremely long content
                "metadata": {"id": "token_overflow"}
            }
        ],
        
        # Scenario 5: Concurrent batch processing edge case
        "concurrent_batches": {
            "batch_1": [
                {"content": f"Batch 1 document {i}", "metadata": {"id": f"b1_doc_{i}"}}
                for i in range(50)
            ],
            "batch_2": [
                {"content": f"Batch 2 document {i}", "metadata": {"id": f"b2_doc_{i}"}}
                for i in range(50)
            ],
            "batch_3": [
                {"content": f"Batch 3 document {i}", "metadata": {"id": f"b3_doc_{i}"}}
                for i in range(50)
            ],
        }
    }


@pytest.fixture
def embedding_api_failure_scenarios():
    """
    Create scenarios that simulate API failures during embedding.
    
    Returns:
        dict: API failure scenarios
    """
    def create_rate_limit_response():
        """Simulate rate limit response."""
        response = Mock()
        response.status_code = 429
        response.json.return_value = {
            "error": {
                "code": 429,
                "message": "Rate limit exceeded",
                "status": "RESOURCE_EXHAUSTED"
            }
        }
        return response
    
    def create_quota_exceeded_response():
        """Simulate quota exceeded response."""
        response = Mock()
        response.status_code = 403
        response.json.return_value = {
            "error": {
                "code": 403,
                "message": "Quota exceeded",
                "status": "PERMISSION_DENIED"
            }
        }
        return response
    
    def create_timeout_response():
        """Simulate timeout response."""
        response = Mock()
        response.status_code = 504
        response.json.return_value = {
            "error": {
                "code": 504,
                "message": "Gateway timeout",
                "status": "DEADLINE_EXCEEDED"
            }
        }
        return response
    
    def create_invalid_request_response():
        """Simulate invalid request response."""
        response = Mock()
        response.status_code = 400
        response.json.return_value = {
            "error": {
                "code": 400,
                "message": "Invalid request: text content is empty",
                "status": "INVALID_ARGUMENT"
            }
        }
        return response
    
    return {
        "rate_limit": create_rate_limit_response(),
        "quota_exceeded": create_quota_exceeded_response(),
        "timeout": create_timeout_response(),
        "invalid_request": create_invalid_request_response()
    }


@pytest.fixture
def malformed_embedding_responses():
    """
    Create malformed embedding responses that might cause parsing errors.
    
    Returns:
        dict: Various malformed responses
    """
    return {
        "missing_values": {
            "embedding": {}  # Missing 'values' key
        },
        
        "wrong_structure": {
            "embeddings": [{"vectors": [0.1] * 768}]  # Wrong key name
        },
        
        "invalid_dimensions": {
            "embedding": {
                "values": [0.1] * 512  # Wrong dimension count
            }
        },
        
        "mixed_types": {
            "embedding": {
                "values": [0.1, "0.2", None, float('inf')] + [0.1] * 764
            }
        },
        
        "empty_response": {},
        
        "nested_error": {
            "embedding": {
                "values": [],
                "error": "Internal processing error"
            }
        }
    }


@pytest.fixture
def batch_processing_edge_cases():
    """
    Create edge cases specific to batch processing that might cause failures.
    
    Returns:
        dict: Batch processing edge cases
    """
    return {
        # Mixed content lengths in single batch
        "mixed_lengths": [
            {"content": "Short", "metadata": {"id": "short"}},
            {"content": "Medium length content with more details", "metadata": {"id": "medium"}},
            {"content": "Very long content " * 100, "metadata": {"id": "very_long"}},
        ],
        
        # Batch with duplicate content
        "duplicates": [
            {"content": "Duplicate content", "metadata": {"id": "dup1"}},
            {"content": "Duplicate content", "metadata": {"id": "dup2"}},
            {"content": "Unique content", "metadata": {"id": "unique"}},
        ],
        
        # Batch with invalid UTF-8 sequences
        "invalid_utf8": [
            {
                "content": "Valid content before invalid \udcff\udcfe",
                "metadata": {"id": "invalid_utf8"}
            }
        ],
        
        # Batch size exactly at limits
        "exact_limit_batch": [
            {
                "content": f"Document {i} at batch limit",
                "metadata": {"id": f"limit_doc_{i}"}
            }
            for i in range(500)  # Exactly at configured batch_size limit
        ],
        
        # Single item batch (edge case)
        "single_item": [
            {
                "content": "Single document in batch",
                "metadata": {"id": "single"}
            }
        ]
    }


@pytest.fixture
def vector_dimension_mismatch_scenarios():
    """
    Create scenarios where vector dimensions don't match expectations.
    
    Returns:
        dict: Dimension mismatch scenarios
    """
    np.random.seed(42)  # For reproducible tests
    
    return {
        "text_embedding_004": {
            "expected_dim": 768,
            "actual_vectors": [
                np.random.randn(512).tolist(),  # Wrong dimension
                np.random.randn(1024).tolist(),  # Wrong dimension
                np.random.randn(768).tolist(),  # Correct dimension
            ]
        },
        
        "mixed_dimensions": [
            np.random.randn(256).tolist(),
            np.random.randn(512).tolist(),
            np.random.randn(768).tolist(),
            np.random.randn(1024).tolist(),
        ],
        
        "zero_dimension": [],
        
        "single_value": [0.5],
        
        "incomplete_vector": [0.1] * 300,  # Incomplete 768-dim vector
    }


@pytest.fixture
def memory_pressure_scenarios():
    """
    Create scenarios that might cause memory pressure during embedding processing.
    
    Returns:
        dict: Memory pressure test scenarios
    """
    return {
        "large_documents": [
            {
                "content": "Large document content. " * 10000,  # ~250KB per document
                "metadata": {"id": f"large_{i}"}
            }
            for i in range(20)  # ~5MB total
        ],
        
        "many_small_documents": [
            {
                "content": f"Small doc {i}",
                "metadata": {"id": f"small_{i}"}
            }
            for i in range(10000)  # Many small documents
        ],
        
        "mixed_size_stress_test": (
            [
                {
                    "content": "Tiny",
                    "metadata": {"id": f"tiny_{i}"}
                }
                for i in range(1000)
            ] +
            [
                {
                    "content": "Medium content " * 100,
                    "metadata": {"id": f"medium_{i}"}
                }
                for i in range(100)
            ] +
            [
                {
                    "content": "Large content " * 5000,
                    "metadata": {"id": f"large_{i}"}
                }
                for i in range(10)
            ]
        )
    }


@pytest.fixture
def embedding_validation_scenarios():
    """
    Create scenarios for validating embedding outputs and catching common bugs.
    
    Returns:
        dict: Validation scenarios
    """
    np.random.seed(42)
    
    def create_valid_vector():
        """Create a properly normalized vector."""
        vector = np.random.randn(768).astype(np.float32)
        return (vector / np.linalg.norm(vector)).tolist()
    
    def create_invalid_vector():
        """Create an invalid vector with various issues."""
        return [float('nan')] * 768
    
    return {
        "valid_embeddings": [create_valid_vector() for _ in range(10)],
        
        "invalid_embeddings": {
            "contains_nan": [float('nan')] + [0.1] * 767,
            "contains_inf": [float('inf')] + [0.1] * 767,
            "all_zeros": [0.0] * 768,
            "not_normalized": [1.0] * 768,  # Magnitude >> 1
            "empty_vector": [],
            "wrong_type": ["0.1"] * 768,  # Strings instead of floats
        },
        
        "mixed_batch": [
            create_valid_vector(),
            [float('nan')] * 768,
            create_valid_vector(),
            [0.0] * 768,
            create_valid_vector()
        ]
    }