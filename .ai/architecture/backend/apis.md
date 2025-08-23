<!-- managed-by: concise-architecture-initializer v1 -->
Purpose: REST API endpoints and WebSocket handlers for wiki generation
Scope: Includes route handlers, WebSocket events; excludes AI client logic
Where in code: api/api.py, api/main.py, api/websocket_wiki.py
Interfaces: /api/generate_wiki, /api/get_messages, WebSocket /ws
Next:
- Routes: generate_wiki, get_messages, chat_stream, simple_chat