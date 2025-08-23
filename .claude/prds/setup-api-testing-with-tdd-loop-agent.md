---
name: setup-api-testing-with-tdd-loop-agent
status: draft
created: 2025-08-23T15:00:00Z
updated: 2025-08-23T16:33:46Z
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
**PRAGMATIC APPROACH**: Fix the critical embedding bug first, then implement minimal testing infrastructure to prevent regression. This PRD focuses on delivering immediate value with the smallest possible implementation that solves the actual problem.

## Goals and Objectives
1. **Fix the embedding bug** causing empty vectors in rag.py
2. **Prevent regression** with minimal test coverage
3. **Enable CI/CD testing** to catch bugs before production
4. **Keep it simple** - no over-engineering

## Technical Requirements (Simplified)

### 1. Minimal Testing Structure
```
tests/
├── test_embedding_pipeline.py  # Focus on the bug
├── test_rag.py                 # Test empty vector handling
└── conftest.py                 # Basic pytest setup
```

### 2. Core Testing Focus
```python
# Only test what's broken
def test_empty_embedding_handling():
    """Verify system handles empty embeddings gracefully"""
    
def test_embedding_generation():
    """Ensure embeddings are actually generated"""
    
def test_vector_validation():
    """Check dimensions before FAISS operations"""
```

### 3. No Complex Infrastructure
- Use real API calls (no mocks)
- Simple test data (3-5 sample documents)
- Direct testing of actual bug scenario
- Focus on rag.py lines 285-295

## Implementation Strategy (Pragmatic)

### Phase 1: Fix the Bug (Day 1)
1. Debug why embeddings are empty
2. Add validation before FAISS operations
3. Write test to verify fix

### Phase 2: Basic Testing (Day 2-3)
1. Install pytest and pytest-asyncio
2. Create 5-10 tests for embedding pipeline
3. Test the specific bug scenario

### Phase 3: CI/CD Integration (Day 4)
1. Add test step to GitHub Actions
2. Run tests before Docker build
3. Block deployment on test failure

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

## Task List (Lean & Pragmatic)

### Task 001: Fix Empty Embedding Bug (Priority: Critical)
- Debug why embeddings are empty in rag.py
- Add validation before FAISS operations
- Implement proper error handling
- **Deliverable**: No more crashes from empty vectors

### Task 002: Create Minimal Test Suite (Priority: High)
- Write 3-5 tests for embedding generation
- Test empty vector scenario explicitly
- Use real API calls (no mocks)
- **Deliverable**: Tests that catch the bug

### Task 003: Setup pytest Infrastructure (Priority: High)
- Add pytest, pytest-asyncio to requirements.txt
- Configure pytest.ini
- Create test directory structure
- **Deliverable**: `pytest` command works

### Task 004: Test Critical Path (Priority: Medium)
- Test: Git repo → Content → Embeddings → Storage
- Focus on happy path + bug scenario
- **Deliverable**: Core pipeline has test coverage

### Task 005: Add CI/CD Testing (Priority: Medium)
- Add test step to GitHub Actions
- Fail deployment if tests fail
- **Deliverable**: Automated testing on every push

## Success Metrics (Simplified)
1. **Bug Fixed**: No more empty embedding errors
2. **Tests Pass**: 5-10 tests covering the bug scenario
3. **CI/CD Works**: Tests run automatically on push
4. **Time to Complete**: 1 week maximum

## What We're NOT Doing
- ❌ Complex test data management
- ❌ AI-driven test generation  
- ❌ Parallel test execution
- ❌ Performance benchmarking
- ❌ 100% coverage targets
- ❌ Service mocking layers
- ❌ Multiple testing frameworks

## Next Steps
1. Fix the embedding bug in rag.py
2. Add pytest to requirements.txt
3. Write 5 focused tests
4. Add test step to GitHub Actions
5. Ship it