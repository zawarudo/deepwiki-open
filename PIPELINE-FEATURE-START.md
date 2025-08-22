### Pipeline Feature Start: Run, analyze, and grow tests

Purpose
- Continuously validate the Generate Wiki streaming flow and expand coverage as bugs are found and fixed.

Scope (initial)
- Target critical test: `test/test_generate_wiki_flow.py` (streams content via `/chat/completions/stream`).
- No external network; dependencies are monkeypatched for determinism.

Run commands
- From repo root:
  - `pytest -q test/test_generate_wiki_flow.py -rA`

What to analyze
- **Failures**: assertion diffs, stack traces, unexpected HTTP status codes.
- **Flakes**: timing-dependent behavior, intermittent failures.
- **Output**: ensure streamed chunks are present and ordered (contains "TEST_STREAM_" and "OK").

Bug triage loop
- If the test fails or reveals a defect:
  - Identify the minimal failing condition.
  - Add/adjust a regression test capturing that condition.
  - Fix the implementation.
  - Re-run the test command until green.
  - Update `TESTING-PIPELINE.md` with any newly added critical tests.

How to grow the pipeline
- Add more tests that exercise:
  - Error pathways (e.g., missing API keys, inconsistent embeddings, token limits) with controlled monkeypatches.
  - Repo types (github, gitlab, bitbucket, codeberg) request payload variations (no network calls).
  - RAG fail-fast behavior (invalid retriever state) and adaptive retry signaling (log/assert paths only; no network).
- Document each new critical test in `TESTING-PIPELINE.md`.

Environment
- Tests are self-contained; no server required.
- Optional: set `SERVER_BASE_URL` for manual CLI checks only (not needed for pytest).

Manual verification (optional)
- `python scripts/generate_wiki.py --url https://codeberg.org/maxcodefaster/teammind`
- Expect streamed output to stdout. Use only for smoke checks; rely on pytest for CI gates.

Exit criteria
- All pipeline tests pass locally and in CI.
- New bugs always produce a new/updated test before fix is merged.


