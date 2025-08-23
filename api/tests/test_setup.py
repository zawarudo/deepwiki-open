"""
Test setup validation.

This module contains tests to validate that the pytest infrastructure
and FastAPI testing setup is working correctly.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json


class TestSetupValidation:
    """Test class to validate the testing setup."""

    @pytest.mark.unit
    def test_pytest_setup(self):
        """Test that pytest is configured correctly."""
        # Simple assertion to validate pytest is working
        assert True, "pytest is working correctly"

    @pytest.mark.api
    def test_fastapi_sync_client(self, test_client: TestClient):
        """Test that the synchronous FastAPI test client works."""
        # Test the health check endpoint
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
        assert data["service"] == "deepwiki-api"

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_fastapi_async_client(self, async_client: AsyncClient):
        """Test that the asynchronous FastAPI test client works."""
        # Test the root endpoint
        response = await async_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Welcome to Streaming API"
        assert "version" in data
        assert "endpoints" in data

    @pytest.mark.api
    def test_model_config_endpoint(self, test_client: TestClient):
        """Test the model configuration endpoint."""
        response = test_client.get("/models/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "providers" in data
        assert "defaultProvider" in data
        assert isinstance(data["providers"], list)
        
        # Validate provider structure if any providers exist
        if data["providers"]:
            provider = data["providers"][0]
            assert "id" in provider
            assert "name" in provider
            assert "models" in provider
            assert isinstance(provider["models"], list)

    @pytest.mark.api
    def test_lang_config_endpoint(self, test_client: TestClient):
        """Test the language configuration endpoint."""
        response = test_client.get("/lang/config")
        assert response.status_code == 200
        
        # Should return language configuration from config
        data = response.json()
        # Validate it's a dictionary (structure may vary based on config)
        assert isinstance(data, dict)

    @pytest.mark.api
    def test_auth_status_endpoint(self, test_client: TestClient):
        """Test the authentication status endpoint."""
        response = test_client.get("/auth/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "auth_required" in data
        assert isinstance(data["auth_required"], bool)

    @pytest.mark.integration
    @pytest.mark.api
    def test_wiki_cache_endpoints_not_found(self, test_client: TestClient):
        """Test wiki cache endpoints with non-existent data."""
        # Test GET for non-existent cache
        params = {
            "owner": "nonexistent",
            "repo": "nonexistent",
            "repo_type": "github",
            "language": "en"
        }
        response = test_client.get("/api/wiki_cache", params=params)
        assert response.status_code == 200
        # Should return null/None for non-existent cache
        assert response.json() is None

    @pytest.mark.integration
    def test_sample_fixtures(self, sample_wiki_page, sample_repo_info, sample_wiki_structure):
        """Test that sample fixtures are created correctly."""
        # Test sample_wiki_page fixture
        assert "id" in sample_wiki_page
        assert "title" in sample_wiki_page
        assert "content" in sample_wiki_page
        assert "filePaths" in sample_wiki_page
        assert "importance" in sample_wiki_page
        assert "relatedPages" in sample_wiki_page
        
        # Test sample_repo_info fixture
        assert "owner" in sample_repo_info
        assert "repo" in sample_repo_info
        assert "type" in sample_repo_info
        
        # Test sample_wiki_structure fixture
        assert "id" in sample_wiki_structure
        assert "title" in sample_wiki_structure
        assert "description" in sample_wiki_structure
        assert "pages" in sample_wiki_structure

    @pytest.mark.unit
    def test_environment_setup(self, setup_test_environment):
        """Test that test environment is set up correctly."""
        import os
        # Verify test environment is configured
        assert os.environ.get("NODE_ENV") == "test"

    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_processed_projects_endpoint(self, async_client: AsyncClient):
        """Test the processed projects endpoint (marked as slow)."""
        response = await async_client.get("/api/processed_projects")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should return empty list initially for test environment


class TestAsyncSupport:
    """Test class specifically for async functionality."""

    @pytest.mark.asyncio
    async def test_async_test_support(self):
        """Test that async tests work correctly."""
        import asyncio
        
        # Simple async operation
        await asyncio.sleep(0.001)  # Very short sleep
        
        # Test async assertion
        result = await self._async_helper()
        assert result == "async_success"

    async def _async_helper(self) -> str:
        """Helper async method for testing."""
        return "async_success"