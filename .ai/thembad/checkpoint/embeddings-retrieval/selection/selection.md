# Selection: Option D (Hybrid A + B)

Chosen approach: Option D — Hybrid (Fail-fast + Adaptive retry)

- Source: `../Option-D.md`
- Rationale: Balanced complexity with immediate automated mitigation; improves reliability without adding provider fallback yet.

## Next Steps
- Implement fail-fast and adaptive retry per checkpoint recommendation.
- Wire config: `adaptive_retry`, `min_chunk_size` in `api/config/embedder.json`.
- Add fail-fast handling in `api/rag.py` and override knobs in `api/data_pipeline.py`.


