---
name: fix-rag-fail-fast-unpack-error
status: in_progress
created: 2025-08-25T19:11:34Z
updated: 2025-08-26T12:00:00Z
progress: 0%
prd: .claude/prds/fix-rag-fail-fast-unpack-error.md
github: [Will be updated when synced to GitHub]
---

# Epic: fix-rag-fail-fast-unpack-error

## Overview
Fix tuple-unpack errors in RAG pipeline using Test-Driven Development approach with defensive programming. Focus on immediate safety through normalizer helper, followed by root cause fixes with comprehensive logging for observability.

## Architecture Decisions
- **Defensive First**: Add normalizer helper immediately to prevent production crashes
- **TDD Approach**: Write failing tests before implementation (RED → GREEN → REFACTOR)
- **Simple Logging**: JSON-structured logs instead of complex metrics/dashboards
- **Minimal Changes**: Fix only what's broken, avoid over-engineering

## Reference Docs
- PRD: `.claude/prds/fix-rag-fail-fast-unpack-error.md`
- Implementation Plan: `.claude/epics/fix-rag-fail-fast-unpack-error/RESEQUENCED_PLAN.md`
- Edge cases: `.claude/epics/fix-rag-fail-fast-unpack-error/edge-cases.md`
- Task analyses: `001-006-*.md` files in this directory

## Technical Approach
### Phase 0: Quick Safety Net (30 min)
- Create `normalize_rag_result()` helper that ensures tuple return
- Update critical consumers to use normalizer
- Add basic shape logging

### Phase 1: Core Fixes (2 hours)
- Fix `RAG.call()` to always return `(answer, documents)` tuple
- Add `__call__` method to make RAG callable (syntactic sugar for `rag(query)` usage)
- Create embedder wrapper for FAISS compatibility (normalizes provider response formats)

### Phase 2: Simple Logging (1 hour)
- Add JSON-structured logging to RAG calls (output to `/tmp/rag_test.log`)
- Log status, doc_count, error_type, has_answer, provider, query_length
- Create log analysis script (`/tmp/analyze_logs.sh`)

### Phase 3: Integration Testing (1.5 hours)
- Write comprehensive tests using TDD
- Test all provider scenarios (OpenAI, Gemini, Ollama, OpenRouter)
- Verify performance overhead < 50% via timing harness

### Phase 4: Documentation & Handoff (30 min)
- Update code docstrings
- Create agent handoff document
- Add troubleshooting to README for:
  - Concurrent access limitations
  - Large result set performance
  - Provider switching (dimension mismatch)
  - Memory monitoring guidance
  - SSL/Proxy configuration

## Implementation Strategy
**Test-Driven Development Flow:**
1. Write failing test (RED)
2. Implement minimal fix (GREEN)
3. Verify with debug commands (REFACTOR)
4. Check logs for validation

**Key Dependencies:**
- Task 001 → Task 003: Adapter output affects normalizer
- Task 002 → Task 003: RAG.call() format must be stable first
- Tasks 001-003 → Task 004: Tests need stable APIs

## Task Breakdown (Revised)
- [ ] **Phase 0**: Defensive normalizer helper (30 min)
- [ ] **Phase 1.1**: Fix RAG.call() tuple return (1 hour)
- [ ] **Phase 1.2**: Add embedder wrapper (1 hour)
- [ ] **Phase 2**: JSON logging implementation (1 hour)
- [ ] **Phase 3**: Integration testing suite (1.5 hours)
- [ ] **Phase 4**: Documentation & handoff (30 min)

## Dependencies
- Python logging module
- pytest for testing
- faiss-cpu for retriever
- numpy for embeddings

## Success Criteria (Simplified)
- **No tuple-unpack errors** in production logs → verified by `test/test_normalizer.py`
- **RAG still works** with all providers → verified by `test/test_integration.py`
- **All tests pass**:
  - `test/test_normalizer.py` → Phase 0 defensive helper
  - `test/test_rag_tuple_return.py` → Phase 1.1 RAG.call() contract
  - `test/test_embedder_wrapper.py` → Phase 1.2 embedder wrapper
  - `test/test_integration.py` → Phase 3 end-to-end validation
- **Performance overhead < 50%** → verified by `test/test_performance.py` timing harness
- **Clear handoff documentation** → `HANDOFF.md` + README updates

## Estimated Effort (Revised)
- **Total: 5-6 hours** of focused work
- Can be completed by one developer in a single day
- Low risk due to defensive normalizer approach

## Debug Commands & Scripts
Key files for agent handoff:
- Test runner: `/tmp/run_all_tests.sh`
- Log analyzer: `/tmp/analyze_logs.sh` (reads from `/tmp/rag_test.log`)
- Quick validation: `/tmp/quick_validation.sh` (edge case validation)
- Performance check: `/tmp/perf_check.sh` (< 50% overhead verification)
- Final verification: `/tmp/final_verification.sh`
- Handoff doc: `.claude/epics/fix-rag-fail-fast-unpack-error/HANDOFF.md`

## Quick Start for Implementation
```bash
# 1. Set up environment
cd /home/ubuwarudo/Personal/deepwiki-open
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 2. Start with Phase 0 - Defensive normalizer
pytest test/test_normalizer.py -v  # Should fail
# Implement normalizer
pytest test/test_normalizer.py -v  # Should pass

# 3. Continue through phases using test files
# Each phase has RED → GREEN → REFACTOR cycle
```

## Tasks Created
- [ ] 001.md - Add query-embedder adapter for FAISSRetriever expectations (Phase 1.2)
- [ ] 002.md - Standardize RAG.call() to always return (answer_or_none, docs) (Phase 1.1)
  - Include `__call__` method for syntactic sugar
  - Handle empty/None queries with early return
  - Catch all exceptions and return (None, [])
- [ ] 003.md - Implement normalize_rag_result() and update consumers (Phase 0)
- [ ] 004.md - Add tests for retrieval success/empty/partial-failure paths (Phase 3)
  - Include performance timing harness for < 50% overhead
- [ ] 005.md - Add structured logs/metrics for return shapes (Phase 2)
  - Output to `/tmp/rag_test.log`
  - Include provider, query_length, status, doc_count, error_type, has_answer
- [ ] 006.md - Update README and internal docs for standardized contracts (Phase 4)
  - Document concurrent access limitations
  - Document large result set performance considerations
  - Document provider switching dimension mismatch risks
  - Add memory monitoring guidance
  - Add SSL/proxy troubleshooting

**Execution Order (from RESEQUENCED_PLAN):**
1. Task 003 (Phase 0) - Defensive normalizer first → `test/test_normalizer.py`
2. Tasks 002 & 001 (Phase 1) - Core fixes (can run parallel)
   - Task 002: `test/test_rag_tuple_return.py`
   - Task 001: `test/test_embedder_wrapper.py`
3. Task 005 (Phase 2) - Logging → output to `/tmp/rag_test.log`
4. Task 004 (Phase 3) - Testing → `test/test_integration.py` + `test/test_performance.py`
5. Task 006 (Phase 4) - Documentation → README + HANDOFF.md

Total tasks: 6
Revised effort: 5-6 hours (down from 27 hours)
Approach: TDD with defensive programming

