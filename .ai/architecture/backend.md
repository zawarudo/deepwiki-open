<!-- managed-by: concise-architecture-initializer v1 -->
Purpose: FastAPI server providing REST endpoints and AI processing
Scope: Includes API handlers, AI clients, RAG; excludes frontend and infrastructure
Where in code: api/, scripts/generate_wiki.py
Interfaces: REST API, WebSocket, AI provider clients
Next:
- .ai/architecture/backend/apis.md — HTTP endpoints and WebSocket handlers
- .ai/architecture/backend/ai-providers.md — LLM client implementations