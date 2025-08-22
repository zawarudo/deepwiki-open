import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture()
def app_client(monkeypatch):
    # Create a temporary directory for logs
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "application.log")
        
        # Mock the logging setup to avoid permission issues
        def mock_setup_logging():
            pass
        
        # Patch the setup_logging function before importing
        import api.logging_config
        monkeypatch.setattr(api.logging_config, "setup_logging", mock_setup_logging)
        
        # Now import the API module
        import api.api as api_main
        return TestClient(api_main.app)


def test_lang_config_endpoint(app_client: TestClient):
    """Test that /api/lang/config endpoint returns expected language configuration."""
    
    resp = app_client.get("/lang/config")
    assert resp.status_code == 200
    
    data = resp.json()
    
    # Check that we have a valid response structure
    assert isinstance(data, dict)
    
    # Check for expected fields based on the actual config structure
    assert "supported_languages" in data
    assert "default" in data
    
    # Verify the supported_languages is a dict
    assert isinstance(data["supported_languages"], dict)
    
    # Check that we have at least English support
    assert "en" in data["supported_languages"]
    assert data["supported_languages"]["en"] == "English"
    
    # Check that default language is set
    assert data["default"] == "en"
    
    print(f"Language config response: {data}")