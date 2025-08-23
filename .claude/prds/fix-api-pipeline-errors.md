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
2. **Decrease average processing time by 85%** (from 267s to 40s for failed batches)
3. **Improve successful batch processing rate to 98%+**
4. **Reduce API costs by 40%** through optimized batching
5. **Achieve 99.9% embedding completeness** for processed documents

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

### Phase 1: Immediate Fixes (Week 1)
- Add request validation and preprocessing
- Implement basic retry with batch size reduction
- Enhance error logging and diagnostics

### Phase 2: Intelligent Batching (Week 2)
- Content-aware batch sizing
- Dynamic batch size optimization
- Performance metrics collection

### Phase 3: Resilience Features (Week 3)
- Circuit breaker implementation
- Queue management system
- Comprehensive monitoring dashboard

### Phase 4: Testing & Deployment (Week 4)
- Load testing with various failure scenarios
- Gradual rollout with feature flags
- Documentation and team training

## Appendix

### Error Analysis Data
- Current batch failure rate: 20-30%
- Processing time impact: 20x slower (267s vs 13s)
- Affected API endpoint: `/batchEmbedContents`
- Error code: HTTP 400 (Bad Request)
- Fallback mechanism: Single request per document
- Code location: `api/google_embedding_client.py:108`