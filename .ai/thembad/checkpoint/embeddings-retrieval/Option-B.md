# Option B: Adaptive chunking retry

Automatically re-run embedding pipeline with smaller chunk size (and/or reduced overlap) when initial run yields zero-valid vectors.

## Pros
- Mitigates token length/size-related failures

## Cons
- Longer processing time
- May still fail if provider rejects inputs

## Good when
- Empties correlate with large or irregular chunks

## Scope of Change
- `api/rag.py`: trigger adaptive retry path
- `api/data_pipeline.py`: accept override chunk_size/overlap
- `api/config/embedder.json`: config for adaptive_retry and min_chunk_size

## Acceptance Criteria
- On initial all-empty, a single adaptive retry succeeds for typical large-file repos


