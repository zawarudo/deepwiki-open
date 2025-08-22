## Command → Approach: Bridging Prompt Checkpoints to RAG Decisions

### Purpose
- **Unify prompts and decisions**: Treat checkpoint prompts as commands that produce explicit, versioned decisions for the RAG pipeline.
- **Make choices first-class**: Capture options, chosen paths, and acceptance criteria in a YAML source of truth.

### Building Blocks (Commands)
- **@checkpoint**: Create a decision checkpoint using the canonical schema in `checkpoint.template.yml`. Output as Markdown and/or YAML.
- **@options-checkpoint**: Generate a concise option set with pros/cons and selection criteria based on the current problem.
- **@options-explore**:
  - `SPLIT ${NAME}`: Branch approaches into separate artifacts for parallel exploration.
  - `SELECT ${APPROACH_NAME}`: Create a safe directory for the chosen approach (see slug rules in `options-explore.md`).

### Source of Truth
- **Schema**: `.ai/thembad/checkpoint/checkpoint.template.yml`
- **Instance**: `.ai/thembad/checkpoint/<date>-<feature>-checkpoint.yml`
- Sections map directly to RAG execution:
  - `system_prompt` → decision context and deliverables
  - `current_state` → implemented behavior and gaps
  - `action_plan` → concrete edits and tests
  - `options` → explicit tradeoffs
  - `recommendation` → chosen path, scope, criteria, test matrix
  - `next_phase_prompt` → handoff prompt for PM/QA/Dev

### RAG System Concepts (Where decisions apply)
- **Ingestion & Splitting**: splitter type, `chunk_size`, `chunk_overlap` in `api/data_pipeline.py`.
- **Embedding**: provider choice, batch sizing, error handling (e.g., partial results) in `api/google_embedding_client.py` or provider-specific clients.
- **Vector Store / Index**: index type (e.g., FAISS), metric (L2/IP), normalization policy, persistence.
- **Retriever Parameters**: `k`, `fetch_k`, filters, fail-fast when all vectors are empty (see `api/rag.py` for retriever prep integration points).
- **Fallbacks & Retries**: adaptive `chunk_size` retry path; optional provider fallback toggles (e.g., proposed in `api/config/embedder.json`).
- **Observability**: counts of valid/empty vectors, provider error summaries; actionable errors before index creation.

### Decision Checkpoints → RAG Alignment
- **Option examples** (from YAML or Markdown):
  - A: Fail-fast + guidance → Improve operator feedback; no auto-mitigation.
  - B: Adaptive chunking retry → Auto-retry with smaller `chunk_size`.
  - C: Provider fallback (feature flag) → Retry with alternate embeddings provider.
  - D: Hybrid (A+B) → Combine signal with one automated mitigation.
- **Acceptance criteria** translate into RAG evals:
  - Non-zero valid vectors for representative repos
  - Clear error messages when zero-valid persists
  - Stable vector sizes and retriever initialization

### Minimal Workflow
1. Run **@options-checkpoint** to enumerate approaches with pros/cons and selection criteria.
2. Use **@options-explore SPLIT** to branch artifacts; for the chosen branch, run **SELECT** to create a safe directory for work.
3. Materialize a YAML checkpoint from `checkpoint.template.yml` that encodes the decision set for the feature.
4. Implement edits in the referenced modules (e.g., `api/data_pipeline.py`, `api/rag.py`, provider clients), guided by `action_plan`.
5. Validate against `acceptance_criteria` and `test_matrix` from the YAML checkpoint.
6. If results fail criteria, return to the option set and iterate.

### Directory & Naming Conventions
- Option exploration: `checkpoint/{solution-space}/{sanitized-approach-name}/`
- Checkpoint instance: `.ai/thembad/checkpoint/<date>-<feature>-checkpoint.yml`
- Keep approach artifacts (notes, diffs, logs) local to the approach directory.

### Safety & Truthfulness
- Commands do not delete or overwrite artifacts by default; branching is additive.
- Only claim configuration fields that exist; proposed toggles (e.g., `adaptive_retry`) must be added explicitly before use.
- Log decisions and outcomes in the YAML to ensure reproducibility and auditability.


