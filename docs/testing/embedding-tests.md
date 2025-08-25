# Embedding Pipeline Tests Documentation

This document describes the comprehensive test suite for the embedding pipeline fixes implemented in the `fix-api-pipeline-errors` epic.

## 📋 Overview

The embedding pipeline tests validate critical fixes that prevent FAISS crashes and ensure reliable document embedding generation. These tests follow Test-Driven Development (TDD) methodology with RED-GREEN-REFACTOR cycles.

## 🧪 Test Suite Structure

All embedding tests are located in `test/embeddings/`:

### 1. Emergency Fix Test (`test_emergency_fix.py`)
**Purpose**: Validates the emergency fix that prevents empty vector creation

**Key Tests**:
- `test_no_empty_vectors_on_api_failure` - Ensures API failures don't create empty vectors
- `test_correct_model_name_default` - Verifies correct model name (text-embedding-004)
- `test_dimension_validation` - Validates all embeddings are 768-dimensional
- `test_large_batch_chunking` - Handles batches larger than 128 texts

**Run**: 
```bash
pytest test/embeddings/test_emergency_fix.py -v
```

### 2. Empty Embedding Validation (`test_empty_embedding_validation.py`)
**Purpose**: Comprehensive validation that no empty vectors are created

**Key Tests** (17 total):
- API failure handling
- Network timeout handling
- Batch processing with partial failures
- JSON parsing error handling
- Edge cases (empty input, unicode, long text)

**TDD Phase**: RED → GREEN (Task 001 → Task 002)

**Run**:
```bash
pytest test/embeddings/test_empty_embedding_validation.py -v
```

### 3. Dimension Consistency (`test_dimension_consistency.py`)
**Purpose**: Ensures all embeddings maintain consistent 768 dimensions

**Key Tests** (11 total):
- All embeddings have exactly 768 dimensions
- Mixed dimensions are detected and rejected
- Validation occurs before FAISS initialization
- Clear error messages for dimension mismatches

**TDD Phase**: RED → GREEN (Task 003 → Task 004)

**Run**:
```bash
pytest test/embeddings/test_dimension_consistency.py -v
```

### 4. Batch Retry Logic (`test_batch_retry_logic.py`)
**Purpose**: Validates exponential backoff retry mechanism

**Key Tests** (11 total):
- Transient failures trigger retries
- Exponential backoff timing (1, 2, 4, 8 seconds)
- Max retry limit enforcement (default: 3)
- Partial batch success preservation
- Rate limit (429) handling with Retry-After header

**TDD Phase**: RED → GREEN (Task 005 → Task 006)

**Run**:
```bash
pytest test/embeddings/test_batch_retry_logic.py -v
```

### 5. Error Reporting (`test_error_reporting.py`)
**Purpose**: Validates enhanced error reporting with document identification

**Key Tests** (11 total):
- Error messages include document information
- Specific failure reason categorization
- Batch failure summaries
- Actionable error guidance

**TDD Phase**: RED → GREEN (Task 007 → Task 008)

**Run**:
```bash
pytest test/embeddings/test_error_reporting.py -v
```

## 🎯 Critical Issues Addressed

| Issue | Test Coverage | Status |
|-------|--------------|--------|
| Empty vectors causing FAISS crashes | `test_empty_embedding_validation.py` | ✅ Fixed |
| Wrong model name (embedding-001) | `test_emergency_fix.py` | ✅ Fixed |
| Dimension inconsistency | `test_dimension_consistency.py` | ✅ Fixed |
| No retry logic for transient failures | `test_batch_retry_logic.py` | ✅ Fixed |
| Generic error messages | `test_error_reporting.py` | ✅ Fixed |

## 🏃 Running the Test Suite

### Run All Embedding Tests
```bash
# Run all embedding tests
pytest test/embeddings/ -v

# With coverage report
pytest test/embeddings/ --cov=api.google_embedding_client --cov=api.data_pipeline

# Run in parallel for speed
pytest test/embeddings/ -n auto
```

### Run Specific Test Categories
```bash
# Only validation tests
pytest test/embeddings/test_*_validation.py -v

# Only retry and error tests
pytest test/embeddings/test_*_retry*.py test/embeddings/test_*error*.py -v
```

### Docker Testing
```bash
# Run in Docker container
docker-compose exec deepwiki pytest test/embeddings/ -v

# Or use the test script
./docker/scripts/test-pipeline.sh
```

## 📊 Test Metrics

### Coverage Goals
- `api/google_embedding_client.py`: >95% coverage
- `api/data_pipeline.py`: >90% coverage
- `api/embedding_errors.py`: 100% coverage

### Performance Benchmarks
- All tests should complete in <30 seconds
- Individual test files should complete in <5 seconds
- Mock mode tests should complete in <2 seconds

## 🔍 Validation Checklist

Before deployment, ensure:

- [ ] All 70+ embedding tests pass
- [ ] No `append([])` statements in code
- [ ] Model name is "text-embedding-004"
- [ ] All embeddings validated for 768 dimensions
- [ ] Retry logic with exponential backoff implemented
- [ ] Error messages include document identification
- [ ] FAISS index creation succeeds 100% of the time

## 🐛 Debugging Failed Tests

### Common Issues

1. **Import Errors**
   ```python
   # Ensure api directory is in path
   import sys
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   ```

2. **Mock vs Real API**
   ```bash
   # Use mock for testing without API keys
   USE_MOCK_EMBEDDINGS=true pytest test/embeddings/
   ```

3. **Dimension Validation Failures**
   - Check `_validate_embedding()` method exists
   - Verify 768 dimension requirement

4. **Retry Logic Not Triggering**
   - Check exponential_backoff_retry decorator
   - Verify error classification (retryable vs permanent)

## 📈 Test Results History

### Summary from Epic Completion
- **Total Tests**: 70+
- **Pass Rate**: 100%
- **Critical Fixes**: 5/5 validated
- **TDD Cycles**: 5 complete (RED-GREEN)
- **Production Ready**: ✅

## 🚀 Next Steps

1. **Maintain Test Coverage** - Keep tests updated with code changes
2. **Add Performance Tests** - Benchmark embedding generation speed
3. **Add Load Tests** - Validate system under high load
4. **Monitor Production** - Track metrics matching test assertions

## 📚 Related Documentation

- [Main Testing Guide](./README.md)
- [Docker Testing Guide](./docker-testing.md)
- [Troubleshooting Guide](./troubleshooting.md)
- Epic Documentation: `.claude/epics/fix-api-pipeline-errors/`