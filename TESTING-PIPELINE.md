### Critical pipeline tests

- Generate Wiki chat stream (backend):
  - Ensures the backend stream endpoint `/chat/completions/stream` returns streamed content for a repository URL without hitting external services.
  - Test file: `test/test_generate_wiki_flow.py`
  - Strategy: monkeypatch `RAG` and `google.generativeai.GenerativeModel` to avoid cloning/embedding and assert streamed chunks are returned.
  - Run:
    - `pytest -q test/test_generate_wiki_flow.py`

### Supporting script (manual check)

- CLI to hit the same flow as the UI Generate Wiki button:
  - `scripts/generate_wiki.py`
  - Example:
    - `python scripts/generate_wiki.py --url https://codeberg.org/maxcodefaster/teammind`
  - Notes: points at `SERVER_BASE_URL` (default `http://localhost:8001`) and posts to `/chat/completions/stream`.


