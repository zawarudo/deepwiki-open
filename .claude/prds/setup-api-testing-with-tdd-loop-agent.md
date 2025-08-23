---
name: setup-api-testing-with-tdd-loop-agent
status: draft
created: 2025-08-23T15:00:00Z
updated: 2025-08-23T16:37:56Z
---

# API Testing Pipeline with TDD Loop PRD

## WHY
We have an API bug in api.rag, however we want to fix the source of the problem not the symptom.
We need to introduce a testing pipeline that tests key points of the earlier steps of this pipeline.
We need to introduce a testing framework that we can setup and start with quickly, but meets standard testing framework requirements.

### Bug needed to identify root cause
Enough to identify and fix the embedding pipeline bug in rag.py
--- Key error we should work from first principles of the pipeline to arrive at a clear solution.
2025-08-23 23:12:31 api-1  | 2025-08-23 15:12:31,569 - WARNING - api.rag - rag.py:285 - Document 921 has empty embedding vector, skipping
2025-08-23 23:12:31 api-1  | 2025-08-23 15:12:31,569 - WARNING - api.rag - rag.py:285 - Document 922 has empty embedding vector, skipping
2025-08-23 23:12:31 api-1  | 2025-08-23 15:12:31,569 - ERROR - api.rag - rag.py:295 - No valid embeddings found in any documents
2025-08-23 23:12:31 api-1  | 2025-08-23 15:12:31,569 - ERROR - api.websocket_wiki - websocket_wiki.py:102 - No valid embeddings found: No valid documents with embeddings found after validation. This usually indicates the embedder returned empty vectors or mismatched dimensions. Rebuild the database or adjust embedder settings.
---

## Executive Summary
**TEST-DRIVEN APPROACH**: Write tests FIRST to identify the root cause of empty embeddings, then fix the code to make tests pass. This PRD prioritizes parallel test creation and research to understand the pipeline failure points BEFORE touching any production code.

## Goals and Objectives
1. **Write tests first** to reproduce the empty embedding bug
2. **Identify root cause** through systematic test-driven investigation
3. **Fix only what tests prove is broken** - no speculative fixes
4. **Parallelize test creation** to speed up root cause analysis

## Technical Requirements (TDD-First)

### 1. Test Structure for Pipeline Investigation
```
tests/
├── test_1_git_ingestion.py     # Test: Can we read repo files?
├── test_2_content_extraction.py # Test: Is content extracted correctly?
├── test_3_embedding_client.py   # Test: Are embeddings generated?
├── test_4_vector_validation.py  # Test: Are vectors valid dimensions?
├── test_5_rag_storage.py       # Test: Does FAISS accept vectors?
└── conftest.py                  # Shared test fixtures
```

### 2. Parallel Test Creation Strategy
```python
# Each test investigates a pipeline stage INDEPENDENTLY
# Run all in parallel to quickly identify failure point

def test_pipeline_stage_X():
    """Test specific stage to isolate where empty vectors originate"""
    # RED: Write failing test that expects correct behavior
    # Investigation: Run test to see actual vs expected
    # Root Cause: Document why this stage fails
```

### 3. Test-Driven Investigation Process
1. **Write tests for each pipeline stage** (before looking at code)
2. **Run tests in parallel** to see where pipeline breaks
3. **Document failures** to understand root cause
4. **Only then fix code** to make tests pass

## Implementation Strategy (TDD-First)

### Phase 1: Setup & Parallel Test Creation (Hour 1-2)
1. Install pytest and pytest-asyncio
2. Launch parallel agents to create tests for each pipeline stage
3. Each agent investigates one stage independently
4. No code fixes yet - only test creation

### Phase 2: Run Tests & Identify Root Cause (Hour 3-4)
1. Run all tests to see failure patterns
2. Analyze which pipeline stage(s) produce empty vectors
3. Document exact failure points with test evidence
4. Create hypothesis for root cause

### Phase 3: Fix Code to Pass Tests (Hour 5-6)
1. Fix ONLY the code that tests prove is broken
2. Re-run tests to verify fixes
3. Add regression tests for edge cases
4. Commit when all tests green

## Testing Framework Selection

### Framework: pytest (minimal setup)
```bash
# Only what we need
pip install pytest pytest-asyncio

# No complex plugins needed initially
```

## Risk Mitigation (Minimal)

### Risks & Simple Solutions
- **Risk**: Over-engineering the solution
  - **Solution**: Stay focused on the bug, add only essential tests
- **Risk**: Complex test infrastructure delays fix
  - **Solution**: Fix bug first, then add tests
- **Risk**: Tests become flaky
  - **Solution**: Use real services, no complex mocks

## Task List (TDD-First, Parallelizable)

### Task 001: Setup pytest Infrastructure (Priority: Critical, 30 min)
- Add pytest, pytest-asyncio to requirements.txt
- Configure pytest.ini for parallel execution
- Create test directory structure
- **Deliverable**: `pytest` command ready

### Parallel Test Creation Tasks (Can run simultaneously):

### Task 002: Test Git Ingestion Stage (Priority: Critical)
- Write test for repository file reading
- Test with sample repo structure
- Verify files are accessible
- **Deliverable**: test_1_git_ingestion.py

### Task 003: Test Content Extraction Stage (Priority: Critical)
- Write test for content parsing
- Test with various file types
- Verify content is extracted
- **Deliverable**: test_2_content_extraction.py

### Task 004: Test Embedding Client Stage (Priority: Critical)
- Write test for embedding generation
- Test with sample documents
- Verify vectors are created with correct dimensions
- **Deliverable**: test_3_embedding_client.py

### Task 005: Test Vector Validation Stage (Priority: Critical)
- Write test for vector dimension checking
- Test empty vector handling
- Verify validation catches bad vectors
- **Deliverable**: test_4_vector_validation.py

### Task 006: Test RAG Storage Stage (Priority: Critical)
- Write test for FAISS operations
- Test with valid and invalid vectors
- Verify storage handles edge cases
- **Deliverable**: test_5_rag_storage.py

### Sequential Tasks (After parallel tests complete):

### Task 007: Run All Tests & Analyze Failures (Priority: Critical)
- Execute full test suite
- Document which stages fail
- Identify root cause from test results
- **Deliverable**: Root cause analysis document

### Task 008: Fix Code Based on Test Results (Priority: Critical)
- Fix ONLY what tests identify as broken
- No speculative changes
- Re-run tests to verify
- **Deliverable**: All tests passing

### Task 009: Add CI/CD Testing (Priority: High)
- Add test step to GitHub Actions
- Run tests before Docker build
- **Deliverable**: Automated testing on push

## Success Metrics (TDD-Focused)
1. **Tests Written First**: All tests created before code changes
2. **Root Cause Identified**: Tests pinpoint exact failure stage
3. **Bug Fixed**: Tests pass after minimal code changes
4. **Time to Complete**: 6 hours with parallel execution

## What We're NOT Doing
- ❌ Complex test data management
- ❌ AI-driven test generation  
- ❌ Parallel test execution
- ❌ Performance benchmarking
- ❌ 100% coverage targets
- ❌ Service mocking layers
- ❌ Multiple testing frameworks

## Next Steps (TDD Workflow)
1. Setup pytest infrastructure (30 min)
2. Launch 5 parallel agents to create pipeline tests (1 hour)
3. Run all tests to identify failure points (30 min)
4. Fix only what tests prove is broken (1 hour)
5. Ship it with confidence