### NEXT-STEPS: Programmatic Decision Checkpoints for RAG (CODG-R System)

This proposal describes how to implement the mechanics of the existing prompt-based checkpoint system as real software with explicit data models, APIs, a CLI, and integration points to a RAG pipeline, following the abstractions defined in the checkpoint docs and their mapping in `.ai/thembad/checkpoint/COMMAND-APPROACH.md`.

### Goals
- **Programmatize checkpoints and options**: Turn `@checkpoint`, `@options-checkpoint`, and `@options-explore (SPLIT/SELECT)` into idempotent commands and library calls that create versioned artifacts and directories.
- **Single source of truth**: Persist decisions in a YAML/Markdown instance that conforms to `.ai/thembad/checkpoint/checkpoint.template.yml` and lives at `.ai/thembad/checkpoint/<date>-<feature>-checkpoint.yml`.
- **RAG alignment**: Materialize decisions into concrete parameters for ingestion/splitting, embedding, vector index, retriever, fallbacks/retries, and observability (as described in `COMMAND-APPROACH.md`).
- **Safety & auditability**: Additive branching, no destructive defaults, explicit provenance and acceptance criteria.

### Non‑Goals
- Designing new RAG algorithms. We operationalize choices already described in `COMMAND-APPROACH.md`.
- Introducing external dependencies or undocumented config fields beyond what the schema declares.

### Core Data Model (files first, DB optional)
- **CheckpointInstance**: Parsed from `.ai/thembad/checkpoint/<date>-<feature>-checkpoint.yml`; sections: `system_prompt`, `current_state`, `action_plan`, `options`, `recommendation`, `next_phase_prompt`, plus `acceptance_criteria` and `test_matrix` if present.
- **OptionBranch**: An element in `options` with pros/cons and selection criteria; can materialize as approach directories under `checkpoint/{solution-space}/{sanitized-approach-name}/`.
- **Recommendation**: The chosen path with scope and param deltas for the RAG system.
- **ProvenanceEvent**: Append‑only log entries that link commands to artifacts (who/when/what), stored alongside the checkpoint instance as Markdown or YAML blocks.

Optional persistence layer (future): Mirror the above in a lightweight SQLite/Postgres schema for richer querying; file artifacts remain the source of truth.

### System Architecture
- **CLI** (thin): Deterministic commands that read/write YAML/MD files and directories.
- **Library** (core): Pure functions for schema validation, branching, selection, slug-safe directory creation, and RAG parameter mapping.
- **Adapters**: Optional hooks that translate a `Recommendation` into concrete edits or runtime parameters for the RAG pipeline (as referenced in `COMMAND-APPROACH.md`).
- **Evaluators**: Run acceptance/test checks (e.g., non‑zero valid vectors) and write results back into the checkpoint instance.

### Modules (proposed)
- `checkpoint_schema`:
  - validate/load/save instances that conform to `.ai/thembad/checkpoint/checkpoint.template.yml`.
  - ensure required sections are present; forbid unknown fields.
- `options_engine`:
  - generate concise option sets with pros/cons and selection criteria.
  - implement `split_options()` to create per‑approach artifacts.
- `explore_select`:
  - `create_safe_directory(solution_space, approach_name)` using slug rules from `.ai/thembad/checkpoint/options-explore.md`.
  - `select_recommendation(option_id|name)` to set the `recommendation` section.
- `provenance`:
  - append events for every CLI/library action; maintain supersedes/branches edges.
- `rag_alignment`:
  - map `action_plan`/`recommendation` to RAG knobs listed in `COMMAND-APPROACH.md` (ingestion, embedding, index, retriever, fallbacks, observability).
  - no‑op for fields not present; fail safely on missing schema entries.
- `eval_runner`:
  - execute `acceptance_criteria`/`test_matrix` checks and write structured results back to the instance.

### CLI (idempotent commands)
- `checkpoint create --feature <name> --date <YYYY-MM-DD>`
  - Materialize a new instance from `.ai/thembad/checkpoint/checkpoint.template.yml` with empty/default sections.
- `options generate --instance <path>`
  - Populate `options` with alternatives (e.g., A: fail‑fast, B: adaptive chunking retry, C: provider fallback, D: hybrid), as outlined in `COMMAND-APPROACH.md`.
- `options split --instance <path> --solution-space <dir>`
  - Create `checkpoint/{solution-space}/{sanitized-approach-name}/` for each option.
- `options select --instance <path> --approach <name|id> --solution-space <dir>`
  - Create safe directory (if needed) and set `recommendation` with scope and criteria.
- `checkpoint materialize --instance <path>`
  - Write updated YAML/MD instance and append provenance.
- `eval run --instance <path>`
  - Run acceptance/test checks; persist results.
- `phase handoff --instance <path>`
  - Emit `next_phase_prompt` into a handoff artifact for PM/QA/Dev.

### Program Flow (minimal workflow, programmatic)
1. `options generate` on a target instance.
2. `options split` to branch artifacts; for the chosen branch, run `options select`.
3. `checkpoint materialize` to persist the decision set.
4. Use `rag_alignment` to project `recommendation` into RAG parameters.
5. `eval run` to verify `acceptance_criteria`/`test_matrix`.
6. If failing, iterate from step 1 with updated options.

### RAG Mapping (from `COMMAND-APPROACH.md`)
- **Ingestion & Splitting**: splitter type, `chunk_size`, `chunk_overlap` → read from `recommendation` and apply where ingestion is configured.
- **Embedding**: provider choice, batch sizing, error handling for partial results → driven by `options` choice and `recommendation` toggles.
- **Vector Store / Index**: index type (e.g., FAISS), metric (L2/IP), normalization, persistence → set via `recommendation`.
- **Retriever Parameters**: `k`, `fetch_k`, filters, fail‑fast on zero‑vectors → set via `recommendation`.
- **Fallbacks & Retries**: adaptive `chunk_size` retry, provider fallback feature flag → selected option encodes behavior (A–D, hybrid).
- **Observability**: valid/empty vector counts, error summaries, pre‑index actionable errors → `eval_runner` records evidence against `acceptance_criteria`.

### Safety & Truthfulness Invariants
- **Additive branching**: SPLIT/SELECT never delete or overwrite source artifacts by default.
- **Schema‑first**: Only fields declared in `.ai/thembad/checkpoint/checkpoint.template.yml` are read/written.
- **Provenance**: Every command appends a `ProvenanceEvent` (who/when/what) to the instance.
- **Fail‑safe**: Missing or unknown fields result in no‑op mappings, with explicit warnings in provenance.

### Testing Strategy
- **Unit**: slugify rules from `.ai/thembad/checkpoint/options-explore.md`; schema validation; selection idempotency; provenance append logic.
- **Integration**: end‑to‑end flow from `options generate` → `options select` → `materialize` → `eval run` with fixtures simulating: (a) all empty vectors, (b) successful embeddings, (c) index creation with varying metrics.
- **Contract**: ensure alignment outputs only touch parameters enumerated in `COMMAND-APPROACH.md`.

### Incremental Delivery Plan
- **Phase 0 – Scaffolding**: CLI skeleton, schema loader/validator, slugify utility, file I/O for instances.
- **Phase 1 – Options Engine**: generate/split/select with provenance and safe directories.
- **Phase 2 – RAG Alignment Adapter**: mapping layer that projects a `Recommendation` onto RAG parameters described in `COMMAND-APPROACH.md`.
- **Phase 3 – Evaluators**: acceptance/test checks and result persistence to the instance.
- **Phase 4 – Handoffs**: `next_phase_prompt` emitters for PM/QA/Dev.
- **Phase 5 – Hardening**: idempotency checks, concurrency guard (file locks), richer provenance, CLI UX polish.

### Deliverables
- Executable CLI with commands listed above.
- Core library functions with clear, typed interfaces.
- Example checkpoint instance and generated approach directories under `.ai/thembad/checkpoint/`.
- Tests covering unit/integration paths and acceptance criteria cases (e.g., non‑zero valid vectors, clear zero‑valid errors, stable retriever init).

### Open Questions
- What exact acceptance/test matrices are canonical beyond those enumerated in `COMMAND-APPROACH.md`?
- Which RAG configuration surfaces are editable at runtime vs. require code edits in the current environment?
- Which observability sinks should be used for recording evaluation outcomes alongside the instance?

### Appendix: Directory & Naming
- Checkpoint instance path: `.ai/thembad/checkpoint/<date>-<feature>-checkpoint.yml`
- Template path: `.ai/thembad/checkpoint/checkpoint.template.yml`
- Option exploration dirs: `checkpoint/{solution-space}/{sanitized-approach-name}/` (apply slug rules in `.ai/thembad/checkpoint/options-explore.md`).


