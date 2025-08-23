---
created: 2025-08-23T07:29:41Z
last_updated: 2025-08-23T07:29:41Z
version: 1.0
author: Claude Code PM System
---

# Project Structure

## Root Directory Organization

```
deepwiki-open/
├── .ai/                    # AI-related configurations
├── .claude/                # Claude Code PM system files
│   ├── context/           # Project context documentation
│   └── rules/             # PM system rules
├── .github/               # GitHub workflows and configurations
├── .next/                 # Next.js build output
├── .vscode/               # VS Code settings
├── api/                   # Backend API (FastAPI)
│   ├── main.py           # API entry point
│   ├── requirements.txt  # Python dependencies
│   └── [modules]         # API modules and services
├── abstraction/           # Abstract layer implementations
├── node_modules/          # Node.js dependencies
├── public/                # Static assets
├── reports/               # Generated reports
├── screenshots/           # Application screenshots
├── scripts/               # Utility scripts
├── src/                   # Frontend source code (Next.js)
│   ├── components/       # React components
│   ├── hooks/            # Custom React hooks
│   └── [modules]         # Frontend modules
├── state/                 # Application state management
├── test/                  # Test files
├── watcher-agents/        # Monitoring agents
│   └── api-logs/         # API log monitoring
└── Configuration Files
```

## Key Directories

### Frontend (`/src`)
```
src/
├── components/            # React UI components
│   ├── Ask.tsx           # Chat/Q&A interface
│   ├── ConfigurationModal.tsx
│   ├── Markdown.tsx      # Markdown renderer
│   ├── Mermaid.tsx       # Diagram renderer
│   ├── ModelSelectionModal.tsx
│   ├── ProcessedProjects.tsx
│   ├── UserSelector.tsx
│   ├── WikiTreeView.tsx # Wiki navigation tree
│   └── WikiTypeSelector.tsx
├── hooks/                # Custom React hooks
│   └── useProcessedProjects.ts
└── [app structure]       # Next.js app router
```

### Backend (`/api`)
```
api/
├── main.py               # FastAPI application entry
├── requirements.txt      # Python dependencies
├── routers/              # API route handlers
├── services/             # Business logic services
├── models/               # Data models
└── utils/                # Utility functions
```

### Configuration Files

#### Docker Configuration
- `Dockerfile` - Main production Docker image
- `Dockerfile-ollama-local` - Ollama integration Docker image
- `docker-compose.yml` - Production Docker Compose
- `docker-compose.dev.yml` - Development Docker Compose
- `.dockerignore` - Docker build exclusions

#### Frontend Configuration
- `package.json` - Node.js dependencies and scripts
- `package-lock.json` - Locked dependency versions
- `yarn.lock` - Yarn locked dependencies
- `next.config.ts` - Next.js configuration
- `tsconfig.json` - TypeScript configuration
- `tailwind.config.js` - Tailwind CSS configuration
- `postcss.config.mjs` - PostCSS configuration
- `eslint.config.mjs` - ESLint linting rules

#### Backend Configuration
- `pyproject.toml` - Python project configuration
- `requirements.txt` - Python dependencies (api/)
- `pytest.ini` - Pytest testing configuration
- `.python-version` - Python version specification
- `uv.lock` - UV package manager lock file

#### Environment & Git
- `.env` - Environment variables (not in repo)
- `.gitignore` - Git exclusion patterns
- `LICENSE` - MIT License

## Documentation Files

### Core Documentation
- `README.md` - Main project documentation (English)
- `README.*.md` - Translations (es, fr, ja, kr, pt-br, ru, vi, zh, zh-tw)
- `Ollama-instruction.md` - Ollama setup guide

### Development Documentation
- `AGENTS.md` - Agent system documentation
- `NEXT-STEPS.md` - Development roadmap
- `PIPELINE-FEATURE-START.md` - Pipeline feature docs
- `TESTING-PIPELINE.md` - Testing pipeline guide
- `@options-explore.md` - Options exploration
- `@start-feature.md` - Feature development guide

## Build & Output Directories

### Generated Directories
- `.next/` - Next.js build output
- `node_modules/` - Node.js dependencies
- `.pytest_cache/` - Pytest cache
- `reports/` - Generated analysis reports
- `state/` - Application runtime state

## Special Directories

### Monitoring & Agents (`/watcher-agents`)
```
watcher-agents/
└── api-logs/
    └── simple_monitor.sh  # API log monitoring script
```

### Abstraction Layer (`/abstraction`)
- Contains abstraction implementations for various services
- Provides unified interfaces for different providers

### Testing (`/test`)
- Unit tests
- Integration tests
- End-to-end tests
- Test fixtures and utilities

## File Naming Conventions

### TypeScript/JavaScript
- Components: `PascalCase.tsx` (e.g., `WikiTreeView.tsx`)
- Hooks: `camelCase.ts` with `use` prefix (e.g., `useProcessedProjects.ts`)
- Utilities: `camelCase.ts` (e.g., `utils.ts`)
- Configuration: `kebab-case.config.{js,ts,mjs}`

### Python
- Modules: `snake_case.py` (e.g., `main.py`)
- Classes: `PascalCase` within files
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Documentation
- Markdown: `UPPER-KEBAB-CASE.md` for main docs
- README translations: `README.{lang-code}.md`
- Feature docs: `{FEATURE-NAME}.md`

## Module Organization Patterns

### Frontend Modules
- Each component in its own file
- Related components grouped in subdirectories
- Shared utilities in common directories
- Type definitions co-located with components

### Backend Modules
- Route handlers in `routers/`
- Business logic in `services/`
- Data models in `models/`
- Shared utilities in `utils/`
- Database operations in `db/`

## Asset Organization

### Static Assets (`/public`)
- Images and icons
- Fonts
- Static HTML/CSS
- Favicon and manifest files

### Screenshots (`/screenshots`)
- Application screenshots for documentation
- Feature demonstrations
- UI examples

## Development Workflow Directories

### Scripts (`/scripts`)
- Build scripts
- Deployment scripts
- Development utilities
- Automation tools

### CI/CD (`.github/`)
- GitHub Actions workflows
- Issue templates
- PR templates
- Community guidelines

This structure supports a full-stack application with React/Next.js frontend and Python/FastAPI backend, containerized with Docker, and integrated with multiple AI providers.