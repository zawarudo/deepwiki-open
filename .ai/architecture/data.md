<!-- managed-by: concise-architecture-initializer v1 -->
Purpose: Data processing pipelines and storage management
Scope: Includes embeddings, RAG, state persistence; excludes UI and API routing
Where in code: api/data_pipeline.py, api/rag.py, state/
Interfaces: Embedding services, vector search, state management
Next:
- .ai/architecture/data/embeddings.md — Vector embedding generation and storage
- .ai/architecture/data/rag.md — Retrieval augmented generation pipeline