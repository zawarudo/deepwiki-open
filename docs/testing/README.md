# DeepWiki Testing Documentation

Welcome to the DeepWiki testing documentation. This guide covers all aspects of testing the DeepWiki application, from unit tests to end-to-end integration tests.

## 📚 Documentation Structure

- **[Docker Testing Guide](./docker-testing.md)** - Complete guide for testing with Docker
- **[Troubleshooting Guide](./troubleshooting.md)** - Solutions for common Docker build and test issues
- **[Embedding Tests Guide](./embedding-tests.md)** - Documentation for the embedding pipeline tests

## 🧪 Test Organization

Our tests are organized into the following categories:

### Unit Tests (`test/unit/`)
Small, focused tests for individual functions and components:
- `test_extract_repo_name.py` - Repository name extraction logic
- `test_lang_config.py` - Language configuration API endpoint

### Integration Tests (`test/integration/`)
Tests that verify multiple components working together:
- `test_e2e_embedding_pipeline.py` - End-to-end embedding pipeline validation
- `test_generate_wiki_flow.py` - Complete wiki generation workflow

### Embedding Tests (`test/embeddings/`)
Specialized tests for the embedding pipeline fixes:
- `test_empty_embedding_validation.py` - Empty vector prevention (Task 001)
- `test_dimension_consistency.py` - 768-dimension validation (Task 003)
- `test_batch_retry_logic.py` - Exponential backoff retry (Task 005)
- `test_error_reporting.py` - Enhanced error messages (Task 007)
- `test_emergency_fix.py` - Emergency fix validation (Task 000)

## 🚀 Quick Start

### Running All Tests
```bash
# Run all tests
pytest test/

# Run with coverage
pytest test/ --cov=api --cov-report=html

# Run specific category
pytest test/unit/           # Unit tests only
pytest test/integration/    # Integration tests only
pytest test/embeddings/     # Embedding tests only
```

### Running Tests in Docker
```bash
# Use the test pipeline script
./docker/scripts/test-pipeline.sh

# Or use docker-compose
docker-compose -f docker/compose/test.yml up
```

## 🛠️ Testing Scripts

### Docker Testing Scripts (`scripts/docker/`)
- `monitor_docker_logs.sh` - Real-time Docker log monitoring
- `validate_docker_pipeline.py` - Validate embedding pipeline fixes in Docker

### Testing Utilities (`scripts/testing/`)
- `run_e2e_tests.sh` - End-to-end test runner
- `test_faiss_index.py` - FAISS index validation

### Validation Scripts (`scripts/validation/`)
- `validate_embeddings.py` - Embedding validation utilities
- `monitor_embeddings.py` - Real-time embedding monitoring

## 📊 Test Coverage Goals

We aim for the following test coverage:

- **Unit Tests**: >90% coverage of core functions
- **Integration Tests**: All major workflows covered
- **API Tests**: All endpoints tested
- **Embedding Pipeline**: 100% coverage of critical paths

## 🔍 Testing Best Practices

1. **No Mocking for Integration Tests** - Use real services for accurate results
2. **Verbose Output** - Capture full stack traces for debugging
3. **Test Structure First** - Check test structure before assuming code bugs
4. **Clean Up** - Always clean up resources after tests
5. **Isolated Tests** - Each test should be independent

## 🐛 Debugging Tests

### Common Issues and Solutions

1. **Permission Errors**
   - Solution: Mock logging infrastructure (see `test_lang_config.py`)

2. **Slow Docker Builds**
   - Solution: Use BuildKit and optimized Dockerfile
   - See [Troubleshooting Guide](./troubleshooting.md)

3. **Empty Vector Errors**
   - Solution: Run embedding validation tests
   - See [Embedding Tests Guide](./embedding-tests.md)

## 📈 Continuous Integration

Tests are automatically run on:
- Every push to main branch
- All pull requests
- Nightly builds

## 🤝 Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add integration tests for new workflows
4. Update this documentation

## 📞 Support

For test-related issues:
1. Check the [Troubleshooting Guide](./troubleshooting.md)
2. Review test output carefully
3. Run tests with `-v` flag for verbose output
4. Check Docker logs if using containers