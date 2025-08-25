---
issue: 000
title: EMERGENCY FIX - Stop empty vector creation in GoogleEmbeddingClient
analyzed: 2025-08-25T18:30:00Z
status: critical
parallel_streams: 3
---

# Analysis: Emergency Fix for GoogleEmbeddingClient

## Critical Path
This is a P0 emergency that blocks ALL other work. The system is completely non-functional.

## Parallel Work Streams Identified

### Stream A: Core Fix Implementation
**Scope**: Fix the GoogleEmbeddingClient to stop creating empty vectors
**Files**: 
- `api/google_embedding_client.py`
**Work**:
1. Fix exception handlers at lines 119, 127, 143-144 to raise exceptions instead of appending empty vectors
2. Fix model name from "embedding-001" to "text-embedding-004"
3. Add `_validate_embedding()` method for dimension validation
4. Add `EmbeddingGenerationError` exception class
5. Implement retry logic with exponential backoff

### Stream B: Test Implementation
**Scope**: Create comprehensive test suite for the fix
**Files**:
- `tests/test_emergency_fix.py`
**Work**:
1. Create test for no empty vectors on API failure
2. Create test for correct model name
3. Create test for dimension validation
4. Create test for retry logic on transient failures
5. Create integration test for end-to-end validation

### Stream C: Validation & Recovery
**Scope**: Validate the fix and recover existing data
**Files**:
- `scripts/validate_fix.py`
- `scripts/regenerate_embeddings.py`
**Work**:
1. Create script to validate no empty vectors in pipeline
2. Create script to test FAISS index creation
3. Create script to regenerate all existing embeddings
4. Test RAG/Chat endpoints return 200 OK
5. Add monitoring for empty vector detection

## Dependencies Between Streams
- Stream B (Tests) can start immediately as they define expected behavior
- Stream A (Core Fix) can start immediately and should be guided by Stream B tests
- Stream C (Validation) depends on Stream A completion but scripts can be prepared in parallel

## Coordination Points
1. All streams work in the same branch: `epic/fix-api-pipeline-errors`
2. Stream B creates tests first (TDD approach)
3. Stream A implements fixes to make tests pass
4. Stream C validates the complete solution
5. All streams must complete before marking task as done

## Risk Factors
- API credentials must be available for testing
- Google Vertex AI service must be accessible
- Existing embeddings are corrupted and need regeneration
- System is DOWN until this is fixed

## Success Metrics
- Zero empty vectors in embedding outputs
- All embeddings are exactly 768 dimensions
- FAISS index creation succeeds
- RAG/Chat endpoints return 200 OK
- All tests pass

## Estimated Timeline
- Stream A: 2 hours
- Stream B: 1.5 hours  
- Stream C: 1.5 hours
- Total (parallel): ~2.5 hours with 3 agents

## Files to Monitor for Conflicts
Since this is the first task and conflicts with all others, no merge conflicts expected.
However, all agents must coordinate on:
- `api/google_embedding_client.py` (main fix file)
- Test file naming conventions
- Script locations and naming