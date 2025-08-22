"""
Error Detection Module
Identifies and categorizes errors in API logs
"""

import re
from typing import List, Dict, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ErrorDetector:
    """Detects and categorizes errors in log entries"""
    
    def __init__(self):
        # Define error patterns with severity levels
        self.error_patterns = {
            'critical': [
                (r'CRITICAL', 'Critical system error'),
                (r'FATAL', 'Fatal error'),
                (r'PANIC', 'System panic'),
                (r'OutOfMemoryError', 'Memory exhaustion'),
                (r'StackOverflowError', 'Stack overflow'),
                (r'SystemExit', 'System exit'),
            ],
            'high': [
                (r'ERROR\s+-\s+', 'Application error'),
                (r'Exception:', 'Exception occurred'),
                (r'Traceback \(most recent call last\)', 'Python traceback'),
                (r'5\d{2}\s+error', 'HTTP 5xx server error'),
                (r'Database.*error', 'Database error'),
                (r'Connection refused', 'Connection refused'),
                (r'Service unavailable', 'Service unavailable'),
            ],
            'medium': [
                (r'4\d{2}\s+error', 'HTTP 4xx client error'),
                (r'Timeout', 'Operation timeout'),
                (r'Rate limit', 'Rate limit exceeded'),
                (r'Authentication failed', 'Auth failure'),
                (r'Permission denied', 'Permission error'),
                (r'Invalid.*request', 'Invalid request'),
            ],
            'low': [
                (r'WARNING\s+-\s+', 'Warning'),
                (r'Deprecated', 'Deprecation warning'),
                (r'Retry', 'Operation retry'),
                (r'Slow query', 'Performance warning'),
            ]
        }
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = {}
        for severity, patterns in self.error_patterns.items():
            self.compiled_patterns[severity] = [
                (re.compile(pattern, re.IGNORECASE), description)
                for pattern, description in patterns
            ]
    
    def detect_errors(self, logs: str) -> List[Dict]:
        """Detect errors in log text"""
        errors = []
        
        for line_num, line in enumerate(logs.split('\n'), 1):
            if not line.strip():
                continue
            
            for severity, patterns in self.compiled_patterns.items():
                if severity == 'low':  # Skip warnings in error detection
                    continue
                    
                for pattern, description in patterns:
                    if pattern.search(line):
                        error_info = self._extract_error_info(line, description, severity)
                        error_info['line_number'] = line_num
                        errors.append(error_info)
                        break  # Only match first pattern per line
        
        return errors
    
    def detect_warnings(self, logs: str) -> List[Dict]:
        """Detect warnings in log text"""
        warnings = []
        
        for line_num, line in enumerate(logs.split('\n'), 1):
            if not line.strip():
                continue
            
            # Only check 'low' severity patterns for warnings
            for pattern, description in self.compiled_patterns.get('low', []):
                if pattern.search(line):
                    warning_info = self._extract_error_info(line, description, 'low')
                    warning_info['line_number'] = line_num
                    warnings.append(warning_info)
                    break
        
        return warnings
    
    def _extract_error_info(self, line: str, description: str, severity: str) -> Dict:
        """Extract detailed information from error line"""
        info = {
            'severity': severity,
            'description': description,
            'raw_line': line[:500],  # Truncate very long lines
            'timestamp': self._extract_timestamp(line),
            'service': self._extract_service(line),
            'details': {}
        }
        
        # Extract HTTP status code if present
        http_match = re.search(r'\b(\d{3})\b', line)
        if http_match and http_match.group(1)[0] in '45':
            info['details']['http_status'] = http_match.group(1)
        
        # Extract error message if present
        error_msg_match = re.search(r'(ERROR|Exception|Error):\s*(.+?)(?:\n|$)', line)
        if error_msg_match:
            info['details']['error_message'] = error_msg_match.group(2).strip()
        
        # Extract file and line number if present (Python traceback)
        file_match = re.search(r'File "([^"]+)", line (\d+)', line)
        if file_match:
            info['details']['file'] = file_match.group(1)
            info['details']['code_line'] = file_match.group(2)
        
        return info
    
    def _extract_timestamp(self, line: str) -> str:
        """Extract timestamp from log line"""
        # Common timestamp patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',  # US format
            r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',    # Syslog format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_service(self, line: str) -> str:
        """Extract service name from log line"""
        # Look for common service indicators
        patterns = [
            r'api-\d+\s*\|',  # Docker compose format
            r'\[(\w+)\]',     # Bracketed service name
            r'^\w+\s*:',      # Service prefix
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                if pattern == r'\[(\w+)\]':
                    return match.group(1)
                else:
                    return match.group(0).strip(':|[]')
        
        return "unknown"
    
    def categorize_errors(self, errors: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize errors by type"""
        categories = {
            'database': [],
            'network': [],
            'authentication': [],
            'validation': [],
            'system': [],
            'application': [],
            'other': []
        }
        
        for error in errors:
            line = error.get('raw_line', '').lower()
            
            if any(term in line for term in ['database', 'sql', 'query', 'postgres', 'mysql']):
                categories['database'].append(error)
            elif any(term in line for term in ['connection', 'timeout', 'network', 'socket']):
                categories['network'].append(error)
            elif any(term in line for term in ['auth', 'permission', 'token', 'credential']):
                categories['authentication'].append(error)
            elif any(term in line for term in ['validation', 'invalid', 'required', 'format']):
                categories['validation'].append(error)
            elif any(term in line for term in ['memory', 'cpu', 'disk', 'system']):
                categories['system'].append(error)
            elif error.get('severity') in ['critical', 'high']:
                categories['application'].append(error)
            else:
                categories['other'].append(error)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}