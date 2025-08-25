---
name: fix-rag-fail-fast-unpack-error
status: backlog
created: 2025-08-25T19:11:34Z
progress: 0%
prd: .claude/prds/fix-rag-fail-fast-unpack-error.md
github: [Will be updated when synced to GitHub]
---

# Epic: fix-rag-fail-fast-unpack-error

## Overview
Harden RAG retrieval interfaces to eliminate tuple-unpack failures and standardize return contracts across embedder→retriever and `RAG.call()`→consumer boundaries. Ensure graceful degradation and improved observability without breaking existing endpoints.

## Architecture Decisions
- Keep AdalFlow and FAISS as core components; avoid provider changes.
- Introduce a small adapter for query-embedder outputs so it matches `FAISSRetriever` expectations.
- Standardize `RAG.call()` to always return a 2-tuple `(answer_or_none, retrieved_list)`.
- Add a normalization helper for consumers to insulate against legacy shapes.

## Technical Approach
### Frontend Components
- None required; impact is backend behavior and logging only.

### Backend Services
- Update `api/rag.py`:
  - Adapter for query embedder to return `(embedding_vector, meta)`.
  - Ensure `RAG.call()` always returns `(answer_or_none, retrieved_documents_or_empty)`.
  - Add type/shape assertions and structured logs for return values.
- Update `api/websocket_wiki.py`:
  - Use `normalize_rag_result()` to accept both tuple and legacy shapes.
  - Maintain current streaming logic; handle empty results without exceptions.

### Infrastructure
- No infra changes. Add metrics/logging fields for return-shape observability.

## Implementation Strategy
- Phase 1: Contract hardening (adapter + tuple return + validations).
- Phase 2: Consumer normalization + tests for normal/empty/partial-failure paths.
- Phase 3: Telemetry fields and docs updates.

## Task Breakdown Preview
- [ ] Add query-embedder adapter for retriever expectations
- [ ] Standardize `RAG.call()` tuple return and validations
- [ ] Implement `normalize_rag_result()` and update consumers
- [ ] Add tests for retrieval paths and error handling
- [ ] Add structured logs/metrics for return shapes
- [ ] Update docs (README and internal)

## Dependencies
- AdalFlow components behavior for retriever and embedder
- Existing FAISS retriever API expectations

## Success Criteria (Technical)
- Zero tuple-unpack errors for 7 days in production logs
- Retrieval paths work with and without context; no exceptions
- Tests cover success, empty, and partial-failure scenarios

## Estimated Effort
- 1 sprint (1–2 weeks): code changes, tests, and docs
- Low risk; small, well-scoped changes with high reliability impact

## Tasks Created
- [ ] 001.md - Add query-embedder adapter for FAISSRetriever expectations (parallel: true)
- [ ] 002.md - Standardize RAG.call() to always return (answer_or_none, docs) (parallel: true)
- [ ] 003.md - Implement normalize_rag_result() and update consumers (parallel: true)
- [ ] 004.md - Add tests for retrieval success/empty/partial-failure paths (parallel: true)
- [ ] 005.md - Add structured logs/metrics for return shapes (parallel: true)
- [ ] 006.md - Update README and internal docs for standardized contracts (parallel: true)

Total tasks: 6
Parallel tasks: 6
Sequential tasks: 0
Estimated total effort: 27 hours


