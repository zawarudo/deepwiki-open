# Test Plan: Standardize RAG.call() Return Format

## Objective
Ensure RAG.call() and RAG.__call__() consistently return a 2-tuple `(answer, documents)` preventing tuple-unpack errors in all consumers.

## Test Categories

### 1. Unit Tests - RAG Class Core Behavior

#### Test 1.1: __call__ Method Exists and Delegates
```python
def test_rag_has_callable_interface():
    """Verify RAG can be called as request_rag(query)."""
    rag = RAG(config={"provider": "openai", "api_key": "test"})
    
    # Should be callable
    assert callable(rag)
    assert hasattr(rag, '__call__')
    
    # __call__ should delegate to call()
    with patch.object(rag, 'call', return_value=("answer", [])) as mock_call:
        result = rag("test query")
        mock_call.assert_called_once_with("test query")
        assert result == ("answer", [])
```

#### Test 1.2: call() Always Returns 2-Tuple
```python
def test_rag_call_returns_tuple():
    """Verify call() always returns (answer, docs) tuple."""
    rag = RAG(config={"provider": "openai"})
    
    # Mock retriever to return documents
    mock_retriever = Mock()
    mock_retriever.retrieve.return_value = ["doc1", "doc2"]
    rag.retriever = mock_retriever
    
    # Mock LLM response
    with patch.object(rag, '_generate_answer', return_value="Generated answer"):
        result = rag.call("test query")
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        answer, docs = result
        assert answer == "Generated answer"
        assert docs == ["doc1", "doc2"]
```

#### Test 1.3: Empty Retrieval Returns Correct Tuple
```python
def test_rag_call_with_no_documents():
    """Verify call() returns (None, []) when no documents retrieved."""
    rag = RAG(config={"provider": "openai"})
    
    # Mock empty retrieval
    mock_retriever = Mock()
    mock_retriever.retrieve.return_value = []
    rag.retriever = mock_retriever
    
    result = rag.call("test query")
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    answer, docs = result
    assert answer is None or answer == ""
    assert docs == []
```

#### Test 1.4: Missing Retriever Handling
```python
def test_rag_call_without_retriever():
    """Verify call() handles missing retriever gracefully."""
    rag = RAG(config={"provider": "openai"})
    rag.retriever = None
    
    result = rag.call("test query")
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    answer, docs = result
    # Should still generate answer without context
    assert answer is not None or docs == []
```

### 2. Integration Tests - Consumer Compatibility

#### Test 2.1: WebSocket Handler Integration
```python
def test_websocket_handler_unpacks_correctly():
    """Verify websocket_wiki.py can unpack RAG results."""
    from api.websocket_wiki import handle_chat_message
    
    # Mock RAG instance
    mock_rag = Mock()
    mock_rag.return_value = ("AI response", ["context1", "context2"])
    
    # Simulate WebSocket message handling
    with patch('api.websocket_wiki.request_rag', mock_rag):
        response = handle_chat_message({"query": "test"})
        
        # Should not raise unpacking error
        assert "answer" in response
        assert "sources" in response
```

#### Test 2.2: Simple Chat API Integration
```python
def test_simple_chat_unpacks_correctly():
    """Verify simple_chat.py can unpack RAG results."""
    from api.simple_chat import chat_completions_stream
    
    mock_rag = Mock()
    mock_rag.return_value = ("Response text", [{"content": "doc"}])
    
    with patch('api.simple_chat.request_rag', mock_rag):
        # Should handle unpacking without error
        result = chat_completions_stream({"messages": [{"content": "test"}]})
        assert result is not None
```

#### Test 2.3: Multiple Consumers Stress Test
```python
def test_multiple_consumers_concurrent():
    """Test RAG with multiple concurrent consumers."""
    import threading
    
    rag = RAG(config={"provider": "openai"})
    results = []
    errors = []
    
    def consumer(query):
        try:
            answer, docs = rag(query)  # Should unpack correctly
            results.append((answer, docs))
        except Exception as e:
            errors.append(e)
    
    threads = [
        threading.Thread(target=consumer, args=(f"query{i}",))
        for i in range(50)
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"Unpacking errors: {errors}"
    assert len(results) == 50
    assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
```

### 3. Provider-Specific Tests

#### Test 3.1: OpenAI Provider
```python
def test_rag_openai_provider_returns_tuple():
    """Test RAG with OpenAI provider configuration."""
    rag = RAG(config={
        "provider": "openai",
        "api_key": "test",
        "model": "gpt-4"
    })
    
    mock_response = {"choices": [{"message": {"content": "OpenAI response"}}]}
    
    with patch('openai.ChatCompletion.create', return_value=mock_response):
        result = rag.call("test")
        assert isinstance(result, tuple)
        assert len(result) == 2
```

#### Test 3.2: Google Gemini Provider
```python
def test_rag_gemini_provider_returns_tuple():
    """Test RAG with Gemini provider configuration."""
    rag = RAG(config={
        "provider": "google",
        "api_key": "test",
        "model": "gemini-pro"
    })
    
    with patch.object(rag, '_call_gemini', return_value="Gemini response"):
        result = rag.call("test")
        assert isinstance(result, tuple)
        assert len(result) == 2
```

#### Test 3.3: Ollama Local Provider
```python
def test_rag_ollama_provider_returns_tuple():
    """Test RAG with Ollama local model."""
    rag = RAG(config={
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434"
    })
    
    mock_response = {"response": "Ollama response"}
    
    with patch('requests.post', return_value=Mock(json=lambda: mock_response)):
        result = rag.call("test")
        assert isinstance(result, tuple)
        assert len(result) == 2
```

#### Test 3.4: OpenRouter Provider
```python
def test_rag_openrouter_provider_returns_tuple():
    """Test RAG with OpenRouter provider."""
    rag = RAG(config={
        "provider": "openrouter",
        "api_key": "test",
        "model": "claude-3-opus"
    })
    
    with patch.object(rag, '_call_openrouter', return_value="OpenRouter response"):
        result = rag.call("test")
        assert isinstance(result, tuple)
        assert len(result) == 2
```

### 4. Error Handling Tests

#### Test 4.1: LLM API Failure
```python
def test_rag_handles_llm_failure():
    """Verify RAG returns tuple even on LLM failure."""
    rag = RAG(config={"provider": "openai"})
    
    with patch.object(rag, '_generate_answer', side_effect=Exception("API Error")):
        result = rag.call("test")
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        answer, docs = result
        assert answer is None or "error" in answer.lower()
```

#### Test 4.2: Retriever Failure
```python
def test_rag_handles_retriever_failure():
    """Verify RAG returns tuple even on retriever failure."""
    rag = RAG(config={"provider": "openai"})
    
    mock_retriever = Mock()
    mock_retriever.retrieve.side_effect = Exception("Index corrupted")
    rag.retriever = mock_retriever
    
    result = rag.call("test")
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    answer, docs = result
    assert docs == [] or docs is None
```

#### Test 4.3: Timeout Handling
```python
def test_rag_handles_timeout():
    """Verify RAG handles timeouts gracefully."""
    rag = RAG(config={"provider": "openai", "timeout": 0.001})
    
    def slow_generate(*args):
        time.sleep(1)
        return "Too slow"
    
    with patch.object(rag, '_generate_answer', side_effect=slow_generate):
        result = rag.call("test")
        
        assert isinstance(result, tuple)
        assert len(result) == 2
```

### 5. Memory Management Tests

#### Test 5.1: Dialog Turn Addition
```python
def test_rag_dialog_memory_with_tuple_return():
    """Test add_dialog_turn works with new tuple format."""
    rag = RAG(config={"provider": "openai"})
    
    # Add turns and verify format
    rag.add_dialog_turn("user", "Hello")
    rag.add_dialog_turn("assistant", "Hi there")
    
    # Call should still return tuple
    result = rag.call("Follow up question")
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    # Memory should be preserved
    assert len(rag.dialog) >= 2
```

#### Test 5.2: Token Limit Handling
```python
def test_rag_truncates_context_returns_tuple():
    """Test context truncation preserves tuple return."""
    rag = RAG(config={"provider": "openai", "max_tokens": 100})
    
    # Add very long context
    long_docs = ["x" * 1000 for _ in range(10)]
    mock_retriever = Mock()
    mock_retriever.retrieve.return_value = long_docs
    rag.retriever = mock_retriever
    
    result = rag.call("test")
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    # Context should be truncated but still valid
```

### 6. Backward Compatibility Tests

#### Test 6.1: Legacy Code Pattern
```python
def test_backward_compatibility_single_assignment():
    """Test code that expects single value still works."""
    rag = RAG(config={"provider": "openai"})
    
    # Legacy pattern: result = rag.call(query)
    # Should not break, even if only first element used
    result = rag.call("test")
    
    # Can still access as tuple
    if isinstance(result, tuple):
        answer = result[0]
    else:
        answer = result  # Legacy support if needed
    
    assert answer is not None or answer == ""
```

#### Test 6.2: Migration Path Validation
```python
def test_migration_with_feature_flag():
    """Test gradual migration with feature flag."""
    # With flag disabled - old behavior
    rag = RAG(config={"provider": "openai", "return_tuple": False})
    with patch.object(rag, '_legacy_call', return_value="just answer"):
        result = rag.call("test")
        assert not isinstance(result, tuple) or len(result) == 1
    
    # With flag enabled - new behavior
    rag = RAG(config={"provider": "openai", "return_tuple": True})
    result = rag.call("test")
    assert isinstance(result, tuple)
    assert len(result) == 2
```

### 7. Type Validation Tests

#### Test 7.1: Type Hints Validation
```python
def test_rag_type_hints_correct():
    """Verify type hints match actual return types."""
    from typing import get_type_hints
    
    # Check __call__ signature
    hints = get_type_hints(RAG.__call__)
    # Should indicate Tuple[Optional[str], List] return
    
    # Check call() signature
    hints = get_type_hints(RAG.call)
    # Should indicate Tuple[Optional[str], List] return
```

#### Test 7.2: Return Type Consistency
```python
def test_return_type_consistency():
    """Verify return types are consistent across all paths."""
    rag = RAG(config={"provider": "openai"})
    
    test_cases = [
        ("normal query", ["doc1", "doc2"]),
        ("empty retrieval", []),
        ("no retriever", None),
        ("error case", Exception("test")),
    ]
    
    for query, retriever_result in test_cases:
        if isinstance(retriever_result, Exception):
            mock_retriever = Mock(side_effect=retriever_result)
        elif retriever_result is None:
            mock_retriever = None
        else:
            mock_retriever = Mock(return_value=retriever_result)
        
        if mock_retriever:
            rag.retriever = mock_retriever
        
        result = rag.call(query)
        
        assert isinstance(result, tuple), f"Failed for {query}"
        assert len(result) == 2, f"Wrong length for {query}"
        assert isinstance(result[0], (str, type(None))), f"Wrong answer type for {query}"
        assert isinstance(result[1], list), f"Wrong docs type for {query}"
```

### 8. Performance Tests

#### Test 8.1: Tuple Creation Overhead
```python
def test_tuple_creation_performance():
    """Measure overhead of tuple creation."""
    rag = RAG(config={"provider": "openai"})
    
    # Measure time for 1000 calls
    start = time.time()
    for _ in range(1000):
        result = rag.call("test")
        assert isinstance(result, tuple)
    duration = time.time() - start
    
    # Should complete in reasonable time (< 1 second for mocked calls)
    assert duration < 1.0, f"Too slow: {duration}s"
```

#### Test 8.2: Memory Usage
```python
def test_tuple_memory_usage():
    """Verify tuple return doesn't leak memory."""
    import gc
    import tracemalloc
    
    tracemalloc.start()
    rag = RAG(config={"provider": "openai"})
    
    # Make many calls
    for _ in range(1000):
        result = rag.call("test")
        del result  # Explicit cleanup
    
    gc.collect()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Memory should be reasonable (< 50MB)
    assert peak < 50 * 1024 * 1024
```

## Test Execution Plan

### Phase 1: Core Functionality (Priority: Critical)
- Tests 1.1-1.4: Verify basic tuple return behavior
- Must pass before any deployment

### Phase 2: Consumer Integration (Priority: Critical)
- Tests 2.1-2.3: Verify all consumers can unpack
- Block deployment if any consumer fails

### Phase 3: Provider Coverage (Priority: High)
- Tests 3.1-3.4: Test each provider configuration
- Ensure all providers work with new format

### Phase 4: Error Resilience (Priority: High)
- Tests 4.1-4.3: Verify error handling
- No unpacking errors even on failure

### Phase 5: Compatibility (Priority: Medium)
- Tests 6.1-6.2: Ensure backward compatibility
- Support gradual migration

### Phase 6: Performance (Priority: Low)
- Tests 8.1-8.2: Verify acceptable performance
- Run after functional tests pass

## Success Metrics
- 100% of tests passing
- Zero tuple-unpack errors in all consumers
- All providers return consistent format
- Performance overhead < 1%
- Backward compatibility maintained

## Test Data Requirements
- Mock LLM responses for each provider
- Sample documents for retrieval
- Error scenarios for each provider
- Memory/performance baseline data

## Dependencies
- pytest
- unittest.mock
- threading
- time, gc, tracemalloc (stdlib)
- Provider SDKs (for integration tests)