---
name: setup-api-testing-with-tdd-loop-agent
status: backlog
created: 2025-08-23T16:45:25Z
progress: 0%
prd: .claude/prds/setup-api-testing-with-tdd-loop-agent.md
github: [Will be updated when synced to GitHub]
---

# Epic: setup-api-testing-with-tdd-loop-agent

## Overview
Implement a Test-Driven Development (TDD) approach to identify and fix the critical embedding pipeline bug causing empty vectors in the RAG system. This epic focuses on writing tests FIRST to diagnose the root cause, then applying minimal fixes to make tests pass, all verified in local Docker environment.

## Architecture Decisions

### Testing Framework
- **pytest with pytest-asyncio**: Minimal setup, supports async FastAPI endpoints
- **Real API calls**: No mocks - test actual behavior to find real bugs
- **Local Docker verification**: Tests must pass both locally and in container

### Investigation Strategy
- **Parallel diagnosis**: 3 focused agents investigate different pipeline stages simultaneously
- **Test-first approach**: Write failing tests to understand expected vs actual behavior
- **Minimal fixes**: Only change code that tests prove is broken

### Key Technical Decisions
- Focus on embedding pipeline (rag.py lines 285-295)
- Test google_embedding_client.py batch processing
- Validate vector dimensions before FAISS operations
- No CI/CD automation - local Docker testing only

## Technical Approach

### Core Components to Test
1. **Embedding Client** (google_embedding_client.py)
   - Batch processing logic
   - Error handling and fallback
   - Vector dimension consistency

2. **Vector Validation** (rag.py)
   - Empty vector detection
   - Dimension validation
   - FAISS compatibility checks

3. **Pipeline Integration**
   - Document flow from input to storage
   - Error propagation
   - Failure recovery

### Testing Infrastructure
```python
# Simple test structure focused on the bug
tests/
├── conftest.py              # Shared fixtures
├── test_embedding_client.py # Test vector generation
├── test_vector_validation.py # Test validation logic
└── test_rag_pipeline.py     # End-to-end tests
```

## Implementation Strategy

### Phase 1: Setup (30 minutes)
- Add pytest dependencies to requirements.txt
- Configure pytest.ini for API testing
- Create basic test structure

### Phase 2: Parallel Investigation (2 hours)
- 3 agents work simultaneously on different components
- Each writes tests to isolate failure points
- Document actual vs expected behavior

### Phase 3: Fix & Verify (2 hours)
- Apply minimal fixes based on test results
- Verify locally with pytest
- Rebuild and test in Docker container

## Task Breakdown Preview

- [ ] Task 1: Setup pytest infrastructure and test structure
- [ ] Task 2: Test embedding client for empty vector generation
- [ ] Task 3: Test vector validation and FAISS compatibility
- [ ] Task 4: Test end-to-end pipeline integration
- [ ] Task 5: Implement fixes based on test findings
- [ ] Task 6: Verify solution in Docker environment
- [ ] Task 7: Document testing approach and results

## Dependencies

### External Dependencies
- Google AI API for embeddings (existing)
- FAISS vector database (existing)
- Docker and docker-compose (existing)

### Internal Dependencies
- Access to api/rag.py
- Access to api/google_embedding_client.py
- Docker configuration files

### No New Dependencies Required
- Using existing pytest (just needs to be added to requirements.txt)
- No new services or infrastructure
- No CI/CD setup needed

## Success Criteria (Technical)

### Must Have
- Empty embedding bug fixed (no more errors in rag.py:295)
- All tests passing locally
- All tests passing in Docker container
- Root cause documented

### Performance Targets
- Tests complete in < 5 minutes
- Bug fix verified in < 1 hour
- Total implementation in 6 hours

### Quality Gates
- No regression in existing functionality
- Tests are deterministic (no flaky tests)
- Clear documentation for running tests

## Estimated Effort

### Timeline: 6 hours total
- Setup: 30 minutes
- Parallel investigation: 2 hours
- Fix implementation: 1.5 hours
- Docker verification: 1 hour
- Documentation: 1 hour

### Resource Requirements
- 1 lead developer for setup and coordination
- 3 parallel agents for investigation phase
- Docker environment for testing

### Critical Path
1. Setup testing infrastructure (blocks all other work)
2. Parallel investigation (can be done simultaneously)
3. Fix implementation (depends on investigation)
4. Docker verification (final validation)

## Tasks Created
- [ ] 001.md - Setup pytest infrastructure and test structure (parallel: false)
- [ ] 002.md - Configure test fixtures and API client setup (parallel: false)
- [ ] 003.md - Test embedding client for empty vector generation (parallel: true)
- [ ] 004.md - Test vector validation and FAISS compatibility (parallel: true)
- [ ] 005.md - Test end-to-end pipeline integration (parallel: true)
- [ ] 006.md - Implement fixes based on test findings (parallel: false)
- [ ] 007.md - Verify solution in Docker environment and document (parallel: false)

Total tasks: 7
Parallel tasks: 3
Sequential tasks: 4
Estimated total effort: 9.5 hours