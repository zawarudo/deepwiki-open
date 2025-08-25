# Task 005: Structured Logging and Metrics Analysis

## Executive Summary
Implement comprehensive observability for RAG return shapes and provider-specific behaviors to enable proactive issue detection and performance monitoring. This analysis defines logging infrastructure requirements, metrics collection points, and dashboard specifications for tracking the health of RAG operations.

## Current State Analysis

### Existing Logging Infrastructure
- **Python Logging**: Standard `logging` module used throughout API
- **Log Levels**: INFO for operations, ERROR for failures, DEBUG for detailed traces
- **Format**: Text-based logs with timestamp, level, module, and message
- **Missing**: Structured fields, metrics collection, provider-specific tracking

### Identified Logging Gaps
1. **Return Shape Tracking**: No visibility into actual vs expected return types
2. **Provider Metrics**: No breakdown of success/failure rates by provider
3. **Latency Tracking**: No measurement of embedding/retrieval times
4. **Error Categorization**: Generic exceptions without classification

## Technical Implementation Strategy

### 1. Structured Logging Enhancement

#### Log Schema Definition
```python
{
    "timestamp": "ISO-8601",
    "level": "INFO|WARNING|ERROR",
    "component": "embedder|retriever|rag",
    "operation": "embed|retrieve|generate",
    "provider": "openai|google|azure|ollama|openrouter",
    "model": "model-name",
    "return_shape": {
        "type": "tuple|list|dict|none",
        "length": int,
        "structure": "description"
    },
    "latency_ms": float,
    "status": "success|empty|error",
    "error_type": "optional-error-classification",
    "trace_id": "uuid-for-request-correlation"
}
```

#### Implementation Points
1. **api/rag.py:422-454** - RAG.call() method
   - Log before retrieval attempt
   - Log retrieval result shape
   - Log after answer generation
   - Log final return shape

2. **api/rag.py:embedder initialization** - Embedder wrapping
   - Log embedder type and configuration
   - Log embedding request/response shapes
   - Track embedding latencies

3. **api/websocket_wiki.py:197** - Consumer endpoint
   - Log incoming query
   - Log RAG response shape
   - Log unpacking success/failure

### 2. Metrics Collection Strategy

#### Key Metrics to Track
1. **Counters**
   - `rag.calls.total{provider, model, status}`
   - `rag.errors.total{provider, model, error_type}`
   - `rag.empty_results.total{provider, model}`

2. **Histograms**
   - `rag.latency.seconds{provider, model, operation}`
   - `rag.document_count{provider, model}`
   - `rag.embedding.dimensions{provider, model}`

3. **Gauges**
   - `rag.active_requests{provider}`
   - `rag.cache_hit_rate{provider}`

#### Metrics Implementation
```python
# Using prometheus_client or similar
from prometheus_client import Counter, Histogram, Gauge

rag_calls = Counter('rag_calls_total', 'Total RAG calls', ['provider', 'model', 'status'])
rag_latency = Histogram('rag_latency_seconds', 'RAG operation latency', ['provider', 'model', 'operation'])
rag_errors = Counter('rag_errors_total', 'RAG errors', ['provider', 'model', 'error_type'])
```

### 3. Logging Middleware Pattern

```python
class RAGLoggingMiddleware:
    def __init__(self, rag_instance):
        self.rag = rag_instance
        self.logger = structlog.get_logger()
    
    def __call__(self, query, language="en"):
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        
        self.logger.info("rag_call_start", 
            trace_id=trace_id,
            provider=self.rag.provider,
            model=self.rag.model,
            query_length=len(query))
        
        try:
            result = self.rag(query, language)
            latency_ms = (time.time() - start_time) * 1000
            
            # Analyze return shape
            return_shape = self._analyze_shape(result)
            
            self.logger.info("rag_call_success",
                trace_id=trace_id,
                latency_ms=latency_ms,
                return_shape=return_shape,
                status="success" if result[0] else "empty")
            
            # Update metrics
            rag_calls.labels(
                provider=self.rag.provider,
                model=self.rag.model,
                status="success"
            ).inc()
            
            return result
            
        except Exception as e:
            self.logger.error("rag_call_error",
                trace_id=trace_id,
                error_type=type(e).__name__,
                error_message=str(e))
            
            rag_errors.labels(
                provider=self.rag.provider,
                model=self.rag.model,
                error_type=type(e).__name__
            ).inc()
            
            raise
```

### 4. Dashboard Specifications

#### Primary Dashboard: RAG Health Overview
- **Success Rate by Provider**: Line chart showing success percentage over time
- **Latency P50/P95/P99**: Heatmap by provider/model combination
- **Error Rate Trends**: Stacked area chart by error type
- **Active Requests**: Real-time gauge per provider

#### Debugging Dashboard: Shape Analysis
- **Return Type Distribution**: Pie chart of tuple vs list vs other
- **Empty Results Frequency**: Time series by provider
- **Shape Mismatch Alerts**: Table of recent mismatches with trace IDs
- **Tuple Unpack Failures**: Counter with drill-down to traces

### 5. Alert Definitions

#### Critical Alerts
1. **Tuple Unpack Failure Rate > 1%**: Page on-call
2. **Provider Error Rate > 10%**: Email to team
3. **All Providers Down**: Page on-call immediately

#### Warning Alerts
1. **Empty Results > 20%**: Slack notification
2. **Latency P95 > 5 seconds**: Dashboard annotation
3. **Shape Mismatch Detected**: Log to debug channel

## Implementation Phases

### Phase 1: Core Logging (2 hours)
1. Add structured logging library (structlog or python-json-logger)
2. Instrument RAG.call() with basic shape logging
3. Add trace IDs for request correlation

### Phase 2: Metrics Collection (1 hour)
1. Integrate prometheus_client or similar
2. Add counters and histograms at key points
3. Expose /metrics endpoint

### Phase 3: Advanced Tracking (1 hour)
1. Implement shape analysis utilities
2. Add provider-specific error classification
3. Create logging middleware wrapper

## Testing Strategy

### Unit Tests
```python
def test_logging_middleware_captures_shape():
    """Verify middleware logs correct return shapes"""
    mock_rag = Mock(return_value=("answer", ["doc1", "doc2"]))
    middleware = RAGLoggingMiddleware(mock_rag)
    
    with patch('structlog.get_logger') as mock_logger:
        result = middleware("test query")
        
        # Verify shape was logged
        mock_logger.info.assert_called_with(
            "rag_call_success",
            return_shape={"type": "tuple", "length": 2},
            # ... other fields
        )

def test_metrics_increment_on_error():
    """Verify error counters increment correctly"""
    mock_rag = Mock(side_effect=ValueError("Test error"))
    middleware = RAGLoggingMiddleware(mock_rag)
    
    with patch('rag_errors') as mock_counter:
        with pytest.raises(ValueError):
            middleware("test query")
        
        mock_counter.labels.assert_called_with(
            error_type="ValueError"
        )
```

### Integration Tests
1. **End-to-end shape tracking**: Query → Log → Metric → Dashboard
2. **Multi-provider testing**: Verify each provider's metrics are isolated
3. **Performance impact**: Ensure < 5ms overhead per request

## Success Criteria

### Quantitative Metrics
- **Zero tuple unpack errors** after shape logging deployed
- **< 5ms latency overhead** from logging/metrics
- **100% trace coverage** for RAG operations
- **< 1% log data loss** under load

### Qualitative Goals
- **Actionable alerts**: Each alert has clear remediation steps
- **Self-service debugging**: Developers can trace issues without assistance
- **Proactive monitoring**: Issues detected before user reports

## Risk Mitigation

### Performance Risks
- **Mitigation**: Async logging, sampling for high-volume endpoints
- **Fallback**: Feature flag to disable verbose logging

### Storage Risks
- **Mitigation**: Log rotation, retention policies, aggregation
- **Fallback**: Write to local disk if remote logging fails

### Privacy Risks
- **Mitigation**: Never log query content, only metadata
- **Fallback**: PII detection and masking utilities

## Dependencies
- Python logging configuration exists
- Metrics endpoint can be exposed
- Dashboard tooling available (Grafana/DataDog/etc)

## Estimated Effort
- **Development**: 4 hours
- **Testing**: 1 hour
- **Documentation**: 1 hour
- **Total**: 6 hours (includes buffer)

## Definition of Done
- [ ] Structured logging implemented with shape tracking
- [ ] Metrics exposed at /metrics endpoint
- [ ] Unit tests achieve 90% coverage
- [ ] Integration tests pass with all providers
- [ ] Dashboard queries documented
- [ ] Alert rules configured
- [ ] Performance impact < 5ms verified
- [ ] Documentation updated with troubleshooting guide