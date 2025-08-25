# Consolidated Edge Cases: RAG Fail-Fast Unpack Error Epic

## Overview
This document consolidates all edge cases identified across the 6 parallel tasks for fixing RAG tuple unpacking errors. Each edge case includes detection criteria, impact assessment, and mitigation strategies.

## Critical Edge Cases (System Failure Risk)

### 1. Null/None Query Input
**Source Tasks**: 001, 002, 003
**Scenario**: User passes None or empty string as query
**Current Behavior**: Unpredictable - may crash embedder or return empty
**Impact**: System crash, undefined behavior
**Detection**:
```python
if query is None or query.strip() == "":
    # Handle edge case
```
**Mitigation**: 
- Return `(None, [])` immediately
- Log warning for monitoring
- Document behavior in API

### 2. Embedder Dimension Mismatch
**Source Tasks**: 001, 004
**Scenario**: Embedder returns vectors of different dimensions than FAISS index expects
**Current Behavior**: FAISS throws runtime error
**Impact**: Complete retrieval failure
**Example**:
```python
# OpenAI returns 1536 dimensions
# Google returns 768 dimensions
# Switching providers without re-indexing fails
```
**Detection**:
```python
expected_dim = retriever.index.d
actual_dim = len(embedding_vector)
if expected_dim != actual_dim:
    raise DimensionMismatchError(f"Expected {expected_dim}, got {actual_dim}")
```
**Mitigation**:
- Validate dimensions before retrieval
- Store dimension metadata with index
- Automatic re-embedding if mismatch detected

### 3. Retriever Returns Non-List Types
**Source Tasks**: 002, 003
**Scenario**: Custom retriever implementations return dict, generator, or None
**Current Behavior**: Tuple unpacking fails downstream
**Impact**: Runtime errors in consumers
**Examples**:
```python
# Generator return (lazy evaluation)
return (doc for doc in documents)

# Dict return (with metadata)
return {"documents": [...], "scores": [...]}

# None return (no results)
return None
```
**Mitigation**:
- Type check and conversion in RAG.call()
- Standardize retriever interface
- Add return type validation

## Provider-Specific Edge Cases

### 4. OpenAI Rate Limit Exhaustion
**Source Tasks**: 002, 005
**Scenario**: API rate limits hit during embedding or generation
**Current Behavior**: Exception raised, no graceful degradation
**Impact**: Complete feature unavailability
**Detection**:
```python
try:
    response = openai_client.embeddings.create(...)
except RateLimitError as e:
    # Handle rate limit
```
**Mitigation**:
- Exponential backoff retry
- Fallback to cached embeddings
- Queue requests for later processing

### 5. Google Gemini Multimodal Input
**Source Tasks**: 001, 006
**Scenario**: User passes image + text, but retriever expects text only
**Current Behavior**: Embedding fails or uses only text portion
**Impact**: Degraded retrieval quality
**Example**:
```python
query = {
    "text": "What is in this diagram?",
    "image": base64_encoded_image
}
```
**Mitigation**:
- Detect multimodal input
- Use appropriate embedder
- Document multimodal support matrix

### 6. Ollama Connection Timeout
**Source Tasks**: 001, 004, 005
**Scenario**: Local Ollama server not responding
**Current Behavior**: Long timeout, then connection error
**Impact**: UI freezes, poor user experience
**Detection**:
```python
import requests
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=1)
except requests.exceptions.Timeout:
    # Ollama not responding
```
**Mitigation**:
- Short timeout (1-2 seconds)
- Async health checks
- Automatic fallback to cloud provider

### 7. Azure OpenAI Endpoint Version Mismatch
**Source Tasks**: 001, 006
**Scenario**: API version in config doesn't match endpoint capabilities
**Current Behavior**: Cryptic error messages
**Impact**: Integration appears broken
**Example**:
```python
# Endpoint supports: "2023-05-15"
# Config specifies: "2024-02-01"
# Result: 404 or feature not available
```
**Mitigation**:
- Version negotiation on init
- Clear error messages
- Compatibility matrix in docs

### 8. OpenRouter Model Availability
**Source Tasks**: 002, 005
**Scenario**: Requested model temporarily unavailable
**Current Behavior**: Generic error, no fallback
**Impact**: Feature unavailable
**Detection**:
```python
if "model_not_available" in error_response:
    # Try alternative model
```
**Mitigation**:
- Model fallback chain
- Real-time availability check
- User notification of model switch

## Data Edge Cases

### 9. Empty Document Corpus
**Source Tasks**: 002, 003, 004
**Scenario**: No documents indexed in FAISS
**Current Behavior**: Retriever returns empty list, generator has no context
**Impact**: Always returns `(None, [])`
**Detection**:
```python
if retriever.index.ntotal == 0:
    logger.warning("No documents in index")
    return (None, [])
```
**Mitigation**:
- Check corpus size on init
- Provide helpful error message
- Suggest indexing documents first

### 10. Oversized Query (> Token Limit)
**Source Tasks**: 001, 002
**Scenario**: Query exceeds model's context window
**Current Behavior**: API error or truncation
**Impact**: Incomplete or failed processing
**Example**:
```python
# GPT-3.5: 4096 tokens
# User passes: 5000 token query
```
**Mitigation**:
- Query truncation with warning
- Query summarization
- Chunking for long queries

### 11. Special Characters in Query
**Source Tasks**: 001, 003
**Scenario**: Query contains emojis, RTL text, or control characters
**Current Behavior**: Inconsistent handling across providers
**Impact**: Retrieval quality degradation
**Examples**:
```python
query = "What is 🚀 deployment?"  # Emoji
query = "מה זה תכנות?"  # Hebrew (RTL)
query = "Hello\x00World"  # Null byte
```
**Mitigation**:
- Unicode normalization
- Character filtering
- Provider-specific encoding

### 12. Circular Document References
**Source Tasks**: 004
**Scenario**: Retrieved documents reference each other infinitely
**Current Behavior**: Potential infinite loop in processing
**Impact**: Memory exhaustion, hung process
**Example**:
```python
doc1.metadata["related"] = doc2.id
doc2.metadata["related"] = doc1.id
# Processing related docs loops forever
```
**Mitigation**:
- Visited set tracking
- Maximum depth limit
- Cycle detection algorithm

## Concurrent Access Edge Cases

### 13. Race Condition in Index Updates
**Source Tasks**: 002, 004
**Scenario**: Multiple threads updating FAISS index simultaneously
**Current Behavior**: Index corruption or crashes
**Impact**: Data loss, retrieval failures
**Detection**:
```python
import threading
index_lock = threading.Lock()

with index_lock:
    # Safe index update
    retriever.add_documents(new_docs)
```
**Mitigation**:
- Thread-safe wrapper
- Read-write locks
- Atomic index swapping

### 14. Memory Pressure During Embedding
**Source Tasks**: 001, 005
**Scenario**: Large batch embedding causes OOM
**Current Behavior**: Process killed by OS
**Impact**: Service unavailability
**Example**:
```python
# Embedding 10,000 documents at once
embeddings = embedder.embed_batch(huge_document_list)
# OOM if each embedding is 1536 floats
```
**Mitigation**:
- Batch size limits
- Streaming processing
- Memory monitoring

### 15. Stale Cache After Provider Switch
**Source Tasks**: 003, 005
**Scenario**: Switch provider but cache contains old provider's format
**Current Behavior**: Type mismatches, parsing errors
**Impact**: Incorrect results or crashes
**Detection**:
```python
cache_key = f"{provider}:{model}:{query_hash}"
if cache_provider != current_provider:
    invalidate_cache()
```
**Mitigation**:
- Provider-aware cache keys
- Cache versioning
- Automatic invalidation

## Error Handling Edge Cases

### 16. Partial Retrieval Success
**Source Tasks**: 002, 003, 004
**Scenario**: Some documents retrieved, but others fail
**Current Behavior**: Varies - might return partial or fail entirely
**Impact**: Inconsistent behavior
**Example**:
```python
# 5 documents match query
# 3 retrieve successfully
# 2 fail due to corruption
```
**Mitigation**:
- Return successful subset
- Log failures for debugging
- Include partial flag in response

### 17. Generator Timeout Mid-Response
**Source Tasks**: 002, 005
**Scenario**: LLM times out while generating answer
**Current Behavior**: Partial response or exception
**Impact**: Incomplete answers
**Detection**:
```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Generation timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout
```
**Mitigation**:
- Return partial answer with flag
- Implement streaming responses
- Adjust timeout based on query complexity

### 18. Embedding Service SSL Certificate Issues
**Source Tasks**: 001, 005
**Scenario**: SSL verification fails for API calls
**Current Behavior**: Connection refused
**Impact**: Complete feature failure
**Example**:
```python
# Corporate proxy with self-signed cert
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```
**Mitigation**:
- Certificate pinning
- Optional SSL verification (with warning)
- Proxy configuration support

## Testing Edge Cases

### 19. Mock vs Real Provider Behavior Differences
**Source Tasks**: 004, 006
**Scenario**: Tests pass with mocks but fail with real providers
**Current Behavior**: False confidence in test coverage
**Impact**: Production failures despite passing tests
**Example**:
```python
# Mock returns clean tuple
mock_rag.return_value = ("answer", [doc1, doc2])

# Real provider might return
real_rag.return_value = ("answer", [doc1, doc2, None, doc3])
# Note the None in the list
```
**Mitigation**:
- Integration tests with real providers
- Contract testing
- Behavior recording and replay

### 20. Floating Point Precision in Embeddings
**Source Tasks**: 001, 004
**Scenario**: Embedding vectors have different precision across providers
**Current Behavior**: Similarity scores slightly different
**Impact**: Non-deterministic retrieval
**Example**:
```python
# OpenAI: float32
# Google: float64
# Comparison yields different results
```
**Mitigation**:
- Normalize to consistent precision
- Use epsilon for comparisons
- Document precision requirements

## Performance Edge Cases

### 21. Quadratic Complexity with Large Result Sets
**Source Tasks**: 002, 003
**Scenario**: Retrieved 1000+ documents, processing becomes slow
**Current Behavior**: UI timeout, perceived hang
**Impact**: Poor user experience
**Detection**:
```python
if len(retrieved_docs) > 100:
    logger.warning(f"Large result set: {len(retrieved_docs)} documents")
```
**Mitigation**:
- Result set size limits
- Pagination support
- Progressive rendering

### 22. Cache Avalanche on Deployment
**Source Tasks**: 005
**Scenario**: All caches expire simultaneously after deployment
**Current Behavior**: Thundering herd to embedding service
**Impact**: Service overload, timeouts
**Mitigation**:
- Staggered cache expiration
- Cache warming on deployment
- Circuit breaker pattern

## Migration Edge Cases

### 23. Mixed Version Deployment
**Source Tasks**: 003, 006
**Scenario**: Some services updated, others still on old version
**Current Behavior**: Incompatible return types
**Impact**: Partial system failure
**Example**:
```python
# Service A: Returns tuple (new)
# Service B: Expects list (old)
# Integration fails
```
**Mitigation**:
- Version detection
- Compatibility adapters
- Phased rollout plan

### 24. Legacy Data in Persistent Storage
**Source Tasks**: 003, 004
**Scenario**: Old format data in database/cache
**Current Behavior**: Parsing errors on read
**Impact**: Historical data inaccessible
**Mitigation**:
- Data migration scripts
- Lazy migration on access
- Format version tracking

## Monitoring Edge Cases

### 25. Log Volume Explosion
**Source Tasks**: 005
**Scenario**: Debug logging left on in production
**Current Behavior**: Disk full, log system overwhelmed
**Impact**: Service failure, no logs available
**Example**:
```python
# Every embedding logged (1536 floats)
# 1000 requests/sec = massive log volume
```
**Mitigation**:
- Log sampling
- Adaptive log levels
- Separate debug log stream

### 26. Metrics Cardinality Explosion
**Source Tasks**: 005
**Scenario**: Unique label values for each query
**Current Behavior**: Metrics storage overwhelmed
**Impact**: Monitoring system failure
**Example**:
```python
# Bad: metric{query="unique text for each request"}
# Good: metric{status="success", provider="openai"}
```
**Mitigation**:
- Label value limits
- Aggregation before storage
- Cardinality monitoring

## Summary Statistics

- **Total Edge Cases Identified**: 26
- **Critical Severity**: 8
- **High Severity**: 10
- **Medium Severity**: 8
- **By Category**:
  - Provider-Specific: 5
  - Data-Related: 6
  - Concurrency: 3
  - Error Handling: 3
  - Performance: 2
  - Testing: 2
  - Migration: 2
  - Monitoring: 2
  - System-Level: 1

## Mitigation Priority Matrix

| Priority | Edge Cases | Effort | Impact |
|----------|------------|--------|--------|
| P0 (Immediate) | 1, 2, 3, 9 | Low | Critical |
| P1 (This Sprint) | 4, 5, 6, 13, 16 | Medium | High |
| P2 (Next Sprint) | 7, 8, 10, 11, 14 | Medium | Medium |
| P3 (Backlog) | 12, 15, 17-26 | High | Low-Medium |

## Test Coverage Requirements

Each edge case requires:
1. **Unit Test**: Isolated component behavior
2. **Integration Test**: Full flow validation
3. **Regression Test**: Ensures fix doesn't break
4. **Performance Test**: No degradation under load
5. **Documentation**: User-visible behavior documented

## Implementation Checklist

- [ ] Review all edge cases with team
- [ ] Prioritize based on user impact
- [ ] Create test cases for each edge case
- [ ] Implement mitigations in priority order
- [ ] Document behavior in API reference
- [ ] Add monitoring for edge case occurrence
- [ ] Create runbook for operations team
- [ ] Schedule review after 30 days in production