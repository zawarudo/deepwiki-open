# Edge Cases: RAG Tuple-Unpack Error Fix

## Overview
Focused edge cases for the simplified 5-6 hour implementation plan. Only includes critical cases that must be handled to prevent tuple-unpack errors and ensure basic functionality.

## Priority 0: Must Fix (Causes Tuple-Unpack Errors)

### 1. RAG Returns Non-Tuple Types
**Impact**: Direct tuple-unpack failure
**Current Behavior**: 
```python
# These all cause "not enough values to unpack" error:
result = rag.call(query)  # Returns list: ["doc1", "doc2"]
answer, docs = result  # FAILS!

result = rag.call(query)  # Returns None
answer, docs = result  # FAILS!

result = rag.call(query)  # Returns single string: "answer"
answer, docs = result  # FAILS!
```
**Fix with Normalizer**:
```python
from api.utils import normalize_rag_result

result = rag.call(query)  # Could be anything
answer, docs = normalize_rag_result(result)  # Always works
```
**Test Coverage**: `test/test_normalizer.py`

### 2. Embedder Returns Non-Tuple for FAISS
**Impact**: FAISSRetriever expects tuple, crashes on unpack
**Current Behavior**:
```python
# FAISSRetriever expects: embedding, metadata = embedder(text)
# But providers return:
embedder("text")  # OpenAI: {"data": [{"embedding": [...]}]}
embedder("text")  # Gemini: np.array([...])
embedder("text")  # Ollama: {"embedding": [...]}
embedder("text")  # OpenRouter: [...] (direct list)
```
**Fix with Wrapper**:
```python
from api.embeddings import wrap_embedder

wrapped = wrap_embedder(raw_embedder)
embedding, metadata = wrapped("text")  # Always returns tuple
```
**Test Coverage**: `test/test_embedder_wrapper.py`

### 3. Empty/None Query Input
**Impact**: Undefined behavior, potential crashes
**Current Behavior**: May crash embedder or return unexpected types
**Fix in RAG.call() and __call__()**:
```python
def call(self, query: str, language: str = "en"):
    if not query or not query.strip():
        logger.warning("Empty query received")
        return (None, [])
    # ... rest of implementation

def __call__(self, query: str, language: str = "en"):
    """Syntactic sugar for rag(query) usage"""
    return self.call(query, language)
```
**Test Coverage**: `test/test_rag_tuple_return.py`

## Priority 1: Common Scenarios (Must Handle Gracefully)

### 4. No Documents Retrieved
**Impact**: Must return consistent tuple format
**Scenario**: Query doesn't match any documents
**Required Behavior**:
```python
answer, docs = rag.call("query with no matches")
assert answer is None
assert docs == []
assert isinstance(docs, list)
```
**Test Coverage**: `test/test_integration.py`

### 5. API/Network Errors
**Impact**: Must return tuple even on failure
**Scenarios**:
- Provider API down
- Network timeout
- Rate limit exceeded
**Required Behavior**:
```python
# Even with errors, always return tuple
try:
    answer, docs = rag.call(query)
except:
    # Should not happen - errors handled internally
    pass

# After fix:
answer, docs = rag.call(query)  # Returns (None, []) on error
```
**Test Coverage**: `test/test_rag_tuple_return.py`

### 6. Provider Response Format Variations
**Impact**: Different providers return different formats
**Examples**:
```python
# OpenAI
{"data": [{"embedding": [0.1, 0.2, ...]}]}

# Gemini  
np.array([0.1, 0.2, ...])

# Ollama
{"embedding": [0.1, 0.2, ...]}

# OpenRouter
[0.1, 0.2, ...]  # Direct list
```
**Fix**: Embedder wrapper handles all formats
**Test Coverage**: `test/test_embedder_wrapper.py`

## Priority 2: Edge Cases to Document (Not Fix)

### 7. Concurrent Access
**Current Risk**: Potential race conditions
**Mitigation**: Document as known limitation
**Workaround**: Use single-threaded access or external locking

### 8. Large Result Sets
**Current Risk**: Slow processing with 100+ documents
**Mitigation**: Document recommended limits
**Workaround**: Limit retriever k parameter

### 9. Provider Switching
**Current Risk**: Dimension mismatch if index not rebuilt
**Mitigation**: Document requirement to reindex
**Workaround**: Check dimensions, warn if mismatch

## Test-Driven Development Coverage

### Phase 0 Tests (Normalizer)
```python
# test/test_normalizer.py
def test_normalizer_handles_tuple():
    assert normalize_rag_result(("ans", [])) == ("ans", [])

def test_normalizer_handles_list():
    assert normalize_rag_result(["doc"]) == (None, ["doc"])

def test_normalizer_handles_none():
    assert normalize_rag_result(None) == (None, [])

def test_normalizer_handles_string():
    assert normalize_rag_result("answer") == ("answer", [])
```

### Phase 1 Tests (Core Fixes)
```python
# test/test_rag_tuple_return.py
def test_rag_always_returns_tuple():
    # Test success, empty, error cases

def test_rag_callable_syntax():
    # Test __call__ method works as syntactic sugar
    rag = RAG()
    result1 = rag.call("test")
    result2 = rag("test")  # Should work the same
    assert isinstance(result1, tuple) and isinstance(result2, tuple)
    
# test/test_embedder_wrapper.py
def test_wrapper_handles_all_providers():
    # Test OpenAI, Gemini, Ollama, OpenRouter formats
```

### Phase 3 Tests (Integration)
```python
# test/test_integration.py
def test_end_to_end_with_normalizer():
    # Full pipeline with various return formats
    
def test_wrapped_embedder_with_faiss():
    # FAISS retriever with wrapped embedder

# test/test_performance.py
def test_overhead_under_50_percent():
    # Timing harness to verify performance constraint
    import time
    baseline_start = time.time()
    # Run without normalizer/wrapper
    baseline_time = time.time() - baseline_start
    
    wrapped_start = time.time()
    # Run with normalizer/wrapper
    wrapped_time = time.time() - wrapped_start
    
    overhead = (wrapped_time - baseline_time) / baseline_time
    assert overhead < 0.5, f"Overhead {overhead:.1%} exceeds 50%"
```

## Logging for Edge Case Detection

### JSON Log Format for Debugging
```json
{
    "event": "rag_call",
    "provider": "openai",
    "query_length": 45,
    "status": "success|no_docs|error",
    "doc_count": 3,
    "error_type": "ValueError",
    "has_answer": true
}
```

**Log Output Path**: `/tmp/rag_test.log`

### Log Analysis Commands
```bash
# Check for tuple-unpack errors
grep -i "tuple\|unpack" /tmp/rag_test.log

# Count different error types
grep '"status":"error"' /tmp/rag_test.log | jq -r .error_type | sort | uniq -c

# Find empty retrieval cases
grep '"status":"no_docs"' /tmp/rag_test.log | wc -l
```

## Implementation Checklist

### Must Handle (In Scope - 5-6 hours)
- [ ] Non-tuple returns from RAG → normalizer helper
- [ ] Non-tuple returns from embedder → wrapper function
- [ ] Empty/None queries → early return
- [ ] No documents case → return (None, [])
- [ ] API errors → return (None, [])
- [ ] Provider variations → wrapper handles all
- [ ] Add `__call__` method for syntactic sugar
- [ ] Performance overhead < 50% (verified by timing harness)

### Document Only (Out of Scope - Phase 4)
- [ ] Concurrent access issues → README note (Task 006)
- [ ] Large result sets → Document limits (Task 006)
- [ ] Provider switching → Reindex requirement (Task 006)
- [ ] Memory issues → Monitor externally (Task 006)
- [ ] SSL/Proxy issues → Operations runbook (Task 006)

## Quick Validation Script
```bash
#!/bin/bash
# Save as /tmp/quick_validation.sh
# Run after implementation to verify edge cases handled

echo "=== Edge Case Validation ==="

# Test normalizer with various inputs
python3 -c "
from api.utils import normalize_rag_result
test_cases = [
    (['doc'], 'List input'),
    (('ans', []), 'Tuple input'),
    (None, 'None input'),
    ('string', 'String input'),
]
for input_val, desc in test_cases:
    result = normalize_rag_result(input_val)
    assert isinstance(result, tuple) and len(result) == 2
    print(f'✓ {desc}: {result}')
"

# Test embedder wrapper with provider formats
python3 -c "
from api.embeddings import wrap_embedder
import numpy as np

def test_openai():
    return {'data': [{'embedding': [0.1] * 10}]}

def test_gemini():
    return np.random.rand(10)

def test_list():
    return [0.1] * 10

for name, embedder in [('OpenAI', test_openai), ('Gemini', test_gemini), ('List', test_list)]:
    wrapped = wrap_embedder(embedder)
    result = wrapped('test')
    assert isinstance(result, tuple) and len(result) == 2
    print(f'✓ {name} format handled')
"

echo "=== All edge cases validated ==="
```

## Summary

**Critical Edge Cases**: 6 identified, all addressed by implementation
**Test Coverage**: 100% of critical paths with specific test file mapping:
- Normalizer edge cases → `test/test_normalizer.py`
- RAG contract edge cases → `test/test_rag_tuple_return.py`
- Embedder edge cases → `test/test_embedder_wrapper.py`
- Integration edge cases → `test/test_integration.py`
- Performance validation → `test/test_performance.py`

**Time to Fix**: 5-6 hours total
**Risk Level**: Low (defensive normalizer prevents crashes)
**Log Output**: `/tmp/rag_test.log` (JSON-structured)

Focus: Fix tuple-unpack errors, ensure basic functionality, document the rest.