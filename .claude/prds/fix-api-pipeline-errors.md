---
name: fix-api-pipeline-errors
description: Fix Google embedding API batch processing failures causing 20x performance degradation
status: backlog
created: 2025-08-23T07:56:00Z
---

# PRD: fix-api-pipeline-errors

## Executive Summary

The DeepWiki API pipeline is experiencing critical performance degradation due to Google embedding API batch processing failures. Currently, 20-30% of batch embedding requests fail with HTTP 400 errors, forcing the system to fall back to single-request processing. This fallback mechanism increases processing time by approximately 20x (from ~13 seconds to 267+ seconds per batch), severely impacting system throughput and user experience. This PRD outlines a comprehensive solution to fix the batch processing errors, implement intelligent retry mechanisms, and improve overall pipeline resilience.

## Problem Statement

### What problem are we solving?
The Google embedding client in our API pipeline consistently fails when processing batch embedding requests, resulting in:
- **20x performance degradation** when fallback to single requests occurs
- **Increased API costs** due to inefficient single-request processing
- **Poor user experience** with document processing taking minutes instead of seconds
- **System instability** during high-load periods due to request queue buildup

### Why is this important now?
1. **User Impact**: Document processing delays are causing user frustration and potential churn
2. **Cost Impact**: Single-request fallback increases API costs by up to 10x per failed batch
3. **Scalability**: Current error rate prevents scaling to handle increased document volume
4. **Reliability**: Silent partial failures may result in incomplete embeddings affecting search quality

## User Stories

### Primary User Personas

**1. Developer Users**
- **As a** developer integrating DeepWiki
- **I want** my documentation to be processed quickly and reliably
- **So that** I can generate wikis without delays impacting my workflow
- **Acceptance Criteria:**
  - Document batches process in under 30 seconds
  - Clear error messages when processing fails
  - Ability to retry failed documents

**2. System Administrators**
- **As a** system administrator
- **I want** to monitor and manage API pipeline health
- **So that** I can ensure reliable service delivery
- **Acceptance Criteria:**
  - Dashboard showing batch success/failure rates
  - Alerts when error rates exceed thresholds
  - Ability to adjust batch processing parameters

**3. End Users**
- **As an** end user browsing generated documentation
- **I want** complete and accurate search results
- **So that** I can find the information I need quickly
- **Acceptance Criteria:**
  - All documents have complete embeddings
  - Search results are comprehensive
  - No missing or partial content

### User Journeys

**Current Pain Journey:**
1. User uploads repository for documentation generation
2. System begins processing with 128-document batches
3. Google API returns 400 error for batch request
4. System falls back to processing each document individually
5. Processing time increases from expected 2 minutes to 40+ minutes
6. User experiences timeout or gives up waiting
7. Partial results may be saved with missing embeddings

**Desired Journey:**
1. User uploads repository for documentation generation
2. System intelligently batches documents based on content characteristics
3. If batch fails, system automatically retries with smaller batch size
4. Processing completes within expected 2-3 minute window
5. User receives complete documentation with all embeddings
6. System logs performance metrics for continuous optimization

## Requirements

### Functional Requirements

**FR1: Intelligent Batch Size Management**
- Dynamic batch size adjustment based on content characteristics
- Automatic reduction on failure (128 → 64 → 32 → 16 → 8)
- Content-aware batching (group similar-sized documents)
- Maximum retry attempts before single-request fallback

**FR2: Request Validation & Preprocessing**
- Validate text content before API submission
- Check for and handle special characters
- Enforce per-document size limits
- Remove or truncate oversized content with warnings

**FR3: Enhanced Error Handling**
- Parse and log specific Google API error reasons
- Implement exponential backoff for retries
- Track failed document indices for targeted retry
- Provide detailed error reporting to users

**FR4: Performance Monitoring**
- Real-time batch success/failure rate tracking
- Processing time metrics per batch size
- API cost tracking and optimization suggestions
- Alert system for degraded performance

**FR5: Resilience Features**
- Circuit breaker pattern for API failures
- Queue management for high-load scenarios
- Graceful degradation with quality indicators
- Automatic recovery from transient failures

### Non-Functional Requirements

**NFR1: Performance**
- Batch processing must complete within 30 seconds for 128 documents
- Single document fallback must not exceed 2 seconds per document
- System must handle 1000+ concurrent document batches
- API response time must be under 500ms for status queries

**NFR2: Reliability**
- 99.9% successful embedding generation for valid documents
- Maximum 0.1% data loss tolerance
- Automatic recovery from API outages within 5 minutes
- No silent failures - all errors must be logged and reported

**NFR3: Scalability**
- Support horizontal scaling of processing workers
- Queue system to handle burst traffic
- Configurable concurrency limits
- Resource-aware batch sizing

**NFR4: Observability**
- Comprehensive logging of all API interactions
- Metrics dashboard with real-time updates
- Tracing for request flow debugging
- Performance profiling capabilities

**NFR5: Security**
- Secure API key management
- Rate limiting to prevent abuse
- Input sanitization to prevent injection attacks
- Audit logging for compliance

## Success Criteria

### Measurable Outcomes
1. **Reduce batch failure rate from 20-30% to under 2%**
   - Validated by: Running generate_wiki.py 100 times, checking failure logs
   - Test command: `for i in {1..100}; do python scripts/generate_wiki.py --url <test-repo> && sleep 1; done`
   - Success metric: e2e_test.sh health score consistently >98
   
2. **Decrease average processing time by 85%** (from 267s to 100s for failed batches)
   - Validated by: Timing tests with known problematic repositories
   - Test command: `time python scripts/generate_wiki.py --url <large-repo>`
   - Success metric: 95th percentile under 100 seconds
   
3. **Improve successful batch processing rate to 98%+**
   - Validated by: Unit tests for batch processing logic
   - Test command: `pytest tests/test_batch_processing.py::test_success_rate`
   - Success metric: All retry scenarios pass without fallback
   
4. **Reduce API costs by 40%** through optimized batching
   - Validated by: Monitoring API call counts in logs
   - Test command: `grep "API call" api.log | wc -l` before/after comparison
   - Success metric: Call count reduction of 40%+ for same workload
   
5. **Achieve 99.9% embedding completeness** for processed documents
   - Validated by: Database query for null embeddings post-processing
   - Test command: `pytest tests/test_embedding_completeness.py`
   - Success metric: <0.1% documents with missing embeddings

### Key Metrics and KPIs
- **Batch Success Rate**: Percentage of batches processed without fallback
- **Average Processing Time**: Mean time to process 128-document batch
- **API Cost per Document**: Average cost to generate embeddings per document
- **Error Recovery Time**: Time from error detection to successful retry
- **User Satisfaction Score**: Based on processing speed feedback
- **System Uptime**: Percentage of time system is fully operational

## Constraints & Assumptions

### Technical Constraints
- Google API rate limits (6000 requests per minute)
- Maximum batch size of 128 documents per request
- API request payload size limit of 10MB
- Python asyncio concurrency limitations
- Existing codebase architecture must be maintained

### Timeline Constraints
- Solution must be implemented within 2 sprints (4 weeks)
- Minimal downtime during deployment (< 5 minutes)
- Backward compatibility with existing data required

### Resource Constraints
- Limited to current engineering team (2 developers)
- API budget cannot exceed current monthly allocation
- Must work within existing infrastructure

### Assumptions
- Google API will maintain current pricing model
- Document volume will not exceed 2x current levels
- Network latency remains consistent
- Users will accept slight processing delays for reliability

## Out of Scope

The following items are explicitly NOT included in this PRD:
1. **Changing embedding providers** (e.g., switching from Google to OpenAI)
2. **Complete API pipeline rewrite** (incremental improvements only)
3. **Real-time embedding generation** (batch processing remains)
4. **Custom embedding model training**
5. **Frontend UI changes** for error display
6. **Database schema modifications**
7. **Authentication system changes**
8. **Multi-region deployment**
9. **Caching layer implementation** (future enhancement)
10. **WebSocket-based progress updates**

## Dependencies

### External Dependencies
1. **Google Cloud Platform**
   - Vertex AI API availability
   - API quota limits and pricing
   - Service SLA guarantees

2. **Network Infrastructure**
   - Stable internet connectivity
   - DNS resolution for API endpoints
   - Firewall rules for outbound connections

3. **Third-party Libraries**
   - aiohttp for async HTTP requests
   - google-cloud-aiplatform SDK
   - retry library for resilience

### Internal Dependencies
1. **Backend Team**
   - API pipeline architecture knowledge
   - Python async programming expertise
   - Testing and deployment capabilities

2. **DevOps Team**
   - Monitoring infrastructure setup
   - Alert configuration
   - Performance metrics collection

3. **Product Team**
   - User impact assessment
   - Success criteria validation
   - Stakeholder communication

4. **Related Systems**
   - Document processing queue
   - Database for embedding storage
   - Search service consuming embeddings
   - User notification system

## Risk Assessment

### High Risk
- **Google API changes** breaking compatibility
- **Increased processing costs** if optimization fails
- **Data loss** during migration to new error handling

### Medium Risk
- **Performance regression** in other system components
- **User adoption** of new error messages/retry mechanisms
- **Technical debt** from quick fixes

### Low Risk
- **Minor bugs** in edge cases
- **Documentation** gaps for new features
- **Training** requirements for support team

## Implementation Phases

### Phase 1: Bug Reproduction & Test Development Loop (Week 1)
- **Step 1: Establish Baseline**
  - Run `python scripts/generate_wiki.py --url <test-repo> --provider google`
  - Capture API error logs using `watcher-agents/api-logs/e2e_test.sh`
  - Document current failure rate and error patterns
  
- **Step 2: Create Unit Tests**
  - Write unit tests for batch validation logic
  - Test retry mechanism with different batch sizes
  - Test error parsing and classification
  - Test fallback to single-request mode
  
- **Step 3: Fix-Test Loop**
  1. Run generate_wiki.py with test repository
  2. Check logs with e2e_test.sh (health score should be >90)
  3. Identify specific error pattern
  4. Write failing unit test for that error
  5. Implement fix
  6. Verify unit test passes
  7. Run generate_wiki.py again
  8. Repeat until health score reaches target

### Phase 2: Intelligent Batching (Week 2)
- **Test-Driven Implementation**
  - Unit test for content size calculation
  - Unit test for batch grouping algorithm
  - Unit test for dynamic size adjustment
  - Integration test with real API calls
  
- **Validation Loop**
  1. Run test suite: `pytest tests/test_batch_processing.py`
  2. Execute end-to-end test with varied repositories
  3. Monitor with e2e_test.sh for regression
  4. Adjust based on performance metrics

### Phase 3: Resilience Features (Week 3)
- **Circuit Breaker Testing**
  - Unit test for state transitions (closed → open → half-open)
  - Unit test for failure threshold detection
  - Integration test with simulated API failures
  
- **Queue Management Testing**
  - Unit test for queue overflow handling
  - Unit test for priority ordering
  - Load test with concurrent requests
  
- **Continuous Validation**
  - Run e2e_test.sh every 2 hours during development
  - Maintain health score above 95%
  - Document any new error patterns discovered

### Phase 4: Testing & Deployment (Week 4)
- **Comprehensive Test Suite**
  - Run all unit tests: `pytest tests/ -v`
  - Execute stress test: 100 concurrent wiki generations
  - Validate with different repository types and sizes
  
- **Production Readiness**
  - Feature flag implementation with gradual rollout
  - Monitor error rates in staging environment
  - A/B test against current implementation
  - Final validation: 99%+ health score for 24 hours

## Appendix

### Error Analysis Data
- Current batch failure rate: 20-30%
- Processing time impact: 20x slower (267s vs 13s)
- Affected API endpoint: `/batchEmbedContents`
- Error code: HTTP 400 (Bad Request)
- Fallback mechanism: Single request per document
- Code location: `api/google_embedding_client.py:108`

### Test Development Resources

#### Testing Scripts
1. **e2e_test.sh** - Primary test validation tool
   - Location: `watcher-agents/api-logs/e2e_test.sh`
   - Usage: `./e2e_test.sh` (returns health score 0-100)
   - Exit codes: 0 (healthy), 1 (warning), 2 (critical)
   
2. **generate_wiki.py** - End-to-end test driver
   - Location: `scripts/generate_wiki.py`
   - Test command: `python scripts/generate_wiki.py --url https://github.com/test/repo --provider google`
   - Monitor output for HTTP 400 errors
   
3. **simple_monitor.sh** - Detailed error reporting
   - Location: `watcher-agents/api-logs/simple_monitor.sh`
   - Usage: `./simple_monitor.sh report` (generates markdown report)
   
#### Unit Test Structure
```python
# tests/test_batch_processing.py
class TestBatchProcessing:
    def test_batch_size_reduction_on_failure(self):
        """Test automatic batch size reduction from 128 → 64 → 32 → 16 → 8"""
        pass
    
    def test_content_validation_before_submission(self):
        """Test that invalid content is caught before API call"""
        pass
    
    def test_retry_with_exponential_backoff(self):
        """Test retry delays: 1s, 2s, 4s, 8s, 16s"""
        pass
    
    def test_error_parsing_and_classification(self):
        """Test correct identification of error types from API response"""
        pass
    
    def test_fallback_to_single_requests(self):
        """Test graceful degradation when all batch sizes fail"""
        pass
```

#### Test Repositories for Validation
- Codeberg repo (Target repo for next steps): `https://codeberg.org/maxcodefaster/teammind`
- Small repo (< 50 files): `https://github.com/sindresorhus/is-docker`
- Medium repo (100-500 files): `https://github.com/fastapi/fastapi`
<!-- Not in scope - Large repo (1000+ files): `https://github.com/facebook/react` -->
<!-- Not in scope - Special characters test: TODO the user will find this -->
<!-- Not in scope - Large file test: TODO the user will find this -->