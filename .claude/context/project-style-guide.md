---
created: 2025-08-23T07:29:41Z
last_updated: 2025-08-23T07:29:41Z
version: 1.0
author: Claude Code PM System
---

# Project Style Guide

## Code Style Conventions

### TypeScript/JavaScript

#### File Naming
- **Components**: `PascalCase.tsx` (e.g., `WikiTreeView.tsx`)
- **Hooks**: `use{HookName}.ts` (e.g., `useProcessedProjects.ts`)
- **Utilities**: `camelCase.ts` (e.g., `formatDate.ts`)
- **Constants**: `UPPER_SNAKE_CASE.ts` (e.g., `API_ENDPOINTS.ts`)
- **Types**: `PascalCase.types.ts` (e.g., `Repository.types.ts`)
- **Tests**: `{filename}.test.ts` or `{filename}.spec.ts`

#### Code Structure
```typescript
// Import order
import React from 'react';                    // 1. React imports
import { useState, useEffect } from 'react';  // 2. React hooks
import NextLink from 'next/link';             // 3. Framework imports
import { Button } from '@/components';        // 4. Internal components
import { formatDate } from '@/utils';         // 5. Internal utilities
import styles from './Component.module.css';  // 6. Styles
import type { ComponentProps } from './types'; // 7. Types

// Component definition
export const ComponentName: React.FC<ComponentProps> = ({ prop1, prop2 }) => {
  // Hooks first
  const [state, setState] = useState(false);
  const data = useCustomHook();
  
  // Event handlers
  const handleClick = () => {
    // Implementation
  };
  
  // Render
  return (
    <div className={styles.container}>
      {/* JSX content */}
    </div>
  );
};
```

#### Variable Naming
- **Constants**: `UPPER_SNAKE_CASE`
- **Functions**: `camelCase`
- **React Components**: `PascalCase`
- **Boolean variables**: `is{Condition}` or `has{Property}`
- **Event handlers**: `handle{Event}` or `on{Event}`

#### Comments
- Use JSDoc for function documentation
- Inline comments for complex logic only
- No commented-out code in production
- TODO comments must include assignee and date

### Python

#### File Naming
- **Modules**: `snake_case.py` (e.g., `repository_analyzer.py`)
- **Classes**: Inside files use `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private functions**: `_snake_case`

#### Code Structure
```python
"""Module docstring describing the module's purpose."""

# Standard library imports
import os
import sys
from typing import Optional, List, Dict

# Third-party imports
import fastapi
from pydantic import BaseModel

# Local imports
from .models import Repository
from .utils import process_data

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Classes
class RepositoryService:
    """Service for handling repository operations."""
    
    def __init__(self, config: Dict):
        """Initialize the service with configuration."""
        self.config = config
    
    def analyze_repository(self, url: str) -> Repository:
        """Analyze a repository and return structured data."""
        # Implementation
        pass

# Functions
def process_repository(url: str) -> Optional[Dict]:
    """Process a repository URL and return metadata."""
    # Implementation
    pass
```

#### Type Hints
- Always use type hints for function parameters and returns
- Use `Optional[]` for nullable types
- Use `List[]`, `Dict[]`, `Set[]` from typing module
- Use Pydantic models for API schemas

#### Error Handling
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Specific error occurred: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.exception("Unexpected error")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### CSS/Styling

#### Tailwind CSS Classes
- Use utility classes directly in JSX
- Group related utilities logically
- Extract common patterns to components

```jsx
// Good
<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-md">

// Better for repeated patterns
const Card = ({ children }) => (
  <div className="p-4 bg-white rounded-lg shadow-md">
    {children}
  </div>
);
```

#### CSS Modules (when needed)
```css
/* ComponentName.module.css */
.container {
  /* Use kebab-case for class names */
}

.container-header {
  /* Nested naming with hyphens */
}
```

## Git Conventions

### Branch Naming
- `feature/{description}` - New features
- `fix/{description}` - Bug fixes
- `refactor/{description}` - Code refactoring
- `docs/{description}` - Documentation updates
- `test/{description}` - Test additions/updates

### Commit Messages
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

**Examples**:
```
feat(api): add repository analysis endpoint

Implement new endpoint for analyzing repository structure
and generating documentation metadata.

Closes #123
```

### Pull Request Guidelines
- Clear, descriptive title
- Reference related issues
- Include screenshots for UI changes
- List breaking changes
- Update documentation as needed

## Documentation Standards

### Code Documentation
- All public functions must have docstrings/JSDoc
- Complex algorithms need inline comments
- README files for each major module
- API endpoints must be documented

### Markdown Files
- Use proper heading hierarchy (# > ## > ###)
- Include table of contents for long documents
- Use code blocks with language specification
- Add diagrams where helpful

### API Documentation
```python
@router.post("/analyze", response_model=AnalysisResult)
async def analyze_repository(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze a repository and generate documentation.
    
    Args:
        request: Analysis request containing repository URL
        background_tasks: FastAPI background task manager
    
    Returns:
        AnalysisResult with generated documentation
    
    Raises:
        HTTPException: If repository cannot be accessed
    """
```

## Testing Standards

### Test File Organization
```
tests/
├── unit/
│   ├── test_services.py
│   └── test_utils.py
├── integration/
│   ├── test_api.py
│   └── test_database.py
└── e2e/
    └── test_workflows.py
```

### Test Naming
- Test functions: `test_{function_name}_{scenario}`
- Test classes: `Test{ClassName}`
- Fixtures: `{resource}_fixture`

### Test Structure
```python
def test_analyze_repository_success():
    """Test successful repository analysis."""
    # Arrange
    repository_url = "https://github.com/example/repo"
    expected_result = {...}
    
    # Act
    result = analyze_repository(repository_url)
    
    # Assert
    assert result == expected_result
```

## Environment & Configuration

### Environment Variables
- Use `.env` for local development
- Never commit `.env` files
- Document all variables in `.env.example`
- Use descriptive names: `{SERVICE}_{PROPERTY}`

### Configuration Files
- Keep configuration in dedicated files
- Use environment-specific configs
- Version control config templates
- Document configuration options

## Performance Guidelines

### Frontend
- Lazy load components when possible
- Memoize expensive computations
- Use virtual scrolling for long lists
- Optimize images and assets

### Backend
- Use async/await for I/O operations
- Implement caching strategies
- Paginate large result sets
- Use database indexes appropriately

## Security Practices

### General
- Never commit secrets or API keys
- Validate all user inputs
- Use parameterized queries
- Implement rate limiting
- Keep dependencies updated

### API Security
- Use HTTPS in production
- Implement proper authentication
- Validate request payloads
- Sanitize responses
- Log security events

## Accessibility Standards

### UI Components
- Use semantic HTML elements
- Include ARIA labels where needed
- Ensure keyboard navigation
- Maintain color contrast ratios
- Provide alt text for images

## Error Messages

### User-Facing
- Clear, actionable messages
- No technical jargon
- Suggest next steps
- Include support contact if needed

### Developer-Facing
- Include error codes
- Detailed stack traces in development
- Structured logging format
- Correlation IDs for tracking

## Code Review Checklist

### Before Submitting
- [ ] Code follows style guide
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No console.log or print statements
- [ ] Security considerations addressed
- [ ] Performance impact considered

### Review Focus
- Correctness and logic
- Code clarity and maintainability
- Test coverage
- Security implications
- Performance considerations

## Continuous Improvement

### Regular Reviews
- Monthly style guide reviews
- Quarterly dependency updates
- Annual architecture reviews
- Continuous documentation updates

### Feedback Loop
- Collect developer feedback
- Monitor code quality metrics
- Update guidelines based on learnings
- Share best practices

This style guide ensures consistency and quality across the DeepWiki-Open codebase, making it easier for contributors to understand and maintain the project.