---
name: fix-api-pipeline-errors
status: backlog
created: 2025-08-23T07:59:26Z
updated: 2025-08-23T12:27:40Z
progress: 0%
prd: .claude/prds/fix-api-pipeline-errors.md
github: [Will be updated when synced to GitHub]
---

# Epic: fix-api-pipeline-errors

## Overview
Fix critical embedding validation failures causing "No valid document embeddings found" error at api/websocket_wiki.py:102. The root cause is GoogleEmbeddingClient silently returning empty embedding vectors `[]` for failed requests, creating dimension mismatches when mixed with successful 768-dimensional embeddings. This causes FAISS retriever initialization to fail completely.

**Root Cause Analysis**: 
- GoogleEmbeddingClient appends empty arrays `[]` on API failures (lines 119, 128, 144)
- These empty embeddings mix with valid 768-dimensional vectors
- FAISS validation rejects the inconsistent embedding dimensions
- System fails with "No valid document embeddings found"

## Architecture Decisions

### Test-Driven Development (TDD) Approach
- **Red Phase**: Write failing tests that reproduce the exact error conditions
- **Green Phase**: Implement minimal fixes to make tests pass
- **Refactor Phase**: Optimize and clean up while maintaining test coverage
- **Fast Feedback Loop**: Create immediate test harness for rapid iteration

### Key Technical Decisions
- **Fail Fast**: Stop appending empty embeddings; skip or retry failed documents
- **Validation Layer**: Pre-validate embeddings before FAISS initialization
- **Explicit Error Handling**: Return detailed failure information instead of silent failures
- **Incremental Fixes**: Small, testable changes with immediate verification

### Technology Choices
- **Testing**: pytest with async support for testing embedding pipeline
- **Monitoring**: Enhanced logging at each embedding stage
- **Existing Stack**: Keep google-cloud-aiplatform, FAISS, adalflow

## Technical Approach

### Test-Driven Development Methodology

**1. Create Failing Test Suite (`test_embedding_validation.py`)**
```python
# Test 1: Verify empty embeddings are NOT added to results
# Test 2: Verify all embeddings have consistent dimensions
# Test 3: Verify batch failures trigger retry logic
# Test 4: Verify partial batch success is handled correctly
# Test 5: Verify error messages are informative
```

**2. Fix GoogleEmbeddingClient (`api/google_embedding_client.py`)**
- Line 119: Skip document instead of appending empty embedding
- Line 128: Log error and skip instead of appending empty
- Line 144: Implement retry for missing batch responses
- Add dimension validation before returning results

**3. Add Validation Layer (`api/data_pipeline.py`)**
- Post-embedding validation at line 460
- Filter documents with invalid embeddings
- Log statistics: total/successful/failed documents

**4. Improve Error Reporting**
- Return EmbedderOutput with failed_indices field
- Provide specific failure reasons per document
- Surface actionable error messages to users

### Fast Feedback Loop Setup

**Test Command Pipeline**:
```bash
# 1. Unit test for embedding validation
pytest test_embedding_validation.py -v

# 2. Integration test with real API
python test_batch_embedding.py

# 3. End-to-end test with actual repository
./verify_embedding_fix.sh <test_repo_url>
```

## Implementation Strategy

### TDD Cycle Phases
1. **Cycle 1 - Empty Embedding Fix (2 hours)**
   - Write test for empty embedding detection
   - Fix GoogleEmbeddingClient to skip failures
   - Verify test passes

2. **Cycle 2 - Dimension Validation (2 hours)**
   - Write test for dimension consistency
   - Add validation layer in data_pipeline
   - Verify all embeddings have same dimensions

3. **Cycle 3 - Retry Logic (3 hours)**
   - Write test for batch retry scenarios
   - Implement exponential backoff retry
   - Verify resilience to transient failures

4. **Cycle 4 - Error Reporting (2 hours)**
   - Write test for error message clarity
   - Enhance error messages and logging
   - Verify user gets actionable feedback

### Risk Mitigation
- **Test First**: Every fix has a test before implementation
- **Incremental Changes**: One fix per commit, verifiable independently
- **Rollback Plan**: Each change can be reverted without affecting others

## Task Breakdown Preview

Test-driven development tasks with clear red-green-refactor cycles:

- [ ] **Task 1**: Write failing test for empty embedding validation
- [ ] **Task 2**: Fix GoogleEmbeddingClient to skip empty embeddings (make test pass)
- [ ] **Task 3**: Write failing test for dimension consistency validation
- [ ] **Task 4**: Add embedding dimension validator (make test pass)
- [ ] **Task 5**: Write failing test for batch retry logic
- [ ] **Task 6**: Implement retry with exponential backoff (make test pass)
- [ ] **Task 7**: Write failing test for error reporting
- [ ] **Task 8**: Enhance error messages and logging (make test pass)
- [ ] **Task 9**: Create end-to-end test script
- [ ] **Task 10**: Run full test suite and document results

## Dependencies

### External Service Dependencies
- Google Vertex AI API for testing actual embeddings
- Test repository with known content for validation

### Testing Infrastructure
- pytest with async support
- Access to Google API with test credentials
- Sample documents for embedding tests

## Success Criteria (Technical)

### Test Coverage Requirements
- 100% test coverage for modified code paths
- All tests passing in < 5 seconds (unit tests)
- Integration tests passing in < 30 seconds

### Performance Benchmarks
- Zero empty embeddings in output
- 100% dimension consistency in embeddings
- < 2% permanent failure rate (after retries)
- Clear error messages for all failure modes

### Quality Gates
- All existing tests still passing
- New tests cover all edge cases
- No regression in working functionality
- Error messages actionable by users

## Estimated Effort

### Overall Timeline
- **Total Duration**: 2-3 days with TDD approach
- **Test Creation**: 40% of effort
- **Implementation**: 30% of effort  
- **Validation**: 30% of effort

### Critical Path Items
1. Create reproducing test (Hour 1)
2. Fix empty embedding bug (Hour 2-3)
3. Add validation layer (Hour 4-5)
4. Implement retry logic (Day 2)
5. Full test suite validation (Day 3)

## Fast Feedback Commands

```bash
# Quick test for embedding validation
python -c "from api.google_embedding_client import GoogleEmbeddingClient; 
client = GoogleEmbeddingClient(); 
# Test with known failing case"

# Check for empty embeddings in output
python test_batch_embedding.py 2>&1 | grep -E "embedding.*\[\]|dimension"

# Verify fix with actual pipeline
./verify_embedding_fix.sh
```

## Tasks Created
- [ ] 001.md - Write failing test for empty embedding validation (parallel: false)
- [ ] 002.md - Fix GoogleEmbeddingClient to skip empty embeddings (parallel: false)
- [ ] 003.md - Write failing test for dimension consistency (parallel: false)
- [ ] 004.md - Add embedding dimension validator (parallel: false)
- [ ] 005.md - Write failing test for batch retry logic (parallel: false)
- [ ] 006.md - Implement retry with exponential backoff (parallel: false)
- [ ] 007.md - Write failing test for error reporting (parallel: false)
- [ ] 008.md - Enhance error messages and logging (parallel: false)
- [ ] 009.md - Create end-to-end test script (parallel: false)
- [ ] 010.md - Run full test suite and document results (parallel: false)

Total tasks: 10
Parallel tasks: 0 (TDD requires sequential execution)
Sequential tasks: 10
Estimated total effort: 16 hours