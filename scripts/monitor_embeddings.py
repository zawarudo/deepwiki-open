#!/usr/bin/env python3
"""
Continuous monitoring script for embedding health and empty vector detection.

This script can:
- Run continuously to detect empty vectors
- Log warnings when issues are detected
- Provide real-time embedding health metrics
- Can be integrated into monitoring systems
- Generate alerts for critical issues

Usage:
    python scripts/monitor_embeddings.py --interval 60
    python scripts/monitor_embeddings.py --daemon
    python scripts/monitor_embeddings.py --alert-webhook https://hooks.slack.com/...
    python scripts/monitor_embeddings.py --help
"""

import argparse
import sys
import asyncio
import logging
import json
import time
import signal
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# Add the api directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

try:
    from google_embedding_client import GoogleEmbeddingClient
    from adalflow.core.types import ModelType
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HealthMetrics:
    """Health metrics for embedding monitoring."""
    timestamp: str
    total_tests: int = 0
    successful_embeddings: int = 0
    empty_vectors: int = 0
    wrong_dimensions: int = 0
    api_failures: int = 0
    avg_response_time: float = 0.0
    health_score: float = 0.0
    status: str = "UNKNOWN"
    
    def calculate_health_score(self):
        """Calculate overall health score (0-100)."""
        if self.total_tests == 0:
            self.health_score = 0.0
            self.status = "NO_DATA"
            return
        
        # Weight different metrics
        success_weight = 50.0  # 50% weight for successful embeddings
        empty_penalty = 40.0   # 40% penalty for empty vectors (critical)
        dimension_penalty = 5.0  # 5% penalty for wrong dimensions
        api_penalty = 5.0      # 5% penalty for API failures
        
        success_score = (self.successful_embeddings / self.total_tests) * success_weight
        empty_score = max(0, empty_penalty - (self.empty_vectors / self.total_tests) * empty_penalty)
        dimension_score = max(0, dimension_penalty - (self.wrong_dimensions / self.total_tests) * dimension_penalty)
        api_score = max(0, api_penalty - (self.api_failures / self.total_tests) * api_penalty)
        
        self.health_score = success_score + empty_score + dimension_score + api_score
        
        # Determine status
        if self.empty_vectors > 0:
            self.status = "CRITICAL"  # Any empty vectors are critical
        elif self.health_score >= 95:
            self.status = "HEALTHY"
        elif self.health_score >= 80:
            self.status = "WARNING"
        else:
            self.status = "UNHEALTHY"


class EmbeddingMonitor:
    """Continuous monitor for embedding health and quality."""
    
    def __init__(self, 
                 interval: int = 300, 
                 test_batch_size: int = 3,
                 alert_webhook: Optional[str] = None):
        self.interval = interval
        self.test_batch_size = test_batch_size
        self.alert_webhook = alert_webhook
        self.embedding_client = GoogleEmbeddingClient()
        self.expected_dimension = 768
        
        # Monitoring state
        self.running = False
        self.metrics_history: List[HealthMetrics] = []
        self.last_alert_time = None
        self.alert_cooldown = timedelta(minutes=15)  # Prevent alert spam
        
        # Test texts for monitoring
        self.test_texts = [
            "Monitoring test document for embedding health validation.",
            "This is a sample text used for continuous embedding quality checks.",
            "System health verification text with various content types: numbers 123, symbols !@#$%"
        ]
        
        # Setup graceful shutdown
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def test_embedding_health(self) -> HealthMetrics:
        """Test embedding generation and return health metrics."""
        metrics = HealthMetrics(
            timestamp=datetime.now().isoformat(),
            total_tests=len(self.test_texts)
        )
        
        start_time = time.time()
        
        try:
            # Generate embeddings for test texts
            api_kwargs = self.embedding_client.convert_inputs_to_api_kwargs(
                input=self.test_texts,
                model_type=ModelType.EMBEDDER
            )
            
            output = self.embedding_client.call(api_kwargs, ModelType.EMBEDDER)
            
            metrics.avg_response_time = time.time() - start_time
            
            if output.error:
                logger.warning(f"API error during monitoring: {output.error}")
                metrics.api_failures = metrics.total_tests
                metrics.calculate_health_score()
                return metrics
            
            # Analyze each embedding
            for i, embedding_obj in enumerate(output.data):
                embedding = embedding_obj.embedding
                
                # Check for empty vectors
                if not embedding or len(embedding) == 0:
                    metrics.empty_vectors += 1
                    logger.error(f"Empty vector detected in monitoring test {i}")
                    continue
                
                # Check dimensions
                if len(embedding) != self.expected_dimension:
                    metrics.wrong_dimensions += 1
                    logger.warning(f"Wrong dimension detected in test {i}: {len(embedding)}")
                    continue
                
                # Check for invalid values
                try:
                    if not all(isinstance(x, (int, float)) for x in embedding):
                        metrics.api_failures += 1
                        continue
                    if any(x != x or abs(x) == float('inf') for x in embedding):
                        metrics.api_failures += 1
                        continue
                except Exception:
                    metrics.api_failures += 1
                    continue
                
                metrics.successful_embeddings += 1
            
        except Exception as e:
            logger.error(f"Error during health test: {e}")
            metrics.api_failures = metrics.total_tests
        
        metrics.calculate_health_score()
        return metrics
    
    async def send_alert(self, metrics: HealthMetrics, alert_message: str):
        """Send alert via webhook or other notification system."""
        if not self.alert_webhook:
            logger.warning(f"Alert would be sent: {alert_message}")
            return
        
        # Check cooldown
        if (self.last_alert_time and 
            datetime.now() - self.last_alert_time < self.alert_cooldown):
            logger.debug("Alert skipped due to cooldown")
            return
        
        try:
            import requests
            
            alert_data = {
                "text": alert_message,
                "timestamp": metrics.timestamp,
                "health_score": metrics.health_score,
                "status": metrics.status,
                "details": {
                    "empty_vectors": metrics.empty_vectors,
                    "wrong_dimensions": metrics.wrong_dimensions,
                    "api_failures": metrics.api_failures,
                    "successful_embeddings": metrics.successful_embeddings
                }
            }
            
            response = requests.post(
                self.alert_webhook,
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Alert sent successfully")
                self.last_alert_time = datetime.now()
            else:
                logger.error(f"Failed to send alert: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def save_metrics(self, metrics: HealthMetrics, metrics_file: str = "embedding_metrics.jsonl"):
        """Save metrics to file for historical analysis."""
        try:
            with open(metrics_file, 'a') as f:
                f.write(json.dumps(asdict(metrics)) + '\n')
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def print_metrics_report(self, metrics: HealthMetrics):
        """Print current metrics report."""
        print(f"\n{'='*50}")
        print(f"EMBEDDING HEALTH REPORT - {metrics.timestamp}")
        print(f"{'='*50}")
        print(f"Status: {metrics.status}")
        print(f"Health Score: {metrics.health_score:.1f}/100.0")
        print(f"Response Time: {metrics.avg_response_time:.2f}s")
        print(f"\nDetails:")
        print(f"  Total Tests: {metrics.total_tests}")
        print(f"  Successful: {metrics.successful_embeddings}")
        print(f"  Empty Vectors: {metrics.empty_vectors}")
        print(f"  Wrong Dimensions: {metrics.wrong_dimensions}")
        print(f"  API Failures: {metrics.api_failures}")
        
        # Status indicators
        if metrics.status == "CRITICAL":
            print("🚨 CRITICAL: Empty vectors detected! System compromised!")
        elif metrics.status == "UNHEALTHY":
            print("❌ UNHEALTHY: Multiple issues detected")
        elif metrics.status == "WARNING":
            print("⚠️  WARNING: Some issues detected")
        elif metrics.status == "HEALTHY":
            print("✅ HEALTHY: All systems operational")
        else:
            print("❓ UNKNOWN: No data or unclear status")
    
    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends in metrics history."""
        if len(self.metrics_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent_metrics = self.metrics_history[-5:]  # Last 5 measurements
        
        # Calculate trend in health score
        health_scores = [m.health_score for m in recent_metrics]
        if len(health_scores) >= 2:
            trend_direction = "improving" if health_scores[-1] > health_scores[0] else "degrading"
            avg_health = sum(health_scores) / len(health_scores)
        else:
            trend_direction = "stable"
            avg_health = health_scores[0] if health_scores else 0
        
        # Count recent issues
        recent_empty_vectors = sum(m.empty_vectors for m in recent_metrics)
        recent_api_failures = sum(m.api_failures for m in recent_metrics)
        
        return {
            "trend": trend_direction,
            "avg_health_score": avg_health,
            "recent_empty_vectors": recent_empty_vectors,
            "recent_api_failures": recent_api_failures,
            "measurements_count": len(recent_metrics)
        }
    
    async def run_continuous_monitoring(self, 
                                      save_metrics: bool = True,
                                      print_reports: bool = True) -> None:
        """Run continuous monitoring loop."""
        logger.info(f"Starting continuous embedding monitoring (interval: {self.interval}s)")
        self.running = True
        
        while self.running:
            try:
                # Run health test
                logger.debug("Running embedding health test...")
                metrics = await self.test_embedding_health()
                
                # Store metrics
                self.metrics_history.append(metrics)
                
                # Keep only last 100 measurements
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-100:]
                
                # Save metrics to file
                if save_metrics:
                    self.save_metrics(metrics)
                
                # Print report if requested
                if print_reports:
                    self.print_metrics_report(metrics)
                
                # Check for critical issues and send alerts
                if metrics.status == "CRITICAL":
                    alert_msg = (f"CRITICAL ALERT: Empty vectors detected in embedding system! "
                               f"Health Score: {metrics.health_score:.1f}/100")
                    await self.send_alert(metrics, alert_msg)
                elif metrics.status == "UNHEALTHY":
                    alert_msg = (f"UNHEALTHY: Embedding system degraded. "
                               f"Health Score: {metrics.health_score:.1f}/100")
                    await self.send_alert(metrics, alert_msg)
                
                # Analyze trends
                trends = self.analyze_trends()
                if trends.get("recent_empty_vectors", 0) > 0:
                    logger.warning(f"Trend Alert: {trends['recent_empty_vectors']} empty vectors in recent measurements")
                
                # Wait for next check
                if self.running:
                    await asyncio.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                # Continue monitoring despite errors
                if self.running:
                    await asyncio.sleep(min(60, self.interval))  # Shorter wait on error
        
        logger.info("Monitoring stopped")
    
    async def run_single_check(self) -> HealthMetrics:
        """Run a single health check and return metrics."""
        return await self.test_embedding_health()


async def main():
    """Main function for embedding monitoring."""
    parser = argparse.ArgumentParser(
        description='Monitor embedding generation health and detect issues'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Monitoring interval in seconds (default: 300)'
    )
    parser.add_argument(
        '--single-check',
        action='store_true',
        help='Run a single health check instead of continuous monitoring'
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon (suppress output)'
    )
    parser.add_argument(
        '--alert-webhook',
        type=str,
        help='Webhook URL for sending alerts'
    )
    parser.add_argument(
        '--metrics-file',
        type=str,
        default='embedding_metrics.jsonl',
        help='File to save metrics (default: embedding_metrics.jsonl)'
    )
    parser.add_argument(
        '--test-batch-size',
        type=int,
        default=3,
        help='Number of test texts per health check (default: 3)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.daemon:
        logging.getLogger().setLevel(logging.WARNING)
    
    monitor = EmbeddingMonitor(
        interval=args.interval,
        test_batch_size=args.test_batch_size,
        alert_webhook=args.alert_webhook
    )
    
    try:
        if args.single_check:
            # Single health check
            logger.info("Running single embedding health check...")
            metrics = await monitor.run_single_check()
            
            if not args.daemon:
                monitor.print_metrics_report(metrics)
            
            # Save metrics
            monitor.save_metrics(metrics, args.metrics_file)
            
            # Return exit code based on health
            if metrics.status == "CRITICAL":
                return 2  # Critical issues
            elif metrics.status in ["UNHEALTHY", "WARNING"]:
                return 1  # Non-critical issues
            else:
                return 0  # Healthy
        else:
            # Continuous monitoring
            await monitor.run_continuous_monitoring(
                save_metrics=True,
                print_reports=not args.daemon
            )
            return 0
            
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user.")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error in monitoring: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))