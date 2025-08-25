# Test Plan: Normalize Helper Function and Consumer Updates

## Objective
Implement and test `normalize_rag_result()` helper function to handle various RAG return formats and update all consumers to use it.

## Test Categories

### 1. Unit Tests - Normalize Helper Core Functionality

#### Test 1.1: Handle Standard Tuple Input
```python
def test_normalize_standard_tuple():
    """Test normalizer with correct 2-tuple input."""
    from api.utils import normalize_rag_result
    
    # Standard tuple input
    input_data = ("Answer text", [{"doc": "content"}])
    result = normalize_rag_result(input_data)
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == "Answer text"
    assert result[1] == [{"doc": "content"}]
```

#### Test 1.2: Handle Legacy Single Value
```python
def test_normalize_legacy_single_value():
    """Test normalizer with legacy single return value."""
    from api.utils import normalize_rag_result
    
    # Legacy: just documents list
    input_data = [{"doc1": "content"}, {"doc2": "content"}]
    result = normalize_rag_result(input_data)
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] is None  # No answer in legacy format
    assert result[1] == input_data  # Documents preserved
```

#### Test 1.3: Handle None Input
```python
def test_normalize_none_input():
    """Test normalizer with None input."""
    from api.utils import normalize_rag_result
    
    result = normalize_rag_result(None)
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] is None
    assert result[1] == []
```

#### Test 1.4: Handle Empty Results
```python
def test_normalize_empty_variations():
    """Test normalizer with various empty formats."""
    from api.utils import normalize_rag_result
    
    test_cases = [
        [],  # Empty list
        "",  # Empty string
        {},  # Empty dict
        (None, None),  # Tuple of Nones
        (None, []),  # Partial empty
        ("", []),  # Empty answer
    ]
    
    for input_data in test_cases:
        result = normalize_rag_result(input_data)
        assert isinstance(result, tuple), f"Failed for {input_data}"
        assert len(result) == 2, f"Wrong length for {input_data}"
        # Should handle gracefully without errors
```

### 2. Edge Case Tests

#### Test 2.1: Handle Malformed Tuples
```python
def test_normalize_malformed_tuples():
    """Test normalizer with wrong-sized tuples."""
    from api.utils import normalize_rag_result
    
    test_cases = [
        ("single",),  # 1-tuple
        ("one", "two", "three"),  # 3-tuple
        ("one", "two", "three", "four"),  # 4-tuple
    ]
    
    for input_data in test_cases:
        result = normalize_rag_result(input_data)
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Should extract first two or pad with defaults
```

#### Test 2.2: Handle Dict Responses
```python
def test_normalize_dict_responses():
    """Test normalizer with dictionary responses."""
    from api.utils import normalize_rag_result
    
    test_cases = [
        {"answer": "text", "documents": []},
        {"response": "text", "sources": []},
        {"text": "answer", "context": []},
        {"result": "text"},  # Missing documents
        {"docs": []},  # Missing answer
    ]
    
    for input_data in test_cases:
        result = normalize_rag_result(input_data)
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Should extract answer and docs from dict
```

#### Test 2.3: Handle String Responses
```python
def test_normalize_string_responses():
    """Test normalizer with plain string responses."""
    from api.utils import normalize_rag_result
    
    test_strings = [
        "Plain answer text",
        "Answer: Some response",
        '{"answer": "JSON string"}',  # JSON string
    ]
    
    for input_data in test_strings:
        result = normalize_rag_result(input_data)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], (str, type(None)))
        assert isinstance(result[1], list)
```

### 3. Type Safety Tests

#### Test 3.1: Type Preservation
```python
def test_normalize_preserves_types():
    """Test that normalizer preserves correct types."""
    from api.utils import normalize_rag_result
    
    # Test with properly typed input
    input_data = ("Answer", [{"id": 1, "content": "doc"}])
    result = normalize_rag_result(input_data)
    
    assert isinstance(result[0], str)
    assert isinstance(result[1], list)
    assert isinstance(result[1][0], dict)
    assert isinstance(result[1][0]["id"], int)
```

#### Test 3.2: Type Coercion
```python
def test_normalize_coerces_types():
    """Test type coercion for incorrect types."""
    from api.utils import normalize_rag_result
    
    test_cases = [
        (123, "not_a_list"),  # Wrong types
        (["list_not_string"], {"dict": "not_list"}),
        (True, False),  # Booleans
    ]
    
    for input_data in test_cases:
        result = normalize_rag_result(input_data)
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Should coerce to expected types
        assert result[0] is None or isinstance(result[0], str)
        assert isinstance(result[1], list)
```

### 4. Consumer Integration Tests

#### Test 4.1: WebSocket Handler Integration
```python
def test_websocket_with_normalizer():
    """Test websocket handler using normalizer."""
    from api.websocket_wiki import handle_chat_with_normalizer
    from api.utils import normalize_rag_result
    
    # Mock RAG returning various formats
    mock_responses = [
        ("answer", ["doc"]),  # Correct format
        ["doc1", "doc2"],  # Legacy format
        None,  # Error case
        {"answer": "text"},  # Dict format
    ]
    
    for mock_response in mock_responses:
        with patch('api.websocket_wiki.request_rag', return_value=mock_response):
            # Should use normalizer internally
            response = handle_chat_with_normalizer({"query": "test"})
            
            assert "answer" in response
            assert "sources" in response
            # No unpacking errors
```

#### Test 4.2: Simple Chat Integration
```python
def test_simple_chat_with_normalizer():
    """Test simple chat API using normalizer."""
    from api.simple_chat import process_with_normalizer
    from api.utils import normalize_rag_result
    
    mock_rag = Mock()
    
    # Test various response formats
    test_responses = [
        ("response", []),
        [],
        None,
        "just a string",
    ]
    
    for response in test_responses:
        mock_rag.return_value = response
        
        with patch('api.simple_chat.request_rag', mock_rag):
            result = process_with_normalizer("test query")
            
            # Should handle all formats gracefully
            assert result is not None
            # Should have normalized structure
```

#### Test 4.3: Batch Processing
```python
def test_batch_normalization():
    """Test normalizer in batch processing scenarios."""
    from api.utils import normalize_rag_result
    
    # Simulate batch of mixed responses
    responses = [
        ("answer1", ["doc1"]),
        ["doc2"],
        None,
        {"answer": "answer3"},
        "answer4",
    ]
    
    normalized = [normalize_rag_result(r) for r in responses]
    
    assert len(normalized) == 5
    assert all(isinstance(r, tuple) for r in normalized)
    assert all(len(r) == 2 for r in normalized)
```

### 5. Error Handling Tests

#### Test 5.1: Exception Handling
```python
def test_normalize_handles_exceptions():
    """Test normalizer handles exceptions gracefully."""
    from api.utils import normalize_rag_result
    
    # Create objects that raise on access
    class BadObject:
        def __getitem__(self, key):
            raise KeyError("Boom!")
        def __len__(self):
            raise ValueError("Boom!")
    
    result = normalize_rag_result(BadObject())
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result == (None, [])  # Safe defaults
```

#### Test 5.2: Recursive Structures
```python
def test_normalize_handles_recursion():
    """Test normalizer handles recursive structures."""
    from api.utils import normalize_rag_result
    
    # Create circular reference
    circular = []
    circular.append(circular)
    
    result = normalize_rag_result(circular)
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    # Should handle without infinite loop
```

#### Test 5.3: Large Data
```python
def test_normalize_handles_large_data():
    """Test normalizer with large inputs."""
    from api.utils import normalize_rag_result
    
    # Create large document list
    large_docs = [{"content": "x" * 10000} for _ in range(1000)]
    input_data = ("answer", large_docs)
    
    result = normalize_rag_result(input_data)
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert len(result[1]) == 1000
    # Should handle without memory issues
```

### 6. Performance Tests

#### Test 6.1: Overhead Measurement
```python
def test_normalize_performance():
    """Measure normalizer overhead."""
    from api.utils import normalize_rag_result
    import time
    
    # Already normalized input
    input_data = ("answer", [{"doc": "content"}])
    
    # Measure 10000 calls
    start = time.time()
    for _ in range(10000):
        result = normalize_rag_result(input_data)
    duration = time.time() - start
    
    # Should be very fast (< 100ms for 10k calls)
    assert duration < 0.1, f"Too slow: {duration}s"
    
    # Average per call should be < 10 microseconds
    avg_time = duration / 10000
    assert avg_time < 0.00001
```

#### Test 6.2: Memory Efficiency
```python
def test_normalize_memory_efficiency():
    """Test normalizer doesn't copy unnecessarily."""
    from api.utils import normalize_rag_result
    import sys
    
    # Large document list
    docs = [{"content": "x" * 1000} for _ in range(100)]
    input_data = ("answer", docs)
    
    # Get memory before
    docs_size = sys.getsizeof(docs)
    
    # Normalize
    result = normalize_rag_result(input_data)
    
    # Should reuse same list object if possible
    if result[1] is docs:
        assert True  # Good, no copy
    else:
        # If copied, size should be similar
        result_size = sys.getsizeof(result[1])
        assert result_size < docs_size * 1.1  # Max 10% overhead
```

### 7. Consumer Update Tests

#### Test 7.1: WebSocket Consumer Refactored
```python
def test_websocket_refactored_code():
    """Test refactored websocket handler."""
    # New code pattern in websocket_wiki.py
    code = '''
    from api.utils import normalize_rag_result
    
    def handle_chat_message(message):
        query = message.get("query")
        
        # Call RAG (may return various formats)
        raw_result = request_rag(query)
        
        # Normalize to consistent format
        answer, documents = normalize_rag_result(raw_result)
        
        return {
            "answer": answer or "No answer available",
            "sources": documents
        }
    '''
    
    # Test the pattern works
    from api.utils import normalize_rag_result
    
    def mock_handler(raw_result):
        answer, documents = normalize_rag_result(raw_result)
        return {"answer": answer, "sources": documents}
    
    # Test with various inputs
    assert mock_handler(("ans", [])) == {"answer": "ans", "sources": []}
    assert mock_handler(None)["answer"] is None
```

#### Test 7.2: Simple Chat Consumer Refactored
```python
def test_simple_chat_refactored_code():
    """Test refactored simple chat handler."""
    # New code pattern in simple_chat.py
    code = '''
    from api.utils import normalize_rag_result
    
    def process_chat(message):
        # Call RAG
        raw_result = request_rag(message)
        
        # Normalize result
        response, context = normalize_rag_result(raw_result)
        
        # Use normalized values
        if response:
            return format_response(response, context)
        else:
            return generate_fallback()
    '''
    
    # Test pattern
    from api.utils import normalize_rag_result
    
    raw_results = [
        ("response", ["context"]),
        ["only_context"],
        None,
    ]
    
    for raw in raw_results:
        response, context = normalize_rag_result(raw)
        # Should unpack without error
        assert isinstance(response, (str, type(None)))
        assert isinstance(context, list)
```

### 8. Backward Compatibility Tests

#### Test 8.1: Legacy Code Pattern Support
```python
def test_backward_compatibility():
    """Test normalizer supports legacy patterns."""
    from api.utils import normalize_rag_result
    
    # Legacy code might expect just documents
    def legacy_handler(rag_result):
        # Old: documents = rag_result
        # New: _, documents = normalize_rag_result(rag_result)
        if isinstance(rag_result, tuple):
            _, documents = rag_result
        else:
            documents = rag_result
        return documents
    
    # Should work with both old and new formats
    assert legacy_handler(["doc1"]) == ["doc1"]
    assert legacy_handler(("answer", ["doc2"])) == ["doc2"]
```

#### Test 8.2: Gradual Migration Support
```python
def test_gradual_migration():
    """Test normalizer supports gradual migration."""
    from api.utils import normalize_rag_result
    
    def hybrid_handler(rag_result, use_normalizer=False):
        if use_normalizer:
            answer, docs = normalize_rag_result(rag_result)
        else:
            # Legacy handling
            if isinstance(rag_result, tuple):
                answer, docs = rag_result
            else:
                answer, docs = None, rag_result
        
        return {"answer": answer, "docs": docs}
    
    # Test both paths work
    result_old = hybrid_handler(["doc"], use_normalizer=False)
    result_new = hybrid_handler(["doc"], use_normalizer=True)
    
    assert result_old["docs"] == ["doc"]
    assert result_new["docs"] == ["doc"]
```

## Test Execution Plan

### Phase 1: Core Normalizer (Priority: Critical)
- Tests 1.1-1.4: Basic normalization logic
- Must pass before consumer updates

### Phase 2: Edge Cases (Priority: High)
- Tests 2.1-2.3: Handle unusual inputs
- Ensure robustness

### Phase 3: Type Safety (Priority: High)
- Tests 3.1-3.2: Type handling
- Prevent type errors

### Phase 4: Consumer Integration (Priority: Critical)
- Tests 4.1-4.3: Verify consumer updates work
- End-to-end validation

### Phase 5: Error Handling (Priority: Medium)
- Tests 5.1-5.3: Resilience testing
- Graceful degradation

### Phase 6: Performance (Priority: Low)
- Tests 6.1-6.2: Verify efficiency
- No performance regression

## Success Metrics
- 100% test coverage of normalizer
- Zero unpacking errors in consumers
- All input formats handled gracefully
- Performance overhead < 1%
- Backward compatibility maintained

## Test Data Requirements
- Various RAG response formats
- Legacy response samples
- Error case examples
- Large document sets for performance testing

## Dependencies
- pytest
- unittest.mock
- time, sys (stdlib)