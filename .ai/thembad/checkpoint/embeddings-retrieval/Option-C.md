# Option C: Provider fallback (feature flag)

Retry embeddings with an alternate provider when primary provider yields pervasive empty vectors or errors.

## Pros
- Recovers when a single provider is unstable or rate-limited

## Cons
- More complexity and credentials
- Cross-provider embeddings are not identical

## Good when
- Reliability > strict reproducibility

## Scope of Change
- `api/config/embedder.json`: enable provider toggle
- `api/tools/embedder.py` and `api/config.py`: honor toggle
- `api/rag.py`: retry with alternate embedder when flagged

## Acceptance Criteria
- When fallback is enabled and primary fails, retry succeeds without code changes


