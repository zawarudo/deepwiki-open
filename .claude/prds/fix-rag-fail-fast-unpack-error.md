---
name: fix-rag-fail-fast-unpack-error
description: Fix RAG fail-fast unpack error and harden retrieval-output contracts
status: backlog
created: 2025-08-26T03:00:00Z
---

# PRD: fix-rag-fail-fast-unpack-error

## Executive Summary

RAG retrieval intermittently raises a fail-fast error "not enough values to unpack (expected 2, got 1)" during WebSocket chat flows. Embeddings are present and FAISS retriever is successfully initialized with 110 valid documents, but downstream interfaces disagree on the expected return shapes. The current `RAG.call()` returns only retrieved results, while some consumers and/or the underlying retriever path expect a two-value return (e.g., tuple unpack). This contract mismatch triggers the unpack exception, logged in `api/rag.py:453` and `api/websocket_wiki.py`, leading to "No context available from RAG" and degraded answers.

## Problem Statement

### What problem are we solving?
- Eliminate the fail-fast unpack error ("expected 2, got 1").
- Standardize IO contracts: query embedder → retriever; `RAG.call()` → consumers.
- Ensure graceful degradation: when retrieval/context is unavailable, return empty/None values without exceptions.

### Why is this important now?
1. **User impact**: Answers miss repository-grounded context when retrieval fails.
2. **Reliability**: Exceptions pollute logs and short-circuit context flows.
3. **Maintainability**: Stable return shapes lower breakage risk across providers/models.

## Observations From INFO Logs
- Database loads 110 documents; embedding size validated (target 768); FAISS retriever built successfully.
- This strongly suggests indexing is fine; failures occur at query-time result handling/consumption.
- After the fail-fast error, WebSocket logs "No context available from RAG" and proceeds without context.

```32:40:.claude/prds/fix-pipeline-part-2.md
2025-08-26 ... WARNING - api.embedding_errors - Embedding failures detected
2025-08-26 ... ERROR   - api.embedding_errors - Document embedding failed: doc_0
2025-08-26 ... ERROR   - api.rag - Error in RAG call (fail-fast): not enough values to unpack (expected 2, got 1)
2025-08-26 ... ERROR   - api.websocket_wiki - Error in RAG retrieval: not enough values to unpack (expected 2, got 1)
```

## Error Analysis (plausible root causes)

- **H1: Query embedder → retriever contract mismatch (likely)**
  - `FAISSRetriever` calls the embedder and unpacks results (e.g., `embedding, _ = ...`). Our adapter (`single_string_embedder` or `self.embedder`) may return a single object/vector rather than a 2-item tuple, yielding "expected 2, got 1".

- **H2: RAG result consumption mismatch**
  - `RAG.call()` docstring says it returns a tuple `(RAGAnswer, retrieved_documents)`, but code currently returns only `retrieved_documents` (list-like). Any consumer that relies on the documented tuple will fail to unpack.

- **H3: Co-occurring embedding failures**
  - `api.embedding_errors` reports partial embedding failures, but FAISS index still builds with 110 valid docs. These errors add noise but are not the direct cause of the unpack exception.

### Relevant Code Reference
```422:454:api/rag.py
def call(self, query: str, language: str = "en") -> Tuple[List]:
    ...
    retrieved_documents = self.retriever(query)
    ...
    return retrieved_documents
```

## User Stories

- **Backend Developer**: Needs a stable `RAG.call()` and embedder→retriever interface so integrations never break on unpack.
- **System Operator**: Wants retrieval to degrade gracefully (empty results, no exceptions) so the service remains stable.
- **End User**: Expects context-grounded answers; if context is unavailable, still receive a valid answer without backend errors.

## Requirements

### Functional Requirements
- **FR1: Query Embedder Adapter**: Wrap the embedder passed to `FAISSRetriever` to return the exact structure it expects (e.g., `(vector, meta)`), eliminating unpack errors.
- **FR2: RAG Return Contract Standardization**: Ensure `RAG.call()` consistently returns a tuple `(rag_answer_or_none, retrieved_documents_list)`. If answer generation isn’t performed here, return `(None, retrieved_documents_list)`.
- **FR3: Defensive IO Validation**: Add explicit checks/logs validating embedder return shape and `RAG.call()` output before returning/consuming.
- **FR4: Graceful Degradation**: On retrieval issues, return `(None, [])` with structured diagnostics rather than raising, unless preconditions are unmet (no retriever/no docs).
- **FR5: Call-Site Normalization**: Provide a `normalize_rag_result(value)` helper and update internal call sites to use it.

### Non-Functional Requirements
- **NFR1: Reliability**: Zero "not enough values to unpack" errors in production for 7 consecutive days.
- **NFR2: Observability**: Structured logs include `embedder_return_shape`, `retriever_return_shape`, `rag_call_return_shape`.
- **NFR3: Backward Compatibility**: No breaking changes to public APIs; internal adapters mask shape changes.

## Success Criteria
- Unpack error eliminated across WebSocket and other RAG consumers.
- Context included when available; otherwise, responses still stream without exceptions.
- No regressions in retriever initialization or embedding validation.

## Constraints & Assumptions
- Preserve AdalFlow and FAISS usage patterns.
- Maintain provider/model selection logic.
- Do not alter database formats.

## Implementation Phases

### Phase 1: Contract Hardening (Week 1)
- Implement query-embedder adapter matching `FAISSRetriever`’s expected return type; e.g., always return `(embedding_vector, None)`.
- Update `RAG.call()` to always return a 2-tuple and add type/shape assertions with structured logs.
- Add `normalize_rag_result` and use it where results are consumed.

### Phase 2: Consumer Updates & Tests (Week 1)
- Update `api/websocket_wiki.py` to normalize results and handle both tuple and legacy shapes safely.
- Add tests: normal retrieval, empty retrieval, partial embedding failures, and exception paths (no retriever/no docs).

### Phase 3: Telemetry & Docs (Week 2)
- Emit structured logs for return shapes and sizes; add counters for retrieval success/empty/error by provider/model.
- Update `README.md` and internal docs describing standardized contracts/adapters.

## Risk Assessment
- **Third-party expectations**: If `FAISSRetriever` changes expected embedder output, adapters must be updated.
- **Hidden consumers**: Other code paths may rely on legacy single-value returns. Mitigate with repo-wide search and normalization helper.

## Out of Scope
- Changing embedding providers or replacing FAISS retriever.
- Reworking the embedding pipeline beyond interface hardening.

## Appendix

### Proposed Return Contract
```python
# Always return a tuple from RAG.call()
return (rag_answer_or_none, retrieved_documents_or_empty_list)
```

### Notes on Embedding Errors
- Partial embedding failures are separately handled/logged by `api.embedding_errors` and should not cause unpack errors if interfaces are correct.


