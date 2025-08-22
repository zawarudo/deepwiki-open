### Options Explore: Generate Wiki Scripting

Goals & outcomes
- Script the Generate Wiki flow via backend stream endpoint.
- Add a fast, reliable test that does not hit external services.

JUSTIFICATION
- Directly exercising `/chat/completions/stream` best mirrors the UI button behavior (via Next.js proxy).
- Monkeypatching external dependencies keeps tests deterministic and fast.

ACTION-PLAN
- Implement `scripts/generate_wiki.py` (argparse, streams stdout).
- Add pytest `test/test_generate_wiki_flow.py` monkeypatching RAG and Google GenAI model.
- Document usage in `@start-feature.md`.

Refs: `.ai/thembad/checkpoint/options-explore.md`.


