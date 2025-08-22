"""
Pattern Analysis Module
Analyzes log patterns for early warning signs
"""

import re
from typing import List, Dict, Set
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """Analyzes patterns and trends in API logs"""
    
    def __init__(self):
        self.pattern_cache = {}
        self.trend_window = 100  # Number of lines to consider for trend analysis
    
    def analyze_patterns(self, logs: str, custom_patterns: List[str] = None) -> Dict:
        """Analyze logs for patterns and anomalies"""
        patterns = {}
        
        # Default patterns to look for
        default_patterns = {
            'rate_limiting': r'[Rr]ate.?limit|429|too many requests',
            'timeouts': r'[Tt]imeout|timed? out|deadline exceeded',
            'connection_issues': r'[Cc]onnection.?(refused|reset|closed|failed)',
            'memory_pressure': r'[Mm]emory|OOM|heap|GC',
            'slow_operations': r'[Ss]low|performance|latency|took \d+ms',
            'retries': r'[Rr]etry|attempt|trying again',
            'degraded_service': r'[Dd]egraded|partial|fallback',
            'queue_buildup': r'[Qq]ueue|backlog|pending|waiting',
            'authentication': r'[Aa]uth|token|credential|permission',
            'data_issues': r'[Ii]nvalid|corrupt|missing|null|undefined'
        }
        
        # Add custom patterns if provided
        if custom_patterns:
            for i, pattern in enumerate(custom_patterns):
                default_patterns[f'custom_{i}'] = pattern
        
        lines = logs.split('\n')
        
        # Analyze each pattern
        for pattern_name, pattern_regex in default_patterns.items():
            matches = self._find_pattern_matches(lines, pattern_regex)
            if matches:
                patterns[pattern_name] = matches
        
        # Analyze error clustering
        patterns['error_clusters'] = self._find_error_clusters(lines)
        
        # Analyze trending issues
        patterns['trends'] = self._analyze_trends(lines)
        
        # Detect anomalies
        patterns['anomalies'] = self._detect_anomalies(lines)
        
        return patterns
    
    def _find_pattern_matches(self, lines: List[str], pattern: str) -> List[Dict]:
        """Find all matches for a pattern"""
        matches = []
        
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            
            for line_num, line in enumerate(lines, 1):
                if compiled_pattern.search(line):
                    matches.append({
                        'line_number': line_num,
                        'excerpt': line[:200],  # First 200 chars
                        'timestamp': self._extract_timestamp(line)
                    })
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
        
        return matches
    
    def _find_error_clusters(self, lines: List[str]) -> List[Dict]:
        """Find clusters of errors occurring close together"""
        clusters = []
        current_cluster = []
        cluster_threshold = 5  # Lines within this distance are considered clustered
        
        error_pattern = re.compile(r'ERROR|Exception|Failed|Critical', re.IGNORECASE)
        
        for i, line in enumerate(lines):
            if error_pattern.search(line):
                if current_cluster and i - current_cluster[-1]['line'] > cluster_threshold:
                    # Save current cluster and start new one
                    if len(current_cluster) >= 3:  # Minimum cluster size
                        clusters.append({
                            'start_line': current_cluster[0]['line'],
                            'end_line': current_cluster[-1]['line'],
                            'error_count': len(current_cluster),
                            'samples': current_cluster[:3]  # First 3 errors
                        })
                    current_cluster = []
                
                current_cluster.append({
                    'line': i,
                    'content': line[:200]
                })
        
        # Don't forget the last cluster
        if len(current_cluster) >= 3:
            clusters.append({
                'start_line': current_cluster[0]['line'],
                'end_line': current_cluster[-1]['line'],
                'error_count': len(current_cluster),
                'samples': current_cluster[:3]
            })
        
        return clusters
    
    def _analyze_trends(self, lines: List[str]) -> Dict:
        """Analyze trending patterns in logs"""
        trends = {
            'increasing_errors': False,
            'repeated_patterns': [],
            'error_velocity': 0,
            'common_terms': []
        }
        
        # Split lines into windows
        window_size = max(len(lines) // 10, 10)
        windows = [lines[i:i+window_size] for i in range(0, len(lines), window_size)]
        
        if len(windows) < 2:
            return trends
        
        # Count errors per window
        error_counts = []
        for window in windows:
            error_count = sum(1 for line in window 
                            if re.search(r'ERROR|Exception|Failed', line, re.IGNORECASE))
            error_counts.append(error_count)
        
        # Check if errors are increasing
        if len(error_counts) >= 3:
            recent_avg = sum(error_counts[-3:]) / 3
            earlier_avg = sum(error_counts[:-3]) / max(len(error_counts) - 3, 1)
            trends['increasing_errors'] = recent_avg > earlier_avg * 1.5
            trends['error_velocity'] = recent_avg - earlier_avg
        
        # Find repeated error messages
        error_messages = []
        for line in lines:
            if re.search(r'ERROR|Exception', line, re.IGNORECASE):
                # Extract message part
                msg_match = re.search(r'(ERROR|Exception)[:\s]+(.{20,100})', line)
                if msg_match:
                    error_messages.append(msg_match.group(2))
        
        if error_messages:
            msg_counter = Counter(error_messages)
            repeated = [(msg, count) for msg, count in msg_counter.items() if count >= 3]
            trends['repeated_patterns'] = sorted(repeated, key=lambda x: x[1], reverse=True)[:5]
        
        # Extract common terms (excluding common words)
        stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 
                     'was', 'were', 'in', 'to', 'for', 'of', 'with', 'by'}
        
        words = []
        for line in lines[-100:]:  # Last 100 lines
            words.extend(re.findall(r'\b[a-zA-Z]{4,}\b', line.lower()))
        
        word_counts = Counter(word for word in words if word not in stop_words)
        trends['common_terms'] = word_counts.most_common(10)
        
        return trends
    
    def _detect_anomalies(self, lines: List[str]) -> List[Dict]:
        """Detect anomalous patterns in logs"""
        anomalies = []
        
        # Detect sudden log volume changes
        if len(lines) > 100:
            line_lengths = [len(line) for line in lines]
            avg_length = sum(line_lengths) / len(line_lengths)
            
            for i, length in enumerate(line_lengths):
                if length > avg_length * 3:  # Lines 3x longer than average
                    anomalies.append({
                        'type': 'unusual_log_length',
                        'line_number': i + 1,
                        'description': f'Log line is {length} chars (avg: {avg_length:.0f})'
                    })
        
        # Detect unusual characters or encoding issues
        for i, line in enumerate(lines):
            if re.search(r'[\x00-\x1f\x7f-\x9f]', line):  # Control characters
                anomalies.append({
                    'type': 'encoding_issue',
                    'line_number': i + 1,
                    'description': 'Contains control characters'
                })
            
            # Detect potential log injection
            if re.search(r'<script|javascript:|onerror=|onclick=', line, re.IGNORECASE):
                anomalies.append({
                    'type': 'potential_injection',
                    'line_number': i + 1,
                    'description': 'Potential script injection detected'
                })
        
        # Detect rapid repeated lines (possible infinite loop)
        for i in range(len(lines) - 10):
            if lines[i] and all(lines[i] == lines[j] for j in range(i+1, min(i+5, len(lines)))):
                anomalies.append({
                    'type': 'repeated_lines',
                    'line_number': i + 1,
                    'description': 'Same line repeated multiple times'
                })
        
        return anomalies[:20]  # Limit to 20 anomalies
    
    def _extract_timestamp(self, line: str) -> str:
        """Extract timestamp from log line"""
        patterns = [
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        
        return ""