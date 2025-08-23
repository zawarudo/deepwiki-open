<!-- managed-by: concise-architecture-initializer v1 -->
Purpose: AI provider client implementations for LLM interactions
Scope: Includes provider clients, embedding services; excludes API routing
Where in code: api/*_client.py, api/google_embedding_client.py
Interfaces: OpenAI, Google, Bedrock, Azure, Ollama, OpenRouter clients
Next:
- Providers: openai, google/gemini, bedrock, azure, ollama, openrouter, dashscope