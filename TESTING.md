# DeepWiki Testing Guide

Welcome to the DeepWiki testing documentation. This guide provides an overview of our testing infrastructure and links to detailed documentation.

## 🚀 Quick Start

### Run All Tests
```bash
# Local testing
pytest test/

# Docker testing
./docker/scripts/test-pipeline.sh
```

### Run Specific Test Categories
```bash
# Unit tests
pytest test/unit/

# Integration tests
pytest test/integration/

# Embedding pipeline tests
pytest test/embeddings/
```

## 📚 Documentation Structure

Our testing documentation is organized as follows:

### Main Testing Documentation (`docs/testing/`)
- **[Complete Testing Guide](docs/testing/README.md)** - Comprehensive testing documentation
- **[Docker Testing Guide](docs/testing/docker-testing.md)** - Testing with Docker containers
- **[Troubleshooting Guide](docs/testing/troubleshooting.md)** - Solutions for common issues
- **[Embedding Tests Guide](docs/testing/embedding-tests.md)** - Embedding pipeline test documentation

### Test Organization (`test/`)
- **[Test Directory Guide](test/README.md)** - How tests are organized
- `test/unit/` - Unit tests for individual components
- `test/integration/` - Integration tests for workflows
- `test/embeddings/` - Embedding pipeline tests
- `test/fixtures/` - Shared test data and mocks

### Testing Scripts (`scripts/`)
- **[Scripts Guide](scripts/README.md)** - Available testing scripts
- `scripts/docker/` - Docker testing utilities
- `scripts/testing/` - Test execution scripts
- `scripts/validation/` - Validation utilities

### Docker Testing (`docker/`)
- **[Docker Guide](docker/README.md)** - Docker configurations and scripts
- `docker/scripts/` - Docker test execution scripts
- `docker/compose/` - Docker compose configurations

## 🧪 Test Coverage

### Current Coverage
- **Embedding Pipeline**: 100% critical path coverage (70+ tests)
- **API Endpoints**: All major endpoints tested
- **Core Functions**: >90% unit test coverage
- **Integration**: All major workflows covered

### Check Coverage
```bash
# Generate coverage report
pytest test/ --cov=api --cov-report=html

# View report
open htmlcov/index.html
```

## 🏃 Testing Workflows

### 1. Local Development Testing
```bash
# Install dependencies
pip install -r api/requirements.txt

# Run tests
pytest test/ -v

# Run with coverage
pytest test/ --cov=api
```

### 2. Docker Testing
```bash
# Build and test
./docker/scripts/test-pipeline.sh

# Monitor tests
./scripts/docker/monitor_docker_logs.sh
```

### 3. Continuous Integration
Tests run automatically on:
- Pull requests
- Pushes to main branch
- Nightly builds

## 🔍 Test Categories

### Embedding Pipeline Tests
Critical tests for FAISS compatibility and embedding generation:
- Empty vector prevention
- Dimension consistency (768-dim)
- Retry logic with exponential backoff
- Enhanced error reporting
- End-to-end pipeline validation

### API Tests
- Language configuration endpoint
- Wiki generation workflow
- WebSocket connections
- Health checks

### Utility Tests
- Repository name extraction
- URL validation
- Data transformation

## 📝 Writing Tests

### Follow TDD Approach
1. **RED** - Write failing test
2. **GREEN** - Implement minimal code to pass
3. **REFACTOR** - Improve code while keeping tests green

### Test Structure
```python
def test_feature():
    # Arrange
    test_data = create_test_data()
    
    # Act
    result = function_under_test(test_data)
    
    # Assert
    assert result == expected_value
```

## 🐛 Debugging

### Verbose Output
```bash
pytest test/ -vv --tb=long
```

### Run Specific Test
```bash
pytest test/unit/test_lang_config.py::test_function -v
```

### Docker Debugging
```bash
# View container logs
docker-compose logs -f

# Execute tests in container
docker-compose exec deepwiki pytest test/ -v
```

## 📊 Performance Benchmarks

- All unit tests: <5 seconds
- Integration tests: <30 seconds
- Full test suite: <2 minutes
- Docker test pipeline: <5 minutes

## 🤝 Contributing

When contributing:
1. Write tests for new features
2. Ensure all tests pass
3. Maintain >90% coverage
4. Update documentation

## 📞 Support

For testing issues:
1. Check [Troubleshooting Guide](docs/testing/troubleshooting.md)
2. Review test output carefully
3. Check Docker logs if applicable
4. Open an issue with test details

## 🔗 Quick Links

- [Main README](README.md)
- [Testing Documentation](docs/testing/README.md)
- [Docker Testing](docs/testing/docker-testing.md)
- [Embedding Tests](docs/testing/embedding-tests.md)
- [Test Organization](test/README.md)
- [Scripts Guide](scripts/README.md)