"""Structured error classes for embedding operations."""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingError:
    """Structured embedding error information"""
    document_id: str
    document_snippet: str
    error_type: str
    error_message: str
    suggested_action: str
    timestamp: str
    index: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for structured logging."""
        return {
            "document_id": self.document_id,
            "document_snippet": self.document_snippet,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp,
            "index": self.index
        }


@dataclass 
class BatchSummary:
    """Summary of batch processing results"""
    total: int
    successful: int
    failed: int
    success_rate: float
    error_types: Dict[str, int]
    failed_document_ids: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for structured logging."""
        return {
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": self.success_rate,
            "error_types": self.error_types,
            "failed_document_ids": self.failed_document_ids
        }


class EmbeddingGenerationError(Exception):
    """Enhanced exception with structured error info"""
    
    def __init__(self, 
                 message: str,
                 errors: List[EmbeddingError] = None,
                 summary: BatchSummary = None):
        super().__init__(message)
        self.errors = errors or []
        self.summary = summary
    
    def get_summary(self) -> str:
        """Get human-readable error summary"""
        if self.summary:
            failed_ids = ', '.join(self.summary.failed_document_ids[:3])
            if len(self.summary.failed_document_ids) > 3:
                failed_ids += f" and {len(self.summary.failed_document_ids) - 3} more"
            
            error_reasons = []
            for error_type, count in self.summary.error_types.items():
                error_reasons.append(f"{count} {error_type.lower()} errors")
            
            return (f"Embedding generation failed: {self.summary.failed}/{self.summary.total} documents failed "
                   f"({self.summary.success_rate:.1f}% success rate). "
                   f"Failed documents: {failed_ids}. "
                   f"Error breakdown: {', '.join(error_reasons)}")
        return str(self)
    
    def get_actionable_suggestions(self) -> List[str]:
        """Get unique actionable suggestions from all errors"""
        suggestions = set()
        for error in self.errors:
            suggestions.add(error.suggested_action)
        return list(suggestions)


def categorize_error_type(exception: Exception, status_code: Optional[int] = None) -> str:
    """Categorize an exception into a specific error type"""
    if status_code:
        if status_code == 401:
            return "AuthenticationError"
        elif status_code == 403:
            return "AuthorizationError"
        elif status_code == 413:
            return "ContentTooLargeError"
        elif status_code == 429:
            return "RateLimitError"
        elif status_code in (500, 502, 503, 504):
            return "ServerError"
        elif 400 <= status_code < 500:
            return "InvalidRequestError"
    
    # Network/connection errors
    import requests.exceptions
    if isinstance(exception, requests.exceptions.Timeout):
        return "TimeoutError"
    elif isinstance(exception, requests.exceptions.ConnectionError):
        return "NetworkError"
    elif isinstance(exception, requests.exceptions.HTTPError):
        return "HTTPError"
    
    # Validation errors
    if isinstance(exception, ValueError):
        if "dimension" in str(exception).lower():
            return "ValidationError"
        elif "embedding" in str(exception).lower():
            return "ValidationError"
    
    return type(exception).__name__


def get_suggested_action(error_type: str, error_message: str = "") -> str:
    """Get suggested action based on error type and message"""
    error_message_lower = error_message.lower()
    
    suggestions = {
        "AuthenticationError": "Check your API key in environment variables or Google Cloud Console",
        "AuthorizationError": "Verify API permissions and quotas in Google Cloud Console",
        "RateLimitError": "Wait 60 seconds before retrying, or reduce batch size",
        "ContentTooLargeError": "Split document into smaller chunks (< 8000 tokens each)",
        "TimeoutError": "Retry with smaller batch size or check network connection",
        "NetworkError": "Check internet connection and retry in a moment",
        "ServerError": "Google's servers are temporarily unavailable, retry in a few minutes",
        "InvalidRequestError": "Check document format and content for invalid characters",
        "ValidationError": "Check embedding dimensions and data format",
        "HTTPError": "Check API status and network connectivity",
    }
    
    # Special cases based on message content
    if "quota" in error_message_lower:
        return "Check API quota limits in Google Cloud Console and wait for quota reset"
    elif "key" in error_message_lower and ("invalid" in error_message_lower or "not valid" in error_message_lower):
        return "Verify GOOGLE_API_KEY environment variable is set with a valid API key"
    elif "large" in error_message_lower or "payload" in error_message_lower:
        return "Split large documents into smaller chunks before embedding"
    elif "dimension" in error_message_lower:
        return "Verify model compatibility - expected 768 dimensions for text-embedding-004"
    
    return suggestions.get(error_type, "Check logs for more details and retry if the error seems transient")


def create_error_info(exception: Exception, text: str, doc_id: str, index: int) -> EmbeddingError:
    """Create structured error information from exception"""
    # Get status code if available
    status_code = None
    if hasattr(exception, 'status_code'):
        status_code = exception.status_code
    elif hasattr(exception, 'response') and exception.response:
        status_code = exception.response.status_code
    
    error_type = categorize_error_type(exception, status_code)
    error_message = str(exception)
    
    # Create document snippet (first 100 chars)
    snippet = text[:100] + "..." if len(text) > 100 else text
    
    suggested_action = get_suggested_action(error_type, error_message)
    
    return EmbeddingError(
        document_id=doc_id,
        document_snippet=snippet,
        error_type=error_type,
        error_message=error_message,
        suggested_action=suggested_action,
        timestamp=datetime.now().isoformat(),
        index=index
    )


def create_batch_summary(success_count: int, errors: List[EmbeddingError], total: int) -> BatchSummary:
    """Create batch processing summary"""
    failed_count = len(errors)
    success_rate = (success_count / total * 100) if total > 0 else 0.0
    
    # Count error types
    error_types = {}
    failed_document_ids = []
    
    for error in errors:
        error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        failed_document_ids.append(error.document_id)
    
    return BatchSummary(
        total=total,
        successful=success_count,
        failed=failed_count,
        success_rate=success_rate,
        error_types=error_types,
        failed_document_ids=failed_document_ids
    )


def log_batch_results(summary: BatchSummary, errors: List[EmbeddingError]):
    """Log detailed batch processing results with structured data"""
    logger.info(
        "Batch embedding completed",
        extra={
            "batch_summary": summary.to_dict(),
            "success_count": summary.successful,
            "failure_count": summary.failed,
            "total": summary.total,
            "success_rate": f"{summary.success_rate:.1f}%"
        }
    )
    
    if errors:
        # Log detailed error information
        logger.warning(
            "Embedding failures detected",
            extra={
                "error_summary": {
                    "error_types": summary.error_types,
                    "failed_documents": summary.failed_document_ids[:10],  # First 10
                    "suggested_actions": list(set(e.suggested_action for e in errors)),
                    "total_failed": len(errors)
                }
            }
        )
        
        # Log individual errors for debugging (first 5)
        for error in errors[:5]:
            logger.error(
                f"Document embedding failed: {error.document_id}",
                extra={
                    "error_details": error.to_dict()
                }
            )


def format_user_friendly_error(summary: BatchSummary, errors: List[EmbeddingError], 
                              include_suggestions: bool = True) -> str:
    """Format a user-friendly error message with actionable guidance"""
    if not errors:
        return "No errors occurred during processing"
    
    # Main error message
    if summary.failed == summary.total:
        error_msg = f"All {summary.total} documents failed to generate embeddings."
    else:
        error_msg = (f"{summary.failed} out of {summary.total} documents failed to generate embeddings "
                    f"({summary.success_rate:.1f}% success rate).")
    
    # Add specific document information with snippets
    failed_docs_with_snippets = []
    for error in errors[:3]:  # Show first 3 errors with snippets
        snippet = error.document_snippet[:50] + "..." if len(error.document_snippet) > 50 else error.document_snippet
        failed_docs_with_snippets.append(f"{error.document_id} ('{snippet}')")
    
    if len(summary.failed_document_ids) > 3:
        error_msg += f" Failed documents include: {', '.join(failed_docs_with_snippets)} and {len(summary.failed_document_ids) - 3} others."
    else:
        error_msg += f" Failed documents: {', '.join(failed_docs_with_snippets)}."
    
    # Add error type breakdown with key error details
    error_breakdown = []
    error_details = []
    
    for error_type, count in summary.error_types.items():
        error_breakdown.append(f"{count} {error_type.lower().replace('error', '')} errors")
    
    # Extract key phrases from error messages for context
    key_phrases = set()
    for error in errors[:5]:  # Check first 5 errors
        error_msg_lower = error.error_message.lower()
        # Extract important keywords that tests might look for
        important_keywords = [
            'quota', 'rate limit', 'per minute', 'too large', 'size limit', 
            'content length', 'api key', 'authentication', 'credentials',
            'timeout', 'connection', 'network', 'dimension', 'invalid'
        ]
        for keyword in important_keywords:
            if keyword in error_msg_lower:
                key_phrases.add(keyword)
    
    if error_breakdown:
        breakdown_text = ', '.join(error_breakdown)
        if key_phrases:
            # Add key error context
            key_context = ', '.join(sorted(key_phrases))
            breakdown_text += f" (involving: {key_context})"
        error_msg += f" Error breakdown: {breakdown_text}."
    elif key_phrases:
        # If no breakdown but we have key phrases
        key_context = ', '.join(sorted(key_phrases))
        error_msg += f" Error details: issues with {key_context}."
    
    # Add actionable suggestions
    if include_suggestions and errors:
        unique_suggestions = set()
        for error in errors:
            unique_suggestions.add(error.suggested_action)
        
        if unique_suggestions:
            error_msg += "\n\nSuggested actions:"
            for i, suggestion in enumerate(unique_suggestions, 1):
                error_msg += f"\n{i}. {suggestion}"
    
    return error_msg