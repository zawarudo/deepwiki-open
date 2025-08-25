# Test Plan: Comprehensive RAG Testing Suite

## Objective
Create a comprehensive test suite covering all RAG paths including success, empty retrieval, partial failures, and edge cases to ensure no tuple-unpack errors occur.

## Test Categories

### 1. End-to-End Integration Tests

#### Test 1.1: Full RAG Pipeline Success Path
```python
def test_e2e_rag_pipeline_success():
    """Test complete RAG flow from query to response."""
    # Setup: Create test index with documents
    test_docs = [
        {"id": 1, "content": "Python is a programming language"},
        {"id": 2, "content": "JavaScript runs in browsers"},
        {"id": 3, "content": "Rust provides memory safety"}
    ]
    
    # Initialize RAG with test configuration
    config = {
        "provider": "openai",
        "api_key": "test",
        "embedding_model": "text-embedding-ada-002",
        "retriever_k": 3
    }
    
    rag = RAG(config)
    rag.prepare_retriever(test_docs)
    
    # Test query
    query = "What is Python?"
    answer, documents = rag(query)
    
    # Assertions
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert isinstance(documents, list)
    assert len(documents) > 0
    assert "Python" in documents[0]["content"]
```

#### Test 1.2: Multi-Turn Conversation Flow
```python
def test_e2e_multi_turn_conversation():
    """Test RAG with conversation memory."""
    rag = RAG(config)
    
    # First turn
    answer1, docs1 = rag("What is Python?")
    assert answer1 is not None
    
    # Add to dialog memory
    rag.add_dialog_turn("user", "What is Python?")
    rag.add_dialog_turn("assistant", answer1)
    
    # Second turn with context
    answer2, docs2 = rag("What are its main features?")
    assert answer2 is not None
    assert len(rag.dialog) == 4
    
    # Verify context influences response
    assert "Python" in answer2 or "features" in answer2
```

#### Test 1.3: Concurrent Request Handling
```python
def test_e2e_concurrent_requests():
    """Test RAG handles concurrent requests correctly."""
    import asyncio
    
    rag = RAG(config)
    rag.prepare_retriever(test_docs)
    
    async def make_request(query):
        return await asyncio.to_thread(rag, query)
    
    async def run_concurrent():
        queries = [
            "What is Python?",
            "Tell me about JavaScript",
            "Explain Rust",
            "Compare programming languages",
            "What is memory safety?"
        ]
        
        tasks = [make_request(q) for q in queries]
        results = await asyncio.gather(*tasks)
        
        # All should return tuples
        assert all(isinstance(r, tuple) for r in results)
        assert all(len(r) == 2 for r in results)
        
        return results
    
    results = asyncio.run(run_concurrent())
    assert len(results) == 5
```

### 2. Retrieval Path Tests

#### Test 2.1: Normal Retrieval with Documents
```python
def test_retrieval_with_matching_documents():
    """Test retrieval when documents match query."""
    rag = RAG(config)
    
    # Mock retriever with matching documents
    mock_retriever = Mock()
    mock_retriever.retrieve.return_value = [
        {"content": "Relevant doc 1", "score": 0.9},
        {"content": "Relevant doc 2", "score": 0.8}
    ]
    rag.retriever = mock_retriever
    
    answer, docs = rag.call("test query")
    
    assert answer is not None
    assert len(docs) == 2
    assert docs[0]["score"] > docs[1]["score"]
```

#### Test 2.2: Empty Retrieval Handling
```python
def test_retrieval_no_matching_documents():
    """Test when no documents match the query."""
    rag = RAG(config)
    
    # Mock empty retrieval
    mock_retriever = Mock()
    mock_retriever.retrieve.return_value = []
    rag.retriever = mock_retriever
    
    answer, docs = rag.call("unmatched query")
    
    # Should still return tuple
    assert isinstance(answer, (str, type(None)))
    assert docs == []
    
    # May generate answer without context
    if answer:
        assert "I don't have specific information" in answer or \
               "Based on general knowledge" in answer
```

#### Test 2.3: Partial Retrieval Success
```python
def test_retrieval_partial_success():
    """Test when some retrievals succeed, others fail."""
    rag = RAG(config)
    
    call_count = [0]
    def partial_retriever(query):
        call_count[0] += 1
        if call_count[0] % 2 == 0:
            raise Exception("Retrieval error")
        return [{"content": f"Doc {call_count[0]}"}]
    
    mock_retriever = Mock()
    mock_retriever.retrieve.side_effect = partial_retriever
    rag.retriever = mock_retriever
    
    # Make multiple calls
    results = []
    for i in range(5):
        try:
            result = rag.call(f"query {i}")
            results.append(result)
        except:
            results.append((None, []))
    
    # All results should be tuples
    assert all(isinstance(r, tuple) for r in results)
    assert all(len(r) == 2 for r in results)
```

### 3. Embedding Failure Tests

#### Test 3.1: Embedding Service Unavailable
```python
def test_embedding_service_failure():
    """Test RAG when embedding service is down."""
    rag = RAG(config)
    
    # Mock embedder failure
    def failing_embedder(text):
        raise ConnectionError("Embedding service unavailable")
    
    with patch('api.rag.prepare_single_string_embedder', return_value=failing_embedder):
        rag.prepare_retriever(test_docs)
        
        # Should handle gracefully
        answer, docs = rag.call("test query")
        
        assert isinstance(answer, (str, type(None)))
        assert isinstance(docs, list)
```

#### Test 3.2: Embedding Dimension Mismatch
```python
def test_embedding_dimension_mismatch():
    """Test when embeddings have wrong dimensions."""
    rag = RAG(config)
    
    # Mock embedder returning wrong dimensions
    def wrong_dim_embedder(text):
        return np.random.rand(512)  # Wrong: expected 768
    
    with patch('api.rag.prepare_single_string_embedder', return_value=wrong_dim_embedder):
        # Should handle dimension mismatch
        try:
            rag.prepare_retriever(test_docs)
            answer, docs = rag.call("test")
        except ValueError:
            # Expected, but should return tuple
            answer, docs = None, []
        
        assert isinstance(answer, (str, type(None)))
        assert isinstance(docs, list)
```

#### Test 3.3: Embedding Timeout
```python
def test_embedding_timeout():
    """Test RAG handles embedding timeouts."""
    import signal
    
    rag = RAG(config)
    
    def slow_embedder(text):
        time.sleep(10)  # Simulate slow embedding
        return np.random.rand(768)
    
    # Set timeout
    def timeout_handler(signum, frame):
        raise TimeoutError("Embedding timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(1)  # 1 second timeout
    
    try:
        with patch('api.rag.prepare_single_string_embedder', return_value=slow_embedder):
            rag.prepare_retriever(test_docs)
            answer, docs = rag.call("test")
    except TimeoutError:
        answer, docs = None, []
    finally:
        signal.alarm(0)
    
    assert isinstance(answer, (str, type(None)))
    assert isinstance(docs, list)
```

### 4. Provider-Specific Tests

#### Test 4.1: OpenAI Provider Full Test
```python
def test_openai_provider_complete_flow():
    """Test OpenAI provider with all components."""
    config = {
        "provider": "openai",
        "api_key": "test",
        "model": "gpt-4",
        "embedding_model": "text-embedding-ada-002"
    }
    
    rag = RAG(config)
    
    # Mock OpenAI responses
    mock_embedding = {"data": [{"embedding": [0.1] * 1536}]}
    mock_completion = {
        "choices": [{
            "message": {"content": "OpenAI response"}
        }]
    }
    
    with patch('openai.Embedding.create', return_value=mock_embedding):
        with patch('openai.ChatCompletion.create', return_value=mock_completion):
            rag.prepare_retriever(test_docs)
            answer, docs = rag("test query")
            
            assert answer == "OpenAI response"
            assert isinstance(docs, list)
```

#### Test 4.2: Gemini Provider Full Test
```python
def test_gemini_provider_complete_flow():
    """Test Google Gemini provider."""
    config = {
        "provider": "google",
        "api_key": "test",
        "model": "gemini-pro"
    }
    
    rag = RAG(config)
    
    # Mock Gemini responses
    mock_embedding = np.random.rand(768)
    mock_response = "Gemini response"
    
    with patch.object(rag, '_call_gemini', return_value=mock_response):
        with patch('api.rag.prepare_single_string_embedder', 
                  return_value=lambda x: mock_embedding):
            rag.prepare_retriever(test_docs)
            answer, docs = rag("test query")
            
            assert answer == "Gemini response"
            assert isinstance(docs, list)
```

#### Test 4.3: Provider Switching
```python
def test_provider_switching():
    """Test switching between providers."""
    providers = ["openai", "google", "ollama", "openrouter"]
    
    for provider in providers:
        config = {"provider": provider, "api_key": "test"}
        rag = RAG(config)
        
        # Mock provider response
        with patch.object(rag, f'_call_{provider}', return_value=f"{provider} response"):
            answer, docs = rag.call("test")
            
            assert isinstance(answer, (str, type(None)))
            assert isinstance(docs, list)
```

### 5. Error Recovery Tests

#### Test 5.1: Cascading Failure Recovery
```python
def test_cascading_failure_recovery():
    """Test RAG recovers from cascading failures."""
    rag = RAG(config)
    
    failures = []
    
    # Simulate various failures
    def fail_then_succeed(component):
        if len(failures) < 3:
            failures.append(component)
            raise Exception(f"{component} failed")
        return "Success after failures"
    
    with patch.object(rag, '_retrieve_documents', 
                     side_effect=lambda q: fail_then_succeed("retriever")):
        # First calls fail, later succeed
        for i in range(5):
            answer, docs = rag.call("test")
            assert isinstance(answer, (str, type(None)))
            assert isinstance(docs, list)
```

#### Test 5.2: Memory/Resource Exhaustion
```python
def test_memory_exhaustion_handling():
    """Test RAG handles memory exhaustion."""
    rag = RAG(config)
    
    # Create large documents
    huge_docs = [{"content": "x" * 1000000} for _ in range(100)]
    
    try:
        rag.prepare_retriever(huge_docs)
        # Try with limited memory
        answer, docs = rag.call("test")
    except MemoryError:
        answer, docs = None, []
    
    assert isinstance(answer, (str, type(None)))
    assert isinstance(docs, list)
```

### 6. Stress Tests

#### Test 6.1: High Volume Sequential
```python
def test_high_volume_sequential():
    """Test RAG with high volume of sequential requests."""
    rag = RAG(config)
    rag.prepare_retriever(test_docs)
    
    errors = []
    for i in range(1000):
        try:
            answer, docs = rag(f"query {i}")
            assert isinstance(answer, (str, type(None)))
            assert isinstance(docs, list)
        except Exception as e:
            errors.append(e)
    
    # Should handle most requests
    assert len(errors) < 10  # Less than 1% error rate
```

#### Test 6.2: Rapid Fire Requests
```python
def test_rapid_fire_requests():
    """Test RAG with rapid-fire requests."""
    import threading
    
    rag = RAG(config)
    rag.prepare_retriever(test_docs)
    
    results = []
    errors = []
    
    def rapid_request():
        for _ in range(10):
            try:
                result = rag("quick query")
                results.append(result)
            except Exception as e:
                errors.append(e)
    
    threads = [threading.Thread(target=rapid_request) for _ in range(10)]
    
    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - start
    
    # Should complete quickly
    assert duration < 10  # seconds
    assert len(results) > 90  # Most succeed
    assert all(isinstance(r, tuple) for r in results)
```

### 7. Edge Case Tests

#### Test 7.1: Malicious Input Handling
```python
def test_malicious_input_handling():
    """Test RAG handles malicious inputs safely."""
    rag = RAG(config)
    
    malicious_inputs = [
        "x" * 1000000,  # Very long input
        "<script>alert('xss')</script>",  # XSS attempt
        "'; DROP TABLE users; --",  # SQL injection
        "\x00\x01\x02",  # Binary data
        "\\..\\..\\etc\\passwd",  # Path traversal
    ]
    
    for malicious in malicious_inputs:
        answer, docs = rag.call(malicious)
        
        # Should handle without crashing
        assert isinstance(answer, (str, type(None)))
        assert isinstance(docs, list)
        
        # Should not reflect malicious input
        if answer:
            assert malicious not in answer
```

#### Test 7.2: Unicode and Encoding Edge Cases
```python
def test_unicode_edge_cases():
    """Test RAG with various unicode edge cases."""
    rag = RAG(config)
    
    unicode_tests = [
        "Z̤̮̠̙̦̥̒̂͐̾A̭̺̰̯͈̅̂̈́L̜̩̞̟̄̊́̕G̱̩̘̅̃̍O̧̲̮̊̐̂",  # Zalgo text
        "𝕌𝕟𝕚𝕔𝕠𝕕𝕖",  # Math bold
        "🏳️‍🌈🏳️‍⚧️",  # Complex emoji
        "\uFEFF",  # Zero-width space
        "א״ב״ג״",  # RTL text
    ]
    
    for text in unicode_tests:
        answer, docs = rag.call(text)
        assert isinstance(answer, (str, type(None)))
        assert isinstance(docs, list)
```

### 8. Regression Tests

#### Test 8.1: Previous Bug Scenarios
```python
def test_regression_tuple_unpack_error():
    """Regression test for tuple unpack error."""
    rag = RAG(config)
    
    # Scenario that caused original error
    mock_retriever = Mock()
    mock_retriever.retrieve.return_value = ["doc1"]  # Returns list, not tuple
    rag.retriever = mock_retriever
    
    # Should not raise unpacking error
    try:
        answer, docs = rag("query")  # This used to fail
        success = True
    except ValueError as e:
        if "unpack" in str(e):
            success = False
        else:
            raise
    
    assert success, "Regression: tuple unpack error returned"
```

#### Test 8.2: Memory Leak Regression
```python
def test_regression_memory_leak():
    """Test for memory leak regression."""
    import gc
    import tracemalloc
    
    tracemalloc.start()
    rag = RAG(config)
    
    # Baseline
    gc.collect()
    snapshot1 = tracemalloc.take_snapshot()
    
    # Many calls
    for _ in range(100):
        answer, docs = rag.call("test")
        del answer, docs
    
    # Check memory
    gc.collect()
    snapshot2 = tracemalloc.take_snapshot()
    
    stats = snapshot2.compare_to(snapshot1, 'lineno')
    total_diff = sum(stat.size_diff for stat in stats)
    
    # Should not leak significantly (< 10MB)
    assert total_diff < 10 * 1024 * 1024
```

## Test Execution Plan

### Phase 1: Core Functionality (Priority: Critical)
- Tests 1.1-1.3: End-to-end flows
- Tests 2.1-2.3: Retrieval paths
- Must pass before deployment

### Phase 2: Error Handling (Priority: High)
- Tests 3.1-3.3: Embedding failures
- Tests 5.1-5.2: Recovery mechanisms
- Ensure resilience

### Phase 3: Provider Coverage (Priority: High)
- Tests 4.1-4.3: All providers
- Ensure compatibility

### Phase 4: Stress Testing (Priority: Medium)
- Tests 6.1-6.2: Load testing
- Performance validation

### Phase 5: Edge Cases (Priority: Medium)
- Tests 7.1-7.2: Unusual inputs
- Security validation

### Phase 6: Regression (Priority: Low)
- Tests 8.1-8.2: Previous bugs
- Ensure fixes persist

## Success Metrics
- 100% of critical tests passing
- Zero tuple-unpack errors across all scenarios
- < 1% error rate under stress
- All providers working correctly
- Memory usage stable

## Test Infrastructure Requirements
- Mock frameworks for external services
- Test document corpus
- Performance monitoring tools
- Memory profiling tools
- Concurrent testing framework

## Dependencies
- pytest
- pytest-asyncio
- unittest.mock
- numpy
- faiss-cpu
- time, threading, signal, gc, tracemalloc (stdlib)