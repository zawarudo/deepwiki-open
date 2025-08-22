# Option D: Hybrid (A + B) [Recommended]

Combine fail-fast operator guidance with one adaptive retry pass using smaller chunk size; defer provider fallback behind a later feature flag.

## Pros
- Clear operator signal and automated mitigation
- Balanced complexity with fast path to reliability

## Cons
- Slightly more surface than A
- No automatic provider failover

## Scope of Change
- `api/rag.py`: fail-fast with actionable error and trigger adaptive retry
- `api/data_pipeline.py`: accept override chunk_size/overlap
- `api/config/embedder.json`: add adaptive_retry and min_chunk_size

## Acceptance Criteria
- Typical repos recover on the single adaptive retry
- All-empty after retry yields explicit, actionable guidance


