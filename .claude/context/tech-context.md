---
created: 2025-08-23T07:29:41Z
last_updated: 2025-08-23T07:29:41Z
version: 1.0
author: Claude Code PM System
---

# Technology Context

## Technology Stack Overview

### Frontend Stack
- **Framework**: Next.js 15.3.1 with React 19.0.0
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 4.x
- **Build Tool**: Next.js with Turbopack
- **Package Manager**: npm/yarn

### Backend Stack
- **Framework**: FastAPI (>=0.95.0)
- **Language**: Python 3.x
- **Server**: Uvicorn with standard extras
- **Validation**: Pydantic 2.0+
- **Environment**: python-dotenv for configuration

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Version Control**: Git with GitHub
- **CI/CD**: GitHub Actions
- **Development**: VS Code configuration included

## Frontend Dependencies

### Core Framework
- `next`: 15.3.1 - React framework with SSR/SSG
- `react`: 19.0.0 - UI library
- `react-dom`: 19.0.0 - React DOM renderer

### UI & Visualization
- `mermaid`: 11.4.1 - Diagram and flowchart rendering
- `react-icons`: 5.5.0 - Icon library
- `svg-pan-zoom`: 3.6.2 - SVG interaction library
- `next-themes`: 0.4.6 - Theme management

### Content Rendering
- `react-markdown`: 10.1.0 - Markdown rendering
- `react-syntax-highlighter`: 15.6.1 - Code syntax highlighting
- `rehype-raw`: 7.0.0 - HTML processing in markdown
- `remark-gfm`: 4.0.1 - GitHub Flavored Markdown support

### Internationalization
- `next-intl`: 4.1.0 - Internationalization support

### Development Dependencies
- `typescript`: 5.x - Type safety
- `eslint`: 9.x with Next.js config
- `@tailwindcss/postcss`: 4.x - CSS processing
- Type definitions for React and libraries

## Backend Dependencies

### API Framework
- `fastapi`: >=0.95.0 - Modern web API framework
- `uvicorn[standard]`: >=0.21.1 - ASGI server
- `pydantic`: >=2.0.0 - Data validation
- `jinja2`: >=3.1.2 - Template engine

### AI/ML Integration
- `google-generativeai`: >=0.3.0 - Google AI integration
- `openai`: >=1.76.2 - OpenAI API client
- `ollama`: >=0.4.8 - Local LLM support
- `azure-identity`: >=1.12.0 - Azure authentication
- `azure-core`: >=1.24.0 - Azure core services

### Vector Search & NLP
- `faiss-cpu`: >=1.7.4 - Vector similarity search
- `tiktoken`: >=0.5.0 - Token counting for OpenAI
- `langid`: >=1.1.6 - Language identification
- `adalflow`: >=0.1.0 - LLM application framework

### Data Processing
- `numpy`: >=1.24.0 - Numerical computing
- `requests`: >=2.28.0 - HTTP client
- `aiohttp`: >=3.8.4 - Async HTTP client

### Infrastructure
- `boto3`: >=1.34.0 - AWS SDK
- `websockets`: >=11.0.3 - WebSocket support
- `python-dotenv`: >=1.0.0 - Environment management

## Development Tools

### Build & Bundle
- **Next.js Turbopack**: Fast development builds
- **TypeScript Compiler**: Type checking
- **PostCSS**: CSS processing pipeline

### Code Quality
- **ESLint**: JavaScript/TypeScript linting
- **Next.js ESLint Config**: Preconfigured rules
- **Pytest**: Python testing framework

### Package Management
- **npm/yarn**: Node.js package management
- **pip/uv**: Python package management
- **Lock Files**: package-lock.json, yarn.lock, uv.lock

## API Integrations

### Supported AI Providers
1. **Google AI (Gemini)**
   - API Key: `GOOGLE_API_KEY`
   - Models: Gemini family

2. **OpenAI**
   - API Key: `OPENAI_API_KEY`
   - Models: GPT family

3. **OpenRouter**
   - API Key: `OPENROUTER_API_KEY`
   - Multiple model access

4. **Ollama (Local)**
   - Host: `OLLAMA_HOST` (default: http://localhost:11434)
   - Local model execution

5. **Azure OpenAI**
   - API Key: `AZURE_OPENAI_API_KEY`
   - Endpoint: `AZURE_OPENAI_ENDPOINT`
   - Version: `AZURE_OPENAI_VERSION`

### External Services
- **GitHub/GitLab/BitBucket**: Repository analysis
- **WebSocket**: Real-time communication
- **AWS Services**: Via boto3 SDK

## Development Environment

### Node.js Configuration
```json
{
  "scripts": {
    "dev": "next dev --turbopack --port 3000",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }
}
```

### Python Configuration
- Python version: Specified in `.python-version`
- Virtual environment: Recommended
- Testing: Pytest with configuration in `pytest.ini`

### Docker Setup
- Production: `Dockerfile` with multi-stage build
- Development: `docker-compose.dev.yml`
- Ollama Integration: `Dockerfile-ollama-local`

## Version Requirements

### Minimum Versions
- **Node.js**: 18.x or higher (for Next.js 15)
- **Python**: 3.8+ (for FastAPI and type hints)
- **Docker**: 20.x or higher
- **Docker Compose**: 2.x

### Browser Support
- Modern browsers with ES6+ support
- WebSocket support required
- SVG rendering capabilities

## Performance Optimizations

### Frontend
- Turbopack for fast development builds
- React 19 with improved performance
- Next.js SSR/SSG for optimal loading
- Code splitting and lazy loading

### Backend
- FastAPI async request handling
- FAISS for efficient vector search
- Connection pooling for databases
- Caching strategies implemented

## Security Considerations

### Authentication & Authorization
- API key management via environment variables
- Azure identity integration
- Secure token handling

### Data Protection
- Environment variables for sensitive data
- HTTPS enforcement in production
- Input validation with Pydantic

## Monitoring & Logging

### Application Monitoring
- Custom watcher agents in `watcher-agents/`
- API log monitoring scripts
- Log rotation implemented (PR #312)

### Development Tools
- VS Code integration
- Debug configurations
- Testing pipelines

This technology context defines the comprehensive tech stack powering the DeepWiki-Open application, enabling automatic wiki generation with AI-powered analysis and visualization.