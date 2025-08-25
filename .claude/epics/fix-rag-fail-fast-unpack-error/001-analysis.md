# Technical Analysis: Query-Embedder Adapter Implementation

## Current State Analysis

### Problem Context
The FAISSRetriever expects embedders to return a 2-tuple `(embedding_vector, metadata)`, but current embedders return different formats:
- **OpenAI**: Returns embedding array directly
- **Gemini**: Returns numpy array
- **Ollama**: Returns list/array
- **OpenRouter**: Variable based on model
- **Azure OpenAI**: Similar to OpenAI

This inconsistency causes tuple-unpacking errors when FAISSRetriever tries to decompose the result.

### Code Locations
```python
# Current embedder usage in api/rag.py:422-449
single_string_embedder = prepare_single_string_embedder(
    config['rag'], logger
)
self.embedder = single_string_embedder

# FAISSRetriever initialization in retrievers/
retriever = FAISSRetriever(
    index=index,
    embedder=self.embedder,  # Expects 2-tuple return
    k=k
)
```

## Solution Architecture

### 1. Adapter Pattern Implementation

```python
class EmbedderAdapter:
    """
    Adapter ensuring embedders return consistent 2-tuple format.
    Wraps any embedder function to guarantee (embedding, metadata) return.
    """
    
    def __init__(self, embedder_func, timeout=30, provider_name=None):
        self.embedder_func = embedder_func
        self.timeout = timeout
        self.provider_name = provider_name or "unknown"
        self.call_count = 0
        self.error_count = 0
    
    def __call__(self, text: str) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """
        Process text through embedder and ensure 2-tuple return.
        
        Returns:
            Tuple of (embedding_array, metadata_dict)
            On error: (None, {"error": str, "provider": str})
        """
        self.call_count += 1
        metadata = {"provider": self.provider_name, "call_id": self.call_count}
        
        try:
            # Handle None/empty input
            if not text:
                return (None, {**metadata, "warning": "empty_input"})
            
            # Call underlying embedder with timeout
            result = self._call_with_timeout(text)
            
            # Normalize result to 2-tuple
            return self._normalize_result(result, metadata)
            
        except Exception as e:
            self.error_count += 1
            error_metadata = {
                **metadata,
                "error": str(e),
                "error_type": type(e).__name__,
                "error_count": self.error_count
            }
            return (None, error_metadata)
    
    def _normalize_result(self, result, metadata):
        """Convert various result formats to consistent 2-tuple."""
        
        # Already a 2-tuple - validate and return
        if isinstance(result, tuple) and len(result) == 2:
            embedding, existing_meta = result
            combined_meta = {**metadata, **(existing_meta or {})}
            return (self._ensure_array(embedding), combined_meta)
        
        # Single value - wrap in tuple
        if isinstance(result, (list, np.ndarray)):
            return (self._ensure_array(result), metadata)
        
        # Dict response (some providers)
        if isinstance(result, dict):
            if "embedding" in result:
                embedding = result["embedding"]
                meta = {**metadata, **{k: v for k, v in result.items() if k != "embedding"}}
                return (self._ensure_array(embedding), meta)
            elif "data" in result:  # OpenAI format
                embedding = result["data"][0]["embedding"]
                meta = {**metadata, "usage": result.get("usage")}
                return (self._ensure_array(embedding), meta)
        
        # Unexpected format - log and return None
        metadata["warning"] = f"unexpected_format: {type(result)}"
        return (None, metadata)
    
    def _ensure_array(self, embedding):
        """Convert embedding to numpy array if needed."""
        if embedding is None:
            return None
        if isinstance(embedding, np.ndarray):
            return embedding
        return np.array(embedding, dtype=np.float32)
```

### 2. Integration Points

#### 2.1 Modify prepare_single_string_embedder()
```python
# In api/rag.py or embeddings module
def prepare_single_string_embedder(config, logger):
    """Prepare embedder with adapter wrapper."""
    
    # Get raw embedder based on provider
    raw_embedder = _create_raw_embedder(config, logger)
    
    # Determine provider name for metadata
    provider_name = config.get('provider', 'unknown')
    
    # Wrap with adapter
    adapted_embedder = EmbedderAdapter(
        embedder_func=raw_embedder,
        timeout=config.get('timeout', 30),
        provider_name=provider_name
    )
    
    logger.info(f"Created adapted embedder for provider: {provider_name}")
    
    return adapted_embedder
```

#### 2.2 Update FAISSRetriever Usage
```python
# No changes needed in FAISSRetriever!
# It already expects (embedding, metadata) tuple
# Adapter ensures this contract is met
```

### 3. Provider-Specific Handling

#### OpenAI/Azure OpenAI
```python
def _handle_openai_response(response):
    """Extract embedding from OpenAI API response."""
    if isinstance(response, dict):
        if "data" in response:
            return response["data"][0]["embedding"]
    return response
```

#### Google Gemini
```python
def _handle_gemini_response(response):
    """Gemini returns embeddings directly as arrays."""
    return np.array(response) if response is not None else None
```

#### Ollama
```python
def _handle_ollama_response(response):
    """Extract embedding from Ollama response."""
    if isinstance(response, dict):
        return response.get("embedding")
    return response
```

### 4. Error Handling Strategy

#### Graceful Degradation
1. **Network Errors**: Return `(None, {"error": "network_timeout"})`
2. **API Errors**: Return `(None, {"error": "api_error", "code": 429})`
3. **Malformed Response**: Return `(None, {"error": "invalid_response"})`
4. **Token Limit**: Truncate input and retry, note in metadata

#### Retry Logic
```python
def _call_with_retry(self, text, max_retries=3):
    """Call embedder with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return self.embedder_func(text)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            time.sleep(wait_time)
```

### 5. Logging and Metrics

#### Structured Logging
```python
def _log_call(self, text, result, duration):
    """Log embedder call with structured data."""
    log_data = {
        "event": "embedder_call",
        "provider": self.provider_name,
        "input_length": len(text) if text else 0,
        "output_shape": self._get_shape(result),
        "duration_ms": duration * 1000,
        "success": result[0] is not None if result else False
    }
    logger.info("Embedder call completed", extra=log_data)
```

#### Metrics Collection
```python
# Prometheus-style metrics
embedder_calls_total = Counter('embedder_calls_total', 'Total embedder calls', ['provider', 'status'])
embedder_duration_seconds = Histogram('embedder_duration_seconds', 'Embedder call duration', ['provider'])
embedder_errors_total = Counter('embedder_errors_total', 'Total embedder errors', ['provider', 'error_type'])
```

## Implementation Plan

### Phase 1: Core Adapter (2 hours)
1. Create `EmbedderAdapter` class in `api/embeddings/adapter.py`
2. Implement basic wrapping and 2-tuple guarantee
3. Add type hints and docstrings

### Phase 2: Provider Integration (1 hour)
1. Update `prepare_single_string_embedder()` to use adapter
2. Test with each provider configuration
3. Verify FAISSRetriever compatibility

### Phase 3: Error Handling (30 minutes)
1. Add timeout support
2. Implement retry logic
3. Add graceful degradation

### Phase 4: Observability (30 minutes)
1. Add structured logging
2. Implement metrics collection
3. Add debug mode for troubleshooting

## Testing Strategy

### Unit Tests
- Test adapter with mock embedders
- Verify all response formats handled
- Test error scenarios

### Integration Tests
- Test with real provider responses (mocked)
- Verify FAISSRetriever integration
- Test end-to-end retrieval flow

### Performance Tests
- Measure adapter overhead (target < 1ms)
- Test concurrent calls
- Memory usage validation

## Risk Analysis

### Low Risk
- Adapter pattern is well-understood
- Changes are isolated to embedder preparation
- Backward compatible with existing code

### Medium Risk
- Provider API changes could break assumptions
- Need to handle all provider response formats

### Mitigations
- Comprehensive test coverage
- Defensive programming with fallbacks
- Detailed logging for debugging

## Success Criteria
1. **Zero tuple-unpack errors** in production for 7+ days
2. **All providers supported** without modification
3. **Performance overhead < 10%** vs raw embedders
4. **100% test coverage** of adapter code
5. **Structured logs** showing consistent shapes

## Dependencies
- No new external dependencies required
- Uses existing numpy, logging
- Compatible with all current providers

## Migration Path
1. Deploy adapter in shadow mode (log only)
2. Monitor for issues for 24 hours
3. Enable adapter for 10% of traffic
4. Gradual rollout to 100% over 3 days
5. Remove old embedder code after 1 week

## Alternative Approaches Considered

### 1. Modify Each Embedder
- **Pros**: Direct control, no wrapper overhead
- **Cons**: Code duplication, harder to maintain
- **Decision**: Rejected - violates DRY principle

### 2. Modify FAISSRetriever
- **Pros**: Single point of change
- **Cons**: Retriever shouldn't know about embedder formats
- **Decision**: Rejected - violates separation of concerns

### 3. Middleware Layer
- **Pros**: Clean separation, reusable
- **Cons**: More complex than needed
- **Decision**: Adapter pattern is simpler middleware

## Conclusion
The EmbedderAdapter provides a clean, maintainable solution that:
- Ensures consistent 2-tuple returns
- Handles all provider variations
- Adds minimal overhead
- Provides comprehensive error handling
- Enables detailed observability

This approach fixes the immediate tuple-unpack error while providing a foundation for future embedder enhancements.