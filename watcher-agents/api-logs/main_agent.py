#!/usr/bin/env python3
"""
API Log Monitoring Agent
Continuously monitors API logs for early error signs and generates analysis reports
"""

import os
import sys
import time
import json
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from collections import defaultdict, deque

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from analyzers.error_detector import ErrorDetector
from analyzers.pattern_analyzer import PatternAnalyzer
from analyzers.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APILogMonitor:
    """Main monitoring agent that orchestrates log analysis"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.error_detector = ErrorDetector()
        self.pattern_analyzer = PatternAnalyzer()
        self.report_generator = ReportGenerator()
        
        # State management
        self.state_dir = Path(__file__).parent / "state"
        self.state_dir.mkdir(exist_ok=True)
        self.last_check_file = self.state_dir / "last_check.json"
        self.error_history_file = self.state_dir / "error_history.json"
        
        # Error tracking
        self.error_history = deque(maxlen=100)  # Keep last 100 error events
        self.error_patterns = defaultdict(int)  # Track error pattern frequencies
        self.last_report_time = None
        
        self._load_state()
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "check_interval": 30,  # seconds between checks
            "log_lines": 500,      # number of log lines to analyze
            "report_threshold": 3,  # errors before generating report
            "report_cooldown": 300, # seconds between reports
            "docker_compose_file": "docker-compose.dev.yml",
            "container_name": "api",
            "early_warning_patterns": [
                r"[Ww]arning.*error",
                r"[Ff]ailed.*retry",
                r"[Tt]imeout",
                r"[Rr]ate.?limit",
                r"[Cc]onnection.?(refused|reset|closed)",
                r"4\d{2}\s+(error|Error)",  # 4xx errors
                r"5\d{2}\s+(error|Error)",  # 5xx errors
                r"[Ee]xception",
                r"[Tt]raceback",
                r"[Mm]emory.*error",
                r"[Dd]atabase.*error"
            ]
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _load_state(self):
        """Load previous state from disk"""
        if self.last_check_file.exists():
            with open(self.last_check_file, 'r') as f:
                state = json.load(f)
                self.last_report_time = state.get('last_report_time')
                if self.last_report_time:
                    self.last_report_time = datetime.fromisoformat(self.last_report_time)
        
        if self.error_history_file.exists():
            with open(self.error_history_file, 'r') as f:
                history = json.load(f)
                self.error_history = deque(history.get('errors', []), maxlen=100)
                self.error_patterns = defaultdict(int, history.get('patterns', {}))
    
    def _save_state(self):
        """Save current state to disk"""
        state = {
            'last_report_time': self.last_report_time.isoformat() if self.last_report_time else None,
            'last_check': datetime.now().isoformat()
        }
        with open(self.last_check_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        history = {
            'errors': list(self.error_history),
            'patterns': dict(self.error_patterns)
        }
        with open(self.error_history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def fetch_logs(self) -> str:
        """Fetch recent logs from Docker container"""
        try:
            # Change to project root directory (2 levels up from this script)
            project_root = Path(__file__).parent.parent.parent
            cmd = [
                "docker-compose", "-f", self.config['docker_compose_file'],
                "logs", "--tail", str(self.config['log_lines']),
                self.config['container_name']
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            return result.stdout
        except Exception as e:
            logger.error(f"Failed to fetch logs: {e}")
            return ""
    
    def analyze_logs(self, logs: str) -> Dict:
        """Analyze logs for errors and patterns"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'errors': [],
            'warnings': [],
            'patterns': {},
            'severity': 'normal',
            'early_signs': [],
            'recommendations': []
        }
        
        # Detect errors and warnings
        errors = self.error_detector.detect_errors(logs)
        warnings = self.error_detector.detect_warnings(logs)
        
        analysis['errors'] = errors
        analysis['warnings'] = warnings
        
        # Analyze patterns
        patterns = self.pattern_analyzer.analyze_patterns(logs, self.config['early_warning_patterns'])
        analysis['patterns'] = patterns
        
        # Check for early warning signs
        for pattern_name, matches in patterns.items():
            if pattern_name not in ['error_clusters', 'trends', 'anomalies'] and isinstance(matches, list) and len(matches) > 0:
                analysis['early_signs'].append({
                    'pattern': pattern_name,
                    'count': len(matches),
                    'first_occurrence': matches[0] if matches else None
                })
        
        # Determine severity
        if len(errors) > 10:
            analysis['severity'] = 'critical'
        elif len(errors) > 5:
            analysis['severity'] = 'high'
        elif len(errors) > 0 or len(warnings) > 5:
            analysis['severity'] = 'medium'
        elif len(warnings) > 0 or len(analysis['early_signs']) > 0:
            analysis['severity'] = 'low'
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        # Update history
        self._update_history(analysis)
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if 'timeout' in str(analysis).lower():
            recommendations.append("Consider increasing timeout values or optimizing slow operations")
        
        if 'rate limit' in str(analysis).lower():
            recommendations.append("Implement request throttling or increase API rate limits")
        
        if 'connection refused' in str(analysis).lower():
            recommendations.append("Check if dependent services are running and accessible")
        
        if '500' in str(analysis.get('errors', [])):
            recommendations.append("Internal server errors detected - check application logs for details")
        
        if analysis['severity'] in ['high', 'critical']:
            recommendations.append("Immediate attention required - multiple errors detected")
        
        # Pattern-based recommendations
        for sign in analysis.get('early_signs', []):
            if sign['count'] > 5:
                recommendations.append(f"Pattern '{sign['pattern']}' occurring frequently ({sign['count']} times)")
        
        return recommendations
    
    def _update_history(self, analysis: Dict):
        """Update error history and pattern tracking"""
        if analysis['errors'] or analysis['warnings']:
            self.error_history.append({
                'timestamp': analysis['timestamp'],
                'error_count': len(analysis['errors']),
                'warning_count': len(analysis['warnings']),
                'severity': analysis['severity']
            })
        
        for pattern_name in analysis.get('patterns', {}):
            self.error_patterns[pattern_name] += 1
    
    def should_generate_report(self, analysis: Dict) -> bool:
        """Determine if a report should be generated"""
        # Check severity
        if analysis['severity'] in ['high', 'critical']:
            return True
        
        # Check error threshold
        recent_errors = sum(1 for event in self.error_history 
                          if event.get('error_count', 0) > 0)
        if recent_errors >= self.config['report_threshold']:
            # Check cooldown
            if self.last_report_time:
                time_since_report = datetime.now() - self.last_report_time
                if time_since_report.total_seconds() < self.config['report_cooldown']:
                    return False
            return True
        
        return False
    
    def generate_report(self, analysis: Dict) -> str:
        """Generate human-readable report"""
        report = self.report_generator.generate(
            analysis,
            self.error_history,
            self.error_patterns
        )
        
        # Save report
        report_dir = Path(__file__).parent / "reports"
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"api_log_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        self.last_report_time = datetime.now()
        logger.info(f"Report generated: {report_file}")
        
        return report
    
    def run_once(self) -> Optional[str]:
        """Run a single monitoring cycle"""
        logger.info("Starting monitoring cycle...")
        
        # Fetch logs
        logs = self.fetch_logs()
        if not logs:
            logger.warning("No logs fetched")
            return None
        
        # Analyze logs
        analysis = self.analyze_logs(logs)
        
        logger.info(f"Analysis complete - Severity: {analysis['severity']}, "
                   f"Errors: {len(analysis['errors'])}, "
                   f"Warnings: {len(analysis['warnings'])}")
        
        # Generate report if needed
        report = None
        if self.should_generate_report(analysis):
            report = self.generate_report(analysis)
            print("\n" + "="*80)
            print("📊 API LOG ANALYSIS REPORT")
            print("="*80)
            print(report)
            print("="*80 + "\n")
        
        # Save state
        self._save_state()
        
        return report
    
    def run_continuous(self):
        """Run continuous monitoring loop"""
        logger.info(f"Starting continuous monitoring (interval: {self.config['check_interval']}s)")
        
        while True:
            try:
                self.run_once()
                time.sleep(self.config['check_interval'])
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config['check_interval'])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="API Log Monitoring Agent")
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuous')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    monitor = APILogMonitor(config_path=args.config)
    
    if args.once:
        monitor.run_once()
    else:
        monitor.run_continuous()