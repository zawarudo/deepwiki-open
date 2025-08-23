"""
Shared fixtures for API testing.

This module provides common fixtures and configuration for testing the FastAPI application.
Includes comprehensive fixtures for document processing, embedding testing, and vector validation.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os
import tempfile
import shutil
import json
import numpy as np
from typing import Generator, AsyncGenerator, Dict, List, Any, Optional
from unittest.mock import Mock, patch

# Import the FastAPI app
from api.api import app


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    """
    Create a test client for synchronous testing.
    
    Yields:
        TestClient: FastAPI test client for synchronous requests
    """
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async client for asynchronous testing with request/response logging.
    
    Yields:
        AsyncClient: HTTPX async client for asynchronous requests
    """
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    
    async with AsyncClient(
        transport=transport, 
        base_url="http://test",
        timeout=30.0  # Longer timeout for embedding operations
    ) as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_async_client(async_client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an authenticated async client for testing protected endpoints.
    
    Args:
        async_client: Base async client fixture
        
    Yields:
        AsyncClient: Authenticated async client
    """
    # Add any authentication headers if needed
    # For now, just return the base client since most endpoints are public
    yield async_client


@pytest_asyncio.fixture
async def debug_async_client(async_client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async client with request/response debugging enabled.
    
    Args:
        async_client: Base async client fixture
        
    Yields:
        AsyncClient: Debug-enabled async client
    """
    import logging
    
    # Enable debug logging for this client
    logger = logging.getLogger("httpx")
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    
    try:
        yield async_client
    finally:
        logger.setLevel(original_level)


@pytest.fixture(scope="session")
def temp_cache_dir() -> Generator[str, None, None]:
    """
    Create a temporary directory for testing wiki cache functionality.
    
    Yields:
        str: Path to temporary cache directory
    """
    temp_dir = tempfile.mkdtemp(prefix="test_wiki_cache_")
    # Set environment variable to use temp directory
    original_adalflow_root = os.environ.get("ADALFLOW_ROOT_PATH")
    os.environ["ADALFLOW_ROOT_PATH"] = temp_dir
    
    try:
        yield temp_dir
    finally:
        # Cleanup
        if original_adalflow_root:
            os.environ["ADALFLOW_ROOT_PATH"] = original_adalflow_root
        else:
            os.environ.pop("ADALFLOW_ROOT_PATH", None)
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_wiki_page():
    """
    Create a sample wiki page for testing.
    
    Returns:
        dict: Sample wiki page data
    """
    return {
        "id": "test-page-1",
        "title": "Test Page",
        "content": "This is a test page content.",
        "filePaths": ["test/file1.py", "test/file2.py"],
        "importance": "high",
        "relatedPages": ["test-page-2"]
    }


@pytest.fixture
def sample_repo_info():
    """
    Create sample repository info for testing.
    
    Returns:
        dict: Sample repository information
    """
    return {
        "owner": "testuser",
        "repo": "test-repo", 
        "type": "github",
        "token": None,
        "localPath": None,
        "repoUrl": "https://github.com/testuser/test-repo"
    }


@pytest.fixture
def sample_wiki_structure(sample_wiki_page):
    """
    Create a sample wiki structure for testing.
    
    Args:
        sample_wiki_page: Sample wiki page fixture
        
    Returns:
        dict: Sample wiki structure
    """
    return {
        "id": "test-wiki",
        "title": "Test Wiki",
        "description": "A test wiki structure",
        "pages": [sample_wiki_page],
        "sections": [
            {
                "id": "section-1",
                "title": "Test Section",
                "pages": ["test-page-1"],
                "subsections": None
            }
        ],
        "rootSections": ["section-1"]
    }


@pytest.fixture
def sample_wiki_cache_request(sample_repo_info, sample_wiki_structure, sample_wiki_page):
    """
    Create a sample wiki cache request for testing.
    
    Args:
        sample_repo_info: Sample repository info fixture
        sample_wiki_structure: Sample wiki structure fixture
        sample_wiki_page: Sample wiki page fixture
        
    Returns:
        dict: Sample wiki cache request data
    """
    return {
        "repo": sample_repo_info,
        "language": "en",
        "wiki_structure": sample_wiki_structure,
        "generated_pages": {"test-page-1": sample_wiki_page},
        "provider": "google",
        "model": "gemini-2.5-flash"
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Setup test environment variables and configuration.
    
    This fixture runs automatically for each test to ensure clean environment.
    """
    # Store original environment variables
    original_env = {}
    test_env_vars = [
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "NODE_ENV",
        "ADALFLOW_ROOT_PATH"
    ]
    
    for var in test_env_vars:
        original_env[var] = os.environ.get(var)
    
    # Set test environment variables
    os.environ["NODE_ENV"] = "test"
    # For API keys, use test keys if available or mock them
    if not os.environ.get("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = "test-google-api-key"
    
    yield
    
    # Restore original environment variables
    for var, value in original_env.items():
        if value is not None:
            os.environ[var] = value
        else:
            os.environ.pop(var, None)


# =============================================================================
# Document Processing Fixtures
# =============================================================================

@pytest.fixture
def sample_document():
    """
    Create a sample document for embedding testing.
    
    Returns:
        dict: Sample document with various content types
    """
    return {
        "content": "This is a sample document for testing embeddings. It contains multiple sentences and various types of content.",
        "metadata": {
            "title": "Sample Document",
            "author": "Test User",
            "created_at": "2024-01-01T00:00:00Z",
            "file_path": "/test/sample.md",
            "source": "test"
        },
        "chunks": [
            "This is a sample document for testing embeddings.",
            "It contains multiple sentences and various types of content."
        ]
    }


@pytest.fixture
def sample_documents():
    """
    Create multiple sample documents for batch processing tests.
    
    Returns:
        List[dict]: List of sample documents
    """
    return [
        {
            "content": "First document content for testing batch processing.",
            "metadata": {"title": "Document 1", "id": "doc1"}
        },
        {
            "content": "Second document with different content for diversity testing.",
            "metadata": {"title": "Document 2", "id": "doc2"}
        },
        {
            "content": "Third document containing technical terms like API, JSON, and HTTP.",
            "metadata": {"title": "Document 3", "id": "doc3"}
        }
    ]


@pytest.fixture
def edge_case_documents():
    """
    Create edge case documents for robustness testing.
    
    Returns:
        dict: Documents with edge cases
    """
    return {
        "empty": {"content": "", "metadata": {"title": "Empty Document"}},
        "whitespace_only": {"content": "   \n\t  ", "metadata": {"title": "Whitespace Only"}},
        "very_short": {"content": "Hi", "metadata": {"title": "Very Short"}},
        "special_chars": {
            "content": "Document with special chars: !@#$%^&*(){}[]|\\:;\"'<>,.?/~`",
            "metadata": {"title": "Special Characters"}
        },
        "unicode": {
            "content": "Unicode content: 你好 こんにちは 🚀 émojis and accénts",
            "metadata": {"title": "Unicode Content"}
        },
        "very_long": {
            "content": "Very long document. " * 1000,  # 20,000+ characters
            "metadata": {"title": "Very Long Document"}
        }
    }


@pytest.fixture
def document_chunks():
    """
    Create pre-chunked document content for chunk processing tests.
    
    Returns:
        dict: Document chunks with various sizes
    """
    return {
        "normal_chunks": [
            "This is the first chunk of a document.",
            "This is the second chunk with different content.",
            "Final chunk with conclusion information."
        ],
        "overlapping_chunks": [
            "Start of document with important context.",
            "Important context continues with new information.",
            "New information leads to final conclusions."
        ],
        "varying_sizes": [
            "Short.",
            "Medium length chunk with more information.",
            "Very long chunk that contains a lot of detailed information and spans multiple sentences to test how the system handles larger text segments."
        ]
    }


# =============================================================================
# Embedding and Vector Fixtures
# =============================================================================

@pytest.fixture
def sample_embedding_vector():
    """
    Create a sample embedding vector with correct dimensions.
    
    Returns:
        List[float]: 768-dimensional embedding vector (text-embedding-004 format)
    """
    # Generate a random normalized vector
    np.random.seed(42)  # For reproducible tests
    vector = np.random.randn(768).astype(np.float32)
    # Normalize to unit vector
    vector = vector / np.linalg.norm(vector)
    return vector.tolist()


@pytest.fixture
def batch_embedding_vectors():
    """
    Create multiple embedding vectors for batch testing.
    
    Returns:
        List[List[float]]: Multiple 768-dimensional embedding vectors
    """
    np.random.seed(42)
    vectors = []
    for i in range(5):
        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        vectors.append(vector.tolist())
    return vectors


@pytest.fixture
def invalid_embedding_vectors():
    """
    Create invalid embedding vectors for error testing.
    
    Returns:
        dict: Various types of invalid vectors
    """
    return {
        "empty": [],
        "wrong_dimension": [0.1] * 512,  # Wrong dimension
        "contains_nan": [0.1] * 767 + [float('nan')],
        "contains_inf": [0.1] * 767 + [float('inf')],
        "all_zeros": [0.0] * 768,
        "not_normalized": [1.0] * 768,  # Not unit vector
        "wrong_type": ["0.1"] * 768  # String instead of float
    }


@pytest.fixture
def embedding_response_mock():
    """
    Create mock embedding response data.
    
    Returns:
        dict: Mock Google Embedding API response
    """
    return {
        "embedding": {
            "values": [0.1] * 768  # Mock 768-dimensional vector
        }
    }


@pytest.fixture
def batch_embedding_response_mock():
    """
    Create mock batch embedding response data.
    
    Returns:
        dict: Mock batch embedding API response
    """
    return {
        "embeddings": [
            {"values": [0.1 + i * 0.01] * 768} for i in range(3)
        ]
    }


# =============================================================================
# Vector Validation Utilities
# =============================================================================

@pytest.fixture
def vector_validator():
    """
    Create vector validation utilities for testing.
    
    Returns:
        dict: Validation utility functions
    """
    def is_valid_dimension(vector: List[float], expected_dim: int = 768) -> bool:
        """Check if vector has correct dimension."""
        return len(vector) == expected_dim
    
    def is_normalized(vector: List[float], tolerance: float = 1e-6) -> bool:
        """Check if vector is normalized (unit vector)."""
        norm = np.linalg.norm(vector)
        return abs(norm - 1.0) < tolerance
    
    def has_valid_values(vector: List[float]) -> bool:
        """Check if vector contains only valid float values."""
        return all(
            isinstance(v, (int, float)) and 
            not np.isnan(v) and 
            not np.isinf(v) 
            for v in vector
        )
    
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    return {
        "is_valid_dimension": is_valid_dimension,
        "is_normalized": is_normalized,
        "has_valid_values": has_valid_values,
        "cosine_similarity": cosine_similarity
    }


# =============================================================================
# Mock API Clients and Responses
# =============================================================================

@pytest.fixture
def mock_google_embedding_client():
    """
    Create a mock Google Embedding Client for testing.
    
    Returns:
        Mock: Mocked GoogleEmbeddingClient
    """
    mock_client = Mock()
    
    # Mock successful embedding response
    mock_response = Mock()
    mock_response.json.return_value = {
        "embedding": {
            "values": [0.1] * 768
        }
    }
    mock_response.status_code = 200
    mock_client.call.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_embedding_service():
    """
    Create a mock embedding service for comprehensive testing.
    
    Returns:
        Mock: Mocked embedding service with various response scenarios
    """
    mock_service = Mock()
    
    def side_effect(*args, **kwargs):
        # Return different responses based on input
        if "error" in str(args[0]):
            response = Mock()
            response.status_code = 400
            response.json.return_value = {"error": "Invalid input"}
            return response
        
        # Normal successful response
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "embedding": {"values": [0.1] * 768}
        }
        return response
    
    mock_service.embed.side_effect = side_effect
    return mock_service


# =============================================================================
# Test Data Generators
# =============================================================================

@pytest.fixture
def test_data_generator():
    """
    Create utilities for generating test data on demand.
    
    Returns:
        dict: Data generation functions
    """
    def generate_documents(count: int, content_template: str = "Document {i} content") -> List[dict]:
        """Generate multiple test documents."""
        return [
            {
                "content": content_template.format(i=i),
                "metadata": {"title": f"Document {i}", "id": f"doc{i}"}
            }
            for i in range(count)
        ]
    
    def generate_embedding_vectors(count: int, dimension: int = 768) -> List[List[float]]:
        """Generate multiple embedding vectors."""
        np.random.seed(42)
        vectors = []
        for i in range(count):
            vector = np.random.randn(dimension).astype(np.float32)
            vector = vector / np.linalg.norm(vector)
            vectors.append(vector.tolist())
        return vectors
    
    def generate_chunks(text: str, chunk_size: int = 100, overlap: int = 20) -> List[str]:
        """Generate text chunks with overlap."""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - overlap
            if start >= len(text):
                break
        return chunks
    
    return {
        "generate_documents": generate_documents,
        "generate_embedding_vectors": generate_embedding_vectors,
        "generate_chunks": generate_chunks
    }


# Test markers configuration
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.api
]