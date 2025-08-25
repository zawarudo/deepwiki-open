# AI-GETTING-STARTED-COMMANDS.MD

> Test-Driven Development (TDD) Command Reference for AI Agents and Developers

## Core Philosophy: Red-Green-Refactor Loop

Every development task follows the TDD cycle:
1. **RED**: Write a failing test that defines expected behavior
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Improve code quality while keeping tests green

## 🧪 TDD Quick Start Commands

### Step 1: Write Failing Test First
```bash
# Create a new test file
touch test/test_${FEATURE_NAME}.py

# Run test to see it fail (RED phase)
python -m pytest test/test_${FEATURE_NAME}.py -v

# Log the failure for debugging
python test/test_${FEATURE_NAME}.py > tests/logs/${FEATURE_NAME}_red.log 2>&1
```

### Step 2: Implement Minimal Fix
```bash
# Edit the implementation
vim api/${MODULE_NAME}.py

# Run test again (aiming for GREEN)
python -m pytest test/test_${FEATURE_NAME}.py -v

# Capture success
python test/test_${FEATURE_NAME}.py > tests/logs/${FEATURE_NAME}_green.log 2>&1
```

### Step 3: Refactor and Validate
```bash
# Run full test suite to ensure no regression
python -m pytest test/ -v

# Check code quality
ruff check api/
```

## 🐳 Docker TDD Commands

### Build & Test Cycle

#### TDD Docker Workflow

```bash
# 1. Write failing test (outside container)
cat > test/test_new_feature.py << 'EOF'
import pytest
from api.module import function_to_test

def test_expected_behavior():
    """Test should fail initially (RED phase)"""
    result = function_to_test("input")
    assert result == "expected_output"  # This will fail
EOF

# 2. Run test in Docker (see it fail)
docker-compose run --rm deepwiki python -m pytest test/test_new_feature.py -v

# 3. Implement fix
# Edit api/module.py to make test pass

# 4. Rebuild and test (GREEN phase)
docker-compose build
docker-compose run --rm deepwiki python -m pytest test/test_new_feature.py -v

# 5. Run full test suite (ensure no regression)
docker-compose run --rm deepwiki python -m pytest test/ -v
```

### Complete Docker Rebuild & Test
```bash
# Full rebuild and test sequence
docker-compose down                    # Stop existing containers
docker-compose build --no-cache        # Force rebuild with changes
docker-compose up -d                   # Start services in background
sleep 10                               # Wait for services to be ready

# Run test suite inside container
docker-compose exec deepwiki python -m pytest test/ -v

# Check specific test
docker-compose exec deepwiki python -m pytest test/test_emergency_fix.py -v

# Run validation scripts
docker-compose exec deepwiki python scripts/validate_embeddings.py --dry-run

# Test API endpoint
curl -X GET http://localhost:8001/health
```

## 🔄 Continuous TDD Loop

### Automated Test Runner
```bash
# Watch for changes and auto-run tests
while true; do
    inotifywait -e modify api/*.py test/*.py
    clear
    echo "========================================="
    echo "Running TDD Loop: $(date)"
    echo "========================================="
    python -m pytest test/ -v --tb=short
    echo ""
    echo "Waiting for changes..."
done
```

### Test Logging System
```bash
# Use the project's test-and-log script
bash .claude/scripts/test-and-log.sh test/test_feature.py feature_v1.log

# View test results
tail -f tests/logs/feature_v1.log

# Compare test runs
diff tests/logs/feature_v1.log tests/logs/feature_v2.log
```

## 🎯 Use Case: Emergency Bug Fix (TDD)

### 1. Reproduce Bug with Test
```bash
# Create test that reproduces the bug
cat > test/test_bug_reproduction.py << 'EOF'
import pytest
from api.google_embedding_client import GoogleEmbeddingClient

def test_no_empty_vectors_on_api_failure():
    """Bug: System creates empty vectors on API failure"""
    client = GoogleEmbeddingClient()
    
    # This should raise an exception, not return empty vectors
    with pytest.raises(EmbeddingGenerationError):
        # Simulate API failure scenario
        result = client.get_embeddings(["test"], simulate_failure=True)
EOF

# Run test to confirm bug exists (test should fail)
python -m pytest test/test_bug_reproduction.py -v
```

### 2. Fix Bug (Make Test Pass)
```bash
# Implement fix in the code
# Edit api/google_embedding_client.py

# Test the fix
python -m pytest test/test_bug_reproduction.py -v

# Should now pass (GREEN)
```

### 3. Add Regression Tests
```bash
# Add comprehensive test coverage
cat > test/test_embedding_validation.py << 'EOF'
def test_dimension_validation():
    """Ensure all embeddings are 768-dimensional"""
    # Test implementation

def test_retry_logic():
    """Verify retry with exponential backoff"""
    # Test implementation

def test_error_messages():
    """Check error messages are informative"""
    # Test implementation
EOF

# Run all tests
python -m pytest test/test_embedding_validation.py -v
```

## 🤖 Agent Development Workflow

### TDD for Agent Tasks
```bash
# 1. Analyze task requirements
cat .claude/epics/fix-api-pipeline-errors/000.md

# 2. Create test suite for task
python -c "
# Generate test cases from requirements
requirements = open('.claude/epics/fix-api-pipeline-errors/000.md').read()
# Parse acceptance criteria and create test stubs
"

# 3. Launch agent with TDD focus
# Agent should:
# - Write tests first
# - Run tests to see failures
# - Implement fixes
# - Verify tests pass
```

### Agent Debugging Commands
```bash
# Monitor agent progress
tail -f .claude/epics/*/execution-status.md

# Check agent test results
find .claude/epics -name "*.log" -exec tail -20 {} \;

# Validate agent changes
git diff --stat
git diff api/

# Run agent's tests
python -m pytest test/test_emergency_fix.py -v --tb=short
```

## 📊 Test Coverage Commands

```bash
# Run tests with coverage
python -m pytest test/ --cov=api --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Check specific module coverage
python -m pytest test/ --cov=api.google_embedding_client --cov-report=term-missing
```

## 🔍 Validation & Integration Testing

### Quick Validation Tests
```bash
# Validate embeddings
python scripts/validate_embeddings.py --dry-run

# Test FAISS index creation
python scripts/test_faiss_index.py

# Monitor embedding generation
python scripts/monitor_embeddings.py

# Regenerate embeddings if needed
python scripts/regenerate_embeddings.py --batch-size 10
```

### End-to-End Testing
```bash
# Full pipeline test
curl -X POST http://localhost:8001/chat/completions/stream \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test query"}]}' \
  | jq .

# RAG system test
curl -X POST http://localhost:8001/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the embedding system work?"}' \
  | jq .
```

## 🚀 Production Deployment Testing

### Pre-Deployment Checklist
```bash
# 1. Run full test suite
python -m pytest test/ -v --strict-markers

# 2. Check for empty vectors
python -c "
from api.google_embedding_client import GoogleEmbeddingClient
client = GoogleEmbeddingClient()
embeddings = client.get_embeddings(['test'])
assert len(embeddings[0].embedding) == 768
print('✅ Embedding validation passed')
"

# 3. Verify FAISS index
python -c "
import faiss
import numpy as np
index = faiss.IndexFlatL2(768)
vectors = np.random.rand(10, 768).astype('float32')
index.add(vectors)
assert index.ntotal == 10
print('✅ FAISS index creation passed')
"

# 4. Load test the API
ab -n 100 -c 10 http://localhost:8001/health
```

## 💡 TDD Best Practices

### Test Naming Convention
```bash
test_<what>_<condition>_<expected_result>.py
# Example: test_embedding_api_failure_raises_exception.py
```

### Test Organization
```
test/
├── unit/           # Fast, isolated tests
├── integration/    # Component interaction tests
├── e2e/           # End-to-end workflow tests
└── logs/          # Test execution logs
```

### Commit Message Format
```bash
git commit -m "Test: Add failing test for <feature>
- Red phase: Test demonstrates expected behavior
- Next: Implement feature to make test pass"

git commit -m "Fix: Implement <feature> to pass test
- Green phase: Minimal code to pass test
- All tests passing"

git commit -m "Refactor: Improve <feature> implementation
- Maintain green tests
- Improve code quality/performance"
```

## 🛠️ Troubleshooting

### Common Issues and Solutions

```bash
# Issue: Tests pass locally but fail in Docker
# Solution: Ensure environment consistency
docker-compose run --rm deepwiki pip list > docker_packages.txt
pip list > local_packages.txt
diff local_packages.txt docker_packages.txt

# Issue: Slow test execution
# Solution: Run tests in parallel
python -m pytest test/ -n auto

# Issue: Flaky tests
# Solution: Add retry logic
python -m pytest test/ --reruns 3 --reruns-delay 1

# Issue: Can't reproduce production bug
# Solution: Capture production state
docker-compose exec deepwiki python -c "
import pickle
# Capture state that causes bug
state = {'embeddings': [...], 'config': {...}}
pickle.dump(state, open('bug_state.pkl', 'wb'))
"
```

## 📚 Additional Resources

- **pytest Documentation**: https://docs.pytest.org/
- **Docker Compose Reference**: https://docs.docker.com/compose/
- **TDD Best Practices**: https://testdriven.io/
- **Project README**: [README.md](./README.md)
- **Ollama Setup**: [Ollama-instruction.md](./Ollama-instruction.md)

---

*Remember: No code without tests. No commit without green. No feature without validation.*