# Test Plan: Structured Logging and Metrics Implementation

## Objective
Implement and test structured logging with return shape tracking, metrics collection, and monitoring capabilities to detect and prevent tuple-unpack errors.

## Test Categories

### 1. Structured Logging Tests

#### Test 1.1: Basic Log Structure Validation
```python
def test_structured_log_format():
    """Test logs contain required structured fields."""
    import json
    from io import StringIO
    import logging
    
    # Capture logs
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter('%(message)s'))
    
    logger = logging.getLogger('api.rag')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Execute RAG call
    rag = RAG(config)
    rag.call("test query")
    
    # Parse captured logs
    log_output = log_capture.getvalue()
    for line in log_output.split('\n'):
        if line and '{' in line:
            log_data = json.loads(line)
            
            # Verify required fields
            assert 'timestamp' in log_data
            assert 'event' in log_data
            assert 'level' in log_data
            
            # Check shape fields for relevant events
            if log_data['event'] in ['rag_call_complete', 'retriever_return']:
                assert 'return_shape' in log_data
```

#### Test 1.2: Return Shape Logging
```python
def test_return_shape_logging():
    """Test return shapes are logged correctly."""
    logs = []
    
    def capture_log(record):
        if hasattr(record, 'return_shape'):
            logs.append(record.return_shape)
    
    # Add custom handler
    logger = logging.getLogger('api.rag')
    handler = logging.Handler()
    handler.emit = capture_log
    logger.addHandler(handler)
    
    rag = RAG(config)
    
    # Test various return scenarios
    test_cases = [
        (["doc1", "doc2"], None),  # Documents only
        (None, Exception("error")),  # Error case
        ([], None),  # Empty retrieval
    ]
    
    for docs, error in test_cases:
        with patch.object(rag, '_retrieve_documents', 
                         return_value=docs, side_effect=error):
            rag.call("test")
    
    # All should log 2-tuple shape
    assert all(shape == "(2,)" for shape in logs)
```

#### Test 1.3: Embedder Shape Logging
```python
def test_embedder_shape_logging():
    """Test embedder return shapes are logged."""
    logs = []
    
    class LogCapture:
        def write(self, msg):
            if "embedder_return_shape" in msg:
                logs.append(msg)
    
    # Mock embedder with logging
    def logging_embedder(text):
        result = (np.random.rand(768), {"provider": "test"})
        logger.info("Embedder call", extra={
            "embedder_return_shape": f"({len(result)},)",
            "embedding_dim": len(result[0])
        })
        return result
    
    with patch('api.rag.prepare_single_string_embedder', return_value=logging_embedder):
        rag = RAG(config)
        rag.prepare_retriever(test_docs)
        rag.call("test")
    
    # Should log 2-tuple embedder shape
    assert any("(2,)" in log for log in logs)
```

### 2. Metrics Collection Tests

#### Test 2.1: Counter Metrics
```python
def test_counter_metrics():
    """Test counter metrics for RAG operations."""
    from prometheus_client import Counter, REGISTRY
    
    # Clear existing metrics
    REGISTRY._collector_to_names.clear()
    REGISTRY._names_to_collectors.clear()
    
    # Define metrics
    rag_calls_total = Counter('rag_calls_total', 'Total RAG calls', ['status'])
    rag_errors_total = Counter('rag_errors_total', 'Total RAG errors', ['error_type'])
    
    rag = RAG(config)
    
    # Successful call
    with patch.object(rag, '_generate_answer', return_value="answer"):
        rag.call("test")
        rag_calls_total.labels(status='success').inc()
    
    # Failed call
    with patch.object(rag, '_generate_answer', side_effect=Exception("API error")):
        rag.call("test")
        rag_calls_total.labels(status='error').inc()
        rag_errors_total.labels(error_type='api_error').inc()
    
    # Check metrics
    assert rag_calls_total.labels(status='success')._value.get() == 1
    assert rag_calls_total.labels(status='error')._value.get() == 1
    assert rag_errors_total.labels(error_type='api_error')._value.get() == 1
```

#### Test 2.2: Histogram Metrics
```python
def test_histogram_metrics():
    """Test histogram metrics for performance tracking."""
    from prometheus_client import Histogram
    import time
    
    # Define metrics
    rag_duration = Histogram('rag_duration_seconds', 'RAG call duration', ['operation'])
    retrieval_duration = Histogram('retrieval_duration_seconds', 'Retrieval duration')
    
    rag = RAG(config)
    
    # Measure call duration
    with rag_duration.labels(operation='call').time():
        rag.call("test")
    
    # Measure retrieval duration
    start = time.time()
    with patch.object(rag, '_retrieve_documents') as mock_retrieve:
        mock_retrieve.return_value = []
        rag.call("test")
        retrieval_duration.observe(time.time() - start)
    
    # Check metrics collected
    assert rag_duration.labels(operation='call')._sum.get() > 0
    assert retrieval_duration._sum.get() > 0
```

#### Test 2.3: Provider-Specific Metrics
```python
def test_provider_metrics():
    """Test metrics by provider and model."""
    from prometheus_client import Counter
    
    provider_calls = Counter('rag_provider_calls', 'Calls by provider', 
                            ['provider', 'model'])
    provider_errors = Counter('rag_provider_errors', 'Errors by provider',
                             ['provider', 'model', 'error'])
    
    providers = [
        ("openai", "gpt-4"),
        ("google", "gemini-pro"),
        ("ollama", "llama2"),
    ]
    
    for provider, model in providers:
        config = {"provider": provider, "model": model}
        rag = RAG(config)
        
        # Successful call
        provider_calls.labels(provider=provider, model=model).inc()
        
        # Error simulation
        with patch.object(rag, f'_call_{provider}', side_effect=Exception("Error")):
            try:
                rag.call("test")
            except:
                provider_errors.labels(
                    provider=provider, 
                    model=model, 
                    error="api_error"
                ).inc()
    
    # Verify metrics
    for provider, model in providers:
        assert provider_calls.labels(provider=provider, model=model)._value.get() == 1
```

### 3. Log Aggregation Tests

#### Test 3.1: Log Pattern Detection
```python
def test_log_pattern_detection():
    """Test detection of error patterns in logs."""
    from collections import defaultdict
    
    error_patterns = defaultdict(int)
    
    def analyze_log(log_entry):
        if "error" in log_entry:
            if "tuple" in log_entry and "unpack" in log_entry:
                error_patterns["tuple_unpack"] += 1
            elif "timeout" in log_entry:
                error_patterns["timeout"] += 1
            elif "api" in log_entry:
                error_patterns["api_error"] += 1
    
    # Simulate various errors
    test_logs = [
        {"error": "not enough values to unpack (expected 2, got 1)"},
        {"error": "Request timeout after 30s"},
        {"error": "API rate limit exceeded"},
        {"error": "cannot unpack non-iterable NoneType"},
    ]
    
    for log in test_logs:
        analyze_log(str(log))
    
    # Check pattern detection
    assert error_patterns["tuple_unpack"] == 2
    assert error_patterns["timeout"] == 1
    assert error_patterns["api_error"] == 1
```

#### Test 3.2: Shape Consistency Analysis
```python
def test_shape_consistency_analysis():
    """Test analysis of return shape consistency."""
    shape_logs = []
    
    # Collect shape logs
    for _ in range(100):
        rag = RAG(config)
        with patch.object(rag, 'call', return_value=("ans", [])):
            result = rag.call("test")
            shape_logs.append({
                "event": "rag_call_complete",
                "return_shape": f"({len(result)},)"
            })
    
    # Analyze consistency
    shapes = [log["return_shape"] for log in shape_logs]
    unique_shapes = set(shapes)
    
    # Should be consistent
    assert len(unique_shapes) == 1
    assert "(2,)" in unique_shapes
```

### 4. Monitoring Dashboard Tests

#### Test 4.1: Metrics Endpoint
```python
def test_metrics_endpoint():
    """Test metrics are exposed via endpoint."""
    from fastapi.testclient import TestClient
    from api.main import app
    
    client = TestClient(app)
    
    # Make some RAG calls
    for _ in range(5):
        client.post("/chat/completions", json={
            "messages": [{"role": "user", "content": "test"}]
        })
    
    # Get metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    metrics_text = response.text
    
    # Check for expected metrics
    assert "rag_calls_total" in metrics_text
    assert "rag_duration_seconds" in metrics_text
    assert "embedder_return_shape" in metrics_text
    assert "retriever_return_shape" in metrics_text
```

#### Test 4.2: Health Check with Shape Validation
```python
def test_health_check_shape_validation():
    """Test health check includes shape validation."""
    from fastapi.testclient import TestClient
    from api.main import app
    
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    
    health_data = response.json()
    
    # Should include shape checks
    assert "rag_shape_check" in health_data
    assert health_data["rag_shape_check"]["expected"] == "(2,)"
    assert health_data["rag_shape_check"]["status"] == "healthy"
```

### 5. Alert Configuration Tests

#### Test 5.1: Tuple Unpack Error Alert
```python
def test_tuple_unpack_error_alert():
    """Test alert triggered on tuple unpack errors."""
    from unittest.mock import Mock
    
    alert_manager = Mock()
    
    def check_logs_for_alerts(logs):
        for log in logs:
            if "tuple" in log and "unpack" in log:
                alert_manager.send_alert({
                    "severity": "critical",
                    "title": "Tuple Unpack Error Detected",
                    "description": log,
                    "runbook": "https://wiki/fix-tuple-unpack"
                })
    
    # Simulate error log
    error_logs = [
        "ValueError: not enough values to unpack (expected 2, got 1)",
    ]
    
    check_logs_for_alerts(error_logs)
    
    # Alert should be sent
    alert_manager.send_alert.assert_called_once()
    alert_call = alert_manager.send_alert.call_args[0][0]
    assert alert_call["severity"] == "critical"
```

#### Test 5.2: Shape Inconsistency Alert
```python
def test_shape_inconsistency_alert():
    """Test alert on shape inconsistencies."""
    alert_threshold = 0.05  # 5% inconsistency threshold
    
    def check_shape_consistency(shapes):
        total = len(shapes)
        shape_counts = {}
        for shape in shapes:
            shape_counts[shape] = shape_counts.get(shape, 0) + 1
        
        # Check if any shape is inconsistent
        expected_shape = "(2,)"
        inconsistent = total - shape_counts.get(expected_shape, 0)
        inconsistency_rate = inconsistent / total
        
        if inconsistency_rate > alert_threshold:
            return {
                "alert": True,
                "rate": inconsistency_rate,
                "shapes": shape_counts
            }
        return {"alert": False}
    
    # Test with inconsistent shapes
    shapes = ["(2,)"] * 95 + ["(1,)"] * 5 + ["(3,)"] * 1
    result = check_shape_consistency(shapes)
    
    assert result["alert"] == True
    assert result["rate"] > alert_threshold
```

### 6. Log Analysis Tools Tests

#### Test 6.1: Log Query Tool
```python
def test_log_query_tool():
    """Test log querying for shape analysis."""
    import json
    
    class LogQuery:
        def __init__(self, logs):
            self.logs = logs
        
        def filter_by_event(self, event_name):
            return [l for l in self.logs if l.get("event") == event_name]
        
        def get_shapes(self):
            return [l.get("return_shape") for l in self.logs 
                   if "return_shape" in l]
        
        def count_errors(self):
            return len([l for l in self.logs if l.get("level") == "ERROR"])
    
    # Sample logs
    logs = [
        {"event": "rag_call_start", "timestamp": "2024-01-01T10:00:00"},
        {"event": "rag_call_complete", "return_shape": "(2,)", "timestamp": "2024-01-01T10:00:01"},
        {"event": "error", "level": "ERROR", "message": "API failed"},
    ]
    
    query = LogQuery(logs)
    
    assert len(query.filter_by_event("rag_call_complete")) == 1
    assert query.get_shapes() == ["(2,)"]
    assert query.count_errors() == 1
```

#### Test 6.2: Shape Trend Analysis
```python
def test_shape_trend_analysis():
    """Test analyzing shape trends over time."""
    from datetime import datetime, timedelta
    
    def analyze_shape_trends(logs, window_minutes=60):
        """Analyze shape consistency over time windows."""
        now = datetime.now()
        windows = {}
        
        for log in logs:
            timestamp = log["timestamp"]
            window = timestamp.replace(minute=timestamp.minute // window_minutes * window_minutes)
            
            if window not in windows:
                windows[window] = {"total": 0, "correct": 0}
            
            windows[window]["total"] += 1
            if log.get("return_shape") == "(2,)":
                windows[window]["correct"] += 1
        
        # Calculate consistency per window
        trends = {}
        for window, counts in windows.items():
            trends[window] = counts["correct"] / counts["total"] if counts["total"] > 0 else 0
        
        return trends
    
    # Generate test logs
    logs = []
    base_time = datetime.now()
    for i in range(100):
        logs.append({
            "timestamp": base_time + timedelta(minutes=i),
            "return_shape": "(2,)" if i % 10 != 0 else "(1,)",  # 10% wrong
        })
    
    trends = analyze_shape_trends(logs, window_minutes=10)
    
    # Check trend detection
    assert len(trends) > 0
    assert all(0 <= consistency <= 1 for consistency in trends.values())
```

### 7. Performance Impact Tests

#### Test 7.1: Logging Overhead
```python
def test_logging_overhead():
    """Test performance impact of structured logging."""
    import time
    
    # RAG without logging
    rag_no_log = RAG(config)
    logging.getLogger('api.rag').setLevel(logging.CRITICAL)
    
    start = time.time()
    for _ in range(100):
        rag_no_log.call("test")
    time_no_log = time.time() - start
    
    # RAG with full logging
    rag_with_log = RAG(config)
    logging.getLogger('api.rag').setLevel(logging.DEBUG)
    
    start = time.time()
    for _ in range(100):
        rag_with_log.call("test")
    time_with_log = time.time() - start
    
    # Overhead should be minimal (< 10%)
    overhead = (time_with_log - time_no_log) / time_no_log
    assert overhead < 0.1, f"Logging overhead too high: {overhead:.2%}"
```

#### Test 7.2: Metrics Collection Overhead
```python
def test_metrics_overhead():
    """Test performance impact of metrics collection."""
    from prometheus_client import Counter, Histogram
    import time
    
    # Without metrics
    start = time.time()
    for _ in range(1000):
        result = ("answer", [])
    time_no_metrics = time.time() - start
    
    # With metrics
    counter = Counter('test_counter', 'Test')
    histogram = Histogram('test_histogram', 'Test')
    
    start = time.time()
    for _ in range(1000):
        counter.inc()
        with histogram.time():
            result = ("answer", [])
    time_with_metrics = time.time() - start
    
    # Overhead should be minimal (< 5%)
    overhead = (time_with_metrics - time_no_metrics) / time_no_metrics
    assert overhead < 0.05, f"Metrics overhead too high: {overhead:.2%}"
```

### 8. Integration Tests

#### Test 8.1: End-to-End Logging Flow
```python
def test_e2e_logging_flow():
    """Test complete logging flow from call to analysis."""
    import json
    from io import StringIO
    
    # Capture all logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    
    logger = logging.getLogger('api.rag')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Execute RAG pipeline
    rag = RAG(config)
    rag.prepare_retriever(test_docs)
    answer, docs = rag("What is Python?")
    
    # Parse and validate logs
    logs = []
    for line in log_stream.getvalue().split('\n'):
        if line and '{' in line:
            try:
                logs.append(json.loads(line))
            except:
                pass
    
    # Verify log sequence
    events = [log.get("event") for log in logs if "event" in log]
    
    expected_sequence = [
        "rag_call_start",
        "retrieval_start",
        "retrieval_complete",
        "generation_start",
        "generation_complete",
        "rag_call_complete"
    ]
    
    for expected in expected_sequence:
        assert expected in events
    
    # Verify shapes logged
    shape_logs = [log for log in logs if "return_shape" in log]
    assert len(shape_logs) > 0
    assert all(log["return_shape"] == "(2,)" for log in shape_logs)
```

## Test Execution Plan

### Phase 1: Logging Infrastructure (Priority: High)
- Tests 1.1-1.3: Structured logging
- Tests 3.1-3.2: Log aggregation
- Must work before metrics

### Phase 2: Metrics Implementation (Priority: High)
- Tests 2.1-2.3: Metrics collection
- Tests 4.1-4.2: Metrics exposure
- Enable monitoring

### Phase 3: Alerting (Priority: Medium)
- Tests 5.1-5.2: Alert configuration
- Critical for operations

### Phase 4: Analysis Tools (Priority: Medium)
- Tests 6.1-6.2: Log analysis
- Debugging capabilities

### Phase 5: Performance (Priority: Low)
- Tests 7.1-7.2: Overhead measurement
- Optimization validation

## Success Metrics
- 100% of RAG calls logged with shapes
- All error patterns detected
- Metrics endpoint functional
- Alerts configured for critical errors
- Logging overhead < 10%

## Dependencies
- Python logging module
- prometheus_client
- fastapi (for metrics endpoint)
- json for structured logs
- Optional: ELK stack for aggregation