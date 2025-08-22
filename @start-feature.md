### Feature: CLI + Test for Generate Wiki Flow

- Goal: Provide a CLI that triggers the same backend flow as the UI "Generate Wiki" and add a test around it.
- Scope: Script calls `/chat/completions/stream` with a repo URL (Codeberg supported). Test stubs models and RAG to validate streaming.

Architecture decisions
- Use backend FastAPI endpoint `api.api:app` route `/chat/completions/stream` to match UI proxy target.
- Keep script minimal; stream SSE-like text to stdout.
- Avoid network/clone in tests by monkeypatching `api.simple_chat.RAG` and `google.generativeai.GenerativeModel`.

Implementation tasks
- Add `scripts/generate_wiki.py` CLI to POST and stream response.
- Add `test/test_generate_wiki_flow.py` with pytest and TestClient.

Validation
- Run: `python scripts/generate_wiki.py --url https://codeberg.org/maxcodefaster/teammind` (server at `SERVER_BASE_URL`).
- Test: `pytest -q test/test_generate_wiki_flow.py` should pass and assert streamed chunks.

Refs: See `.ai/thembad/feature/start-feature.md` for process guidance.


