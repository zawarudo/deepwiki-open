# Test Plan: Query-Embedder Adapter for FAISSRetriever

## Objective
Ensure the query-embedder adapter consistently returns a 2-tuple structure preventing tuple-unpack errors in FAISSRetriever.

## Test Categories

### 1. Unit Tests - Adapter Behavior

#### Test 1.1: Basic Wrapper Functionality
```python
def test_embedder_adapter_wraps_single_return():
    """Verify adapter converts single embedding to 2-tuple."""
    # Given: Raw embedder returns single numpy array
    raw_embedder = lambda text: np.array([0.1, 0.2, 0.3])
    adapter = EmbedderAdapter(raw_embedder)
    
    # When: Adapter processes query
    result = adapter("test query")
    
    # Then: Returns 2-tuple (embedding, metadata)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert np.array_equal(result[0], np.array([0.1, 0.2, 0.3]))
    assert result[1] is None or isinstance(result[1], dict)
```

#### Test 1.2: Already-Tuple Passthrough
```python
def test_adapter_preserves_existing_tuple():
    """Verify adapter doesn't double-wrap already-correct returns."""
    # Given: Embedder already returns 2-tuple
    raw_embedder = lambda text: (np.array([0.1, 0.2]), {"provider": "openai"})
    adapter = EmbedderAdapter(raw_embedder)
    
    # When: Adapter processes
    result = adapter("test")
    
    # Then: Original tuple preserved
    assert len(result) == 2
    assert result[1]["provider"] == "openai"
```

#### Test 1.3: Empty String Handling
```python
def test_adapter_handles_empty_input():
    """Verify adapter handles empty/None inputs gracefully."""
    raw_embedder = lambda text: np.zeros(768) if text else None
    adapter = EmbedderAdapter(raw_embedder)
    
    # Test empty string
    result = adapter("")
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    # Test None
    result = adapter(None)
    assert isinstance(result, tuple)
    assert len(result) == 2
```

### 2. Integration Tests - Provider Compatibility

#### Test 2.1: OpenAI Provider
```python
def test_adapter_with_openai_embedder():
    """Test adapter with actual OpenAI embedder behavior."""
    # Mock OpenAI response structure
    mock_openai_response = {
        "data": [{"embedding": [0.1] * 1536}],
        "usage": {"total_tokens": 5}
    }
    
    embedder = create_openai_embedder(api_key="test")
    adapter = EmbedderAdapter(embedder)
    
    with patch('openai.Embedding.create', return_value=mock_openai_response):
        result = adapter("test query")
        assert len(result) == 2
        assert len(result[0]) == 1536
```

#### Test 2.2: Google Gemini Provider
```python
def test_adapter_with_gemini_embedder():
    """Test adapter with Gemini embedder behavior."""
    # Gemini returns 768-dim embeddings
    mock_gemini_embedding = np.random.rand(768)
    
    embedder = create_gemini_embedder(api_key="test")
    adapter = EmbedderAdapter(embedder)
    
    with patch.object(embedder, 'embed', return_value=mock_gemini_embedding):
        result = adapter("test query")
        assert len(result) == 2
        assert len(result[0]) == 768
```

#### Test 2.3: Ollama Local Provider
```python
def test_adapter_with_ollama_embedder():
    """Test adapter with Ollama local embeddings."""
    mock_ollama_response = {"embedding": [0.2] * 384}
    
    embedder = create_ollama_embedder(model="llama2")
    adapter = EmbedderAdapter(embedder)
    
    with patch('requests.post', return_value=Mock(json=lambda: mock_ollama_response)):
        result = adapter("test query")
        assert len(result) == 2
        assert len(result[0]) == 384
```

### 3. Error Handling Tests

#### Test 3.1: Provider Timeout
```python
def test_adapter_handles_timeout():
    """Verify adapter handles embedding timeouts gracefully."""
    def slow_embedder(text):
        time.sleep(10)
        return np.zeros(768)
    
    adapter = EmbedderAdapter(slow_embedder, timeout=1)
    
    result = adapter("test")
    assert len(result) == 2
    assert result[0] is None or len(result[0]) == 768
    assert result[1].get("error") == "timeout"
```

#### Test 3.2: Provider API Error
```python
def test_adapter_handles_api_errors():
    """Verify adapter handles API failures."""
    def failing_embedder(text):
        raise Exception("API rate limit exceeded")
    
    adapter = EmbedderAdapter(failing_embedder)
    
    result = adapter("test")
    assert len(result) == 2
    assert result[0] is None or isinstance(result[0], np.ndarray)
    assert "error" in result[1] or result[1] is None
```

#### Test 3.3: Malformed Response
```python
def test_adapter_handles_malformed_response():
    """Verify adapter handles unexpected response formats."""
    test_cases = [
        None,  # None response
        [],    # Empty list
        "embedding",  # String instead of array
        {"unexpected": "format"},  # Dict without embedding
        [1, 2, 3, 4, 5],  # List of wrong length (too many items)
    ]
    
    for malformed_response in test_cases:
        embedder = lambda x: malformed_response
        adapter = EmbedderAdapter(embedder)
        
        result = adapter("test")
        assert isinstance(result, tuple), f"Failed for {malformed_response}"
        assert len(result) == 2, f"Wrong length for {malformed_response}"
```

### 4. FAISSRetriever Integration Tests

#### Test 4.1: Retriever with Adapted Embedder
```python
def test_faiss_retriever_with_adapter():
    """Verify FAISSRetriever works with adapted embedder."""
    # Create mock FAISS index
    index = faiss.IndexFlatL2(768)
    index.add(np.random.rand(10, 768).astype('float32'))
    
    # Create retriever with adapted embedder
    raw_embedder = lambda x: np.random.rand(768)
    adapted_embedder = EmbedderAdapter(raw_embedder)
    
    retriever = FAISSRetriever(
        index=index,
        embedder=adapted_embedder,
        k=5
    )
    
    # Should not raise tuple-unpack error
    results = retriever.retrieve("test query")
    assert len(results) <= 5
```

#### Test 4.2: Retriever Error Recovery
```python
def test_retriever_continues_after_embedding_failure():
    """Verify retriever handles embedding failures gracefully."""
    index = faiss.IndexFlatL2(768)
    
    # Embedder that fails intermittently
    call_count = [0]
    def flaky_embedder(text):
        call_count[0] += 1
        if call_count[0] % 2 == 0:
            raise Exception("Network error")
        return np.random.rand(768)
    
    adapter = EmbedderAdapter(flaky_embedder)
    retriever = FAISSRetriever(index=index, embedder=adapter, k=5)
    
    # Should handle failures without crashing
    for _ in range(5):
        try:
            retriever.retrieve("test")
        except:
            pass  # Expected for some calls
```

### 5. Performance Tests

#### Test 5.1: Adapter Overhead
```python
def test_adapter_minimal_overhead():
    """Verify adapter adds minimal performance overhead."""
    raw_embedder = lambda x: np.random.rand(768)
    adapter = EmbedderAdapter(raw_embedder)
    
    # Measure raw embedder time
    start = time.time()
    for _ in range(100):
        raw_embedder("test")
    raw_time = time.time() - start
    
    # Measure adapted embedder time
    start = time.time()
    for _ in range(100):
        adapter("test")
    adapted_time = time.time() - start
    
    # Overhead should be < 10%
    overhead = (adapted_time - raw_time) / raw_time
    assert overhead < 0.1, f"Overhead too high: {overhead:.2%}"
```

#### Test 5.2: Memory Usage
```python
def test_adapter_memory_efficiency():
    """Verify adapter doesn't leak memory."""
    import tracemalloc
    
    raw_embedder = lambda x: np.random.rand(768)
    adapter = EmbedderAdapter(raw_embedder)
    
    tracemalloc.start()
    
    # Run many iterations
    for _ in range(1000):
        result = adapter("test query")
        del result
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Memory usage should be reasonable (< 100MB)
    assert peak < 100 * 1024 * 1024
```

### 6. Edge Cases

#### Test 6.1: Unicode and Special Characters
```python
def test_adapter_handles_unicode():
    """Test adapter with various character encodings."""
    test_strings = [
        "Hello 世界",  # Chinese
        "Привет мир",  # Russian
        "مرحبا بالعالم",  # Arabic
        "🚀 Emoji test 🎉",  # Emojis
        "Special chars: @#$%^&*()",
        "\n\t\r Whitespace \n\n",
    ]
    
    raw_embedder = lambda x: np.random.rand(768)
    adapter = EmbedderAdapter(raw_embedder)
    
    for text in test_strings:
        result = adapter(text)
        assert len(result) == 2, f"Failed for: {text}"
```

#### Test 6.2: Very Long Inputs
```python
def test_adapter_handles_long_text():
    """Test adapter with texts exceeding token limits."""
    # Create text longer than typical token limit
    long_text = "word " * 10000  # ~10k words
    
    raw_embedder = lambda x: np.random.rand(768) if len(x) < 8192 else None
    adapter = EmbedderAdapter(raw_embedder)
    
    result = adapter(long_text)
    assert len(result) == 2
    # Should either truncate or return None with metadata
```

#### Test 6.3: Concurrent Calls
```python
def test_adapter_thread_safety():
    """Test adapter handles concurrent calls safely."""
    import threading
    
    raw_embedder = lambda x: np.random.rand(768)
    adapter = EmbedderAdapter(raw_embedder)
    
    results = []
    def worker():
        for _ in range(10):
            result = adapter("test")
            results.append(result)
    
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All results should be valid 2-tuples
    assert len(results) == 100
    assert all(len(r) == 2 for r in results)
```

## Test Execution Plan

### Phase 1: Unit Tests (Priority: High)
- Run tests 1.1-1.3 first to validate core adapter logic
- Must pass before proceeding to integration

### Phase 2: Provider Tests (Priority: High)
- Test with each supported provider (2.1-2.3)
- Mock external APIs to avoid dependencies
- Verify all provider-specific quirks handled

### Phase 3: Error Handling (Priority: Critical)
- Tests 3.1-3.3 ensure resilience
- Must handle all failure modes gracefully
- No tuple-unpack errors even on failure

### Phase 4: Integration (Priority: High)
- Tests 4.1-4.2 verify FAISSRetriever compatibility
- Ensure end-to-end flow works

### Phase 5: Performance (Priority: Medium)
- Tests 5.1-5.2 ensure acceptable performance
- Run after functional tests pass

### Phase 6: Edge Cases (Priority: Medium)
- Tests 6.1-6.3 cover unusual scenarios
- Run last to catch remaining issues

## Success Metrics
- 100% of tests passing
- Zero tuple-unpack errors in 1000+ test runs
- Performance overhead < 10%
- All providers supported
- Graceful failure handling

## Test Data Requirements
- Sample embeddings for each provider format
- FAISS index with test documents
- Various text samples (short, long, unicode, etc.)
- Mock API responses for each provider

## Dependencies
- pytest
- numpy
- faiss-cpu
- unittest.mock
- time, threading, tracemalloc (stdlib)