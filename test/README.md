# Test Directory

This directory contains all tests for the DeepWiki application, organized by test type and component.

## 📁 Test Organization

### `unit/` - Unit Tests
Fast, isolated tests for individual functions and components:
- **`test_extract_repo_name.py`** - Tests for repository name extraction logic
- **`test_lang_config.py`** - Tests for language configuration API endpoint

### `integration/` - Integration Tests
Tests that verify multiple components working together:
- **`test_e2e_embedding_pipeline.py`** - End-to-end embedding pipeline validation
- **`test_generate_wiki_flow.py`** - Complete wiki generation workflow testing

### `embeddings/` - Embedding Pipeline Tests
Specialized tests for the embedding pipeline fixes from the `fix-api-pipeline-errors` epic:
- **`test_emergency_fix.py`** - Emergency fix validation (Task 000)
- **`test_empty_embedding_validation.py`** - Empty vector prevention tests (Task 001)
- **`test_dimension_consistency.py`** - 768-dimension validation tests (Task 003)
- **`test_batch_retry_logic.py`** - Exponential backoff retry tests (Task 005)
- **`test_error_reporting.py`** - Enhanced error message tests (Task 007)

### `fixtures/` - Test Fixtures
Shared test data and mock objects used across multiple tests.

## 🚀 Running Tests

### Run All Tests
```bash
# Run all tests with pytest
pytest test/

# Run with verbose output
pytest test/ -v

# Run with coverage report
pytest test/ --cov=api --cov-report=html
```

### Run Tests by Category
```bash
# Unit tests only
pytest test/unit/

# Integration tests only
pytest test/integration/

# Embedding tests only
pytest test/embeddings/
```

### Run Specific Test Files
```bash
# Run a specific test file
pytest test/unit/test_lang_config.py -v

# Run tests matching a pattern
pytest test/ -k "embedding" -v
```

### Run Tests in Docker
```bash
# Using docker-compose
docker-compose exec deepwiki pytest test/

# Using the test script
./docker/scripts/test-pipeline.sh
```

## 📊 Test Coverage

Current test coverage goals:
- **Unit Tests**: >90% coverage
- **Integration Tests**: All major workflows
- **Embedding Pipeline**: 100% of critical paths

Check coverage:
```bash
# Generate coverage report
pytest test/ --cov=api --cov-report=term-missing

# Generate HTML coverage report
pytest test/ --cov=api --cov-report=html
# Open htmlcov/index.html in browser
```

## 🧪 Test Conventions

### Naming Conventions
- Test files: `test_<component>.py`
- Test classes: `Test<Component>`
- Test methods: `test_<what_is_being_tested>`

### Test Structure
```python
def test_example():
    # Arrange - Set up test data
    input_data = create_test_data()
    
    # Act - Execute the function
    result = function_under_test(input_data)
    
    # Assert - Verify the result
    assert result == expected_value
```

### Fixtures
Common fixtures are available in `conftest.py`:
- `client` - Test client for API testing
- `mock_embeddings` - Mock embedding responses
- `sample_documents` - Sample document data

## 🐛 Debugging Failed Tests

### Verbose Output
```bash
# Show detailed test output
pytest test/ -vv

# Show print statements
pytest test/ -s

# Show full traceback
pytest test/ --tb=long
```

### Run Specific Test
```bash
# Run a single test method
pytest test/unit/test_lang_config.py::TestLangConfig::test_endpoint -v
```

### Debug with pdb
```python
# Add breakpoint in test
import pdb; pdb.set_trace()
```

## 📝 Writing New Tests

### 1. Choose the Right Directory
- Unit test → `test/unit/`
- Integration test → `test/integration/`
- Embedding-related → `test/embeddings/`

### 2. Follow TDD Approach
1. Write a failing test (RED)
2. Implement minimal code to pass (GREEN)
3. Refactor while keeping tests passing (REFACTOR)

### 3. Use Appropriate Assertions
```python
# Basic assertions
assert result == expected
assert error_occurred is False
assert len(items) > 0

# With pytest
import pytest
with pytest.raises(ValueError):
    invalid_function_call()
```

### 4. Mock External Dependencies
```python
from unittest.mock import Mock, patch

@patch('api.external_service')
def test_with_mock(mock_service):
    mock_service.return_value = 'mocked response'
    # Test code here
```

## 🔧 Test Configuration

### pytest.ini
Configuration is in the root `pytest.ini` file:
```ini
[pytest]
testpaths = test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Environment Variables
Set test environment variables:
```bash
# Use mock embeddings for testing
USE_MOCK_EMBEDDINGS=true pytest test/

# Set test API keys
OPENAI_API_KEY=test_key pytest test/
```

## 📚 Related Documentation

- [Testing Guide](../docs/testing/README.md)
- [Embedding Tests Guide](../docs/testing/embedding-tests.md)
- [Docker Testing Guide](../docs/testing/docker-testing.md)