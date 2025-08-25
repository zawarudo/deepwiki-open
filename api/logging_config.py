import logging
import json
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler


class IgnoreLogChangeDetectedFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return "Detected file change in" not in record.getMessage()


class StructuredFormatter(logging.Formatter):
    """Formatter that supports both structured logging and traditional formatting."""
    
    def format(self, record):
        # Create base log entry
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Add structured data if present in record.extra
        if hasattr(record, 'batch_summary'):
            log_entry['batch_summary'] = record.batch_summary
        if hasattr(record, 'error_summary'):
            log_entry['error_summary'] = record.error_summary
        if hasattr(record, 'error_details'):
            log_entry['error_details'] = record.error_details
        if hasattr(record, 'success_count'):
            log_entry['success_count'] = record.success_count
        if hasattr(record, 'failure_count'):
            log_entry['failure_count'] = record.failure_count
        if hasattr(record, 'total'):
            log_entry['total'] = record.total
        if hasattr(record, 'success_rate'):
            log_entry['success_rate'] = record.success_rate
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(format: str = None, structured: bool = None):
    """
    Configure logging for the application with log rotation.

    Args:
        format (str, optional): Custom log format string
        structured (bool, optional): Use structured JSON logging. 
                                   If None, determined by LOG_FORMAT env var.

    Environment variables:
        LOG_LEVEL: Log level (default: INFO)
        LOG_FILE_PATH: Path to log file (default: logs/application.log)
        LOG_MAX_SIZE: Max size in MB before rotating (default: 10MB)
        LOG_BACKUP_COUNT: Number of backup files to keep (default: 5)
        LOG_FORMAT: 'structured' for JSON logging, 'text' for traditional (default: text)

    Ensures log directory exists, prevents path traversal, and configures
    both rotating file and console handlers with structured logging support.
    """
    # Determine log directory and default file path
    base_dir = Path(__file__).parent
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    default_log_file = log_dir / "application.log"

    # Get log level from environment
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Get log file path
    log_file_path = Path(os.environ.get("LOG_FILE_PATH", str(default_log_file)))

    # Secure path check: must be inside logs/ directory
    log_dir_resolved = log_dir.resolve()
    resolved_path = log_file_path.resolve()
    if not str(resolved_path).startswith(str(log_dir_resolved) + os.sep):
        raise ValueError(f"LOG_FILE_PATH '{log_file_path}' is outside the trusted log directory '{log_dir_resolved}'")

    # Ensure parent directories exist
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    # Get max log file size (default: 10MB)
    try:
        max_mb = int(os.environ.get("LOG_MAX_SIZE", 10))  # 10MB default
        max_bytes = max_mb * 1024 * 1024
    except (TypeError, ValueError):
        max_bytes = 10 * 1024 * 1024  # fallback to 10MB on error

    # Get backup count (default: 5)
    try:
        backup_count = int(os.environ.get("LOG_BACKUP_COUNT", 5))
    except ValueError:
        backup_count = 5

    # Determine logging format
    if structured is None:
        log_format_env = os.environ.get("LOG_FORMAT", "text").lower()
        structured = log_format_env == "structured"
    
    # Configure format
    if structured:
        # Use structured JSON formatter
        formatter = StructuredFormatter()
    else:
        # Use traditional text formatter
        log_format = format or "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
        formatter = logging.Formatter(log_format)

    # Create handlers
    handlers = []
    
    # Skip file handler if DISABLE_FILE_LOGGING is set (for tests)
    if not os.environ.get("DISABLE_FILE_LOGGING"):
        try:
            file_handler = RotatingFileHandler(resolved_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.addFilter(IgnoreLogChangeDetectedFilter())
            handlers.append(file_handler)
        except PermissionError as e:
            # Log to console that file logging is disabled due to permission error
            print(f"Warning: Cannot create log file at {resolved_path} due to permission error. File logging disabled.")
            # Continue without file handler
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(IgnoreLogChangeDetectedFilter())
    handlers.append(console_handler)

    # Apply logging configuration
    logging.basicConfig(level=log_level, handlers=handlers, force=True)
    
    # Keep MLflow warning visible - it's harmless but good to know about
    # logging.getLogger("adalflow.tracing.mlflow_integration").setLevel(logging.ERROR)

    # Log configuration info
    logger = logging.getLogger(__name__)
    logger.debug(
        f"Logging configured: level={log_level_str}, "
        f"format={'structured' if structured else 'text'}, "
        f"file={resolved_path}, max_size={max_bytes} bytes, "
        f"backup_count={backup_count}"
    )
