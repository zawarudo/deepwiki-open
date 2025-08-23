"""
Shared fixtures for API testing.

This module provides common fixtures and configuration for testing the FastAPI application.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os
import tempfile
import shutil
from typing import Generator, AsyncGenerator

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
    Create an async client for asynchronous testing.
    
    Yields:
        AsyncClient: HTTPX async client for asynchronous requests
    """
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


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
        "NODE_ENV"
    ]
    
    for var in test_env_vars:
        original_env[var] = os.environ.get(var)
    
    # Set test environment variables
    os.environ["NODE_ENV"] = "test"
    # Don't set API keys to None to avoid warnings, just leave them as they are
    
    yield
    
    # Restore original environment variables
    for var, value in original_env.items():
        if value is not None:
            os.environ[var] = value
        else:
            os.environ.pop(var, None)


# Test markers configuration
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.api
]