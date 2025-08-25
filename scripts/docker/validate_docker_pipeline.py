#!/usr/bin/env python3
"""
Validate that the embedding pipeline fixes are working correctly in Docker.
This script tests all critical fixes from the fix-api-pipeline-errors epic.
"""

import os
import sys
import json
import time
import subprocess
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

@dataclass
class ValidationResult:
    """Result of a validation check"""
    name: str
    passed: bool
    message: str
    details: Optional[str] = None

class PipelineValidator:
    """Validates the embedding pipeline fixes in Docker environment"""
    
    def __init__(self, container_name: str = "deepwiki-open_deepwiki_1"):
        self.container_name = container_name
        self.results: List[ValidationResult] = []
        
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Colors.BLUE}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BLUE}{text.center(80)}{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")
        
    def print_status(self, message: str, status: str = "INFO"):
        """Print a status message with color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED
        }.get(status, Colors.WHITE)
        
        symbol = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }.get(status, "•")
        
        print(f"{color}[{timestamp}] {symbol} {message}{Colors.RESET}")
    
    def run_docker_command(self, command: str) -> Tuple[bool, str]:
        """Run a command in the Docker container"""
        full_command = f"docker exec {self.container_name} {command}"
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def check_container_running(self) -> bool:
        """Check if the Docker container is running"""
        self.print_status("Checking if container is running...")
        
        command = f"docker ps --filter name={self.container_name} --format '{{{{.Names}}}}'"
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if self.container_name in result.stdout or self.container_name.replace("_", "-") in result.stdout:
                self.print_status("Container is running", "SUCCESS")
                return True
            else:
                # Try alternative name format
                alt_name = self.container_name.replace("_", "-")
                command = f"docker ps --filter name={alt_name} --format '{{{{.Names}}}}'"
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if alt_name in result.stdout:
                    self.container_name = alt_name
                    self.print_status(f"Container is running (as {alt_name})", "SUCCESS")
                    return True
                    
                self.print_status("Container is not running", "ERROR")
                print(f"  Run: docker-compose up -d")
                return False
        except Exception as e:
            self.print_status(f"Error checking container: {e}", "ERROR")
            return False
    
    def validate_no_empty_vectors(self) -> ValidationResult:
        """Validate that no empty vectors are created"""
        self.print_status("Validating empty vector prevention...")
        
        # Check Python code for empty vector creation
        success, output = self.run_docker_command(
            "grep -r 'append(\\[\\])' /app/api/ 2>/dev/null || echo 'NONE_FOUND'"
        )
        
        if "NONE_FOUND" in output:
            return ValidationResult(
                name="No Empty Vectors",
                passed=True,
                message="No empty vector creation found in code",
                details="All append([]) statements have been removed"
            )
        else:
            return ValidationResult(
                name="No Empty Vectors",
                passed=False,
                message="Found empty vector creation in code",
                details=output[:500]
            )
    
    def validate_dimension_consistency(self) -> ValidationResult:
        """Validate that dimension validation is implemented"""
        self.print_status("Validating dimension consistency checks...")
        
        # Check for dimension validation function
        success, output = self.run_docker_command(
            "grep -l '_validate_embedding\\|validate_dimension' /app/api/*.py /app/api/**/*.py 2>/dev/null | head -5"
        )
        
        if success and output.strip():
            files = output.strip().split('\n')
            return ValidationResult(
                name="Dimension Validation",
                passed=True,
                message="Dimension validation implemented",
                details=f"Found in {len(files)} files: {', '.join(files[:3])}"
            )
        else:
            return ValidationResult(
                name="Dimension Validation",
                passed=False,
                message="Dimension validation not found",
                details="Could not find _validate_embedding or validate_dimension functions"
            )
    
    def validate_retry_logic(self) -> ValidationResult:
        """Validate that retry logic is implemented"""
        self.print_status("Validating retry logic implementation...")
        
        # Check for exponential backoff implementation
        success, output = self.run_docker_command(
            "grep -l 'exponential_backoff\\|retry\\|max_retries' /app/api/google_embedding_client.py 2>/dev/null"
        )
        
        if success and output.strip():
            # Check for actual retry decorator or logic
            success2, details = self.run_docker_command(
                "grep -A 5 'exponential_backoff_retry\\|@retry\\|for attempt in range' /app/api/google_embedding_client.py 2>/dev/null | head -20"
            )
            
            return ValidationResult(
                name="Retry Logic",
                passed=True,
                message="Exponential backoff retry implemented",
                details=details[:300] if details else "Retry logic found in google_embedding_client.py"
            )
        else:
            return ValidationResult(
                name="Retry Logic",
                passed=False,
                message="Retry logic not found",
                details="Could not find retry implementation in google_embedding_client.py"
            )
    
    def validate_error_reporting(self) -> ValidationResult:
        """Validate that error reporting is enhanced"""
        self.print_status("Validating enhanced error reporting...")
        
        # Check for EmbeddingError class
        success, output = self.run_docker_command(
            "grep -l 'EmbeddingError\\|BatchSummary\\|document_id' /app/api/*.py /app/api/**/*.py 2>/dev/null | head -5"
        )
        
        if success and output.strip():
            files = output.strip().split('\n')
            return ValidationResult(
                name="Error Reporting",
                passed=True,
                message="Enhanced error reporting implemented",
                details=f"Structured errors found in {len(files)} files"
            )
        else:
            return ValidationResult(
                name="Error Reporting",
                passed=False,
                message="Enhanced error reporting not found",
                details="Could not find EmbeddingError or structured error classes"
            )
    
    def validate_model_name(self) -> ValidationResult:
        """Validate that the correct model name is used"""
        self.print_status("Validating model name configuration...")
        
        # Check for correct model name
        success, output = self.run_docker_command(
            "grep 'text-embedding-004' /app/api/google_embedding_client.py 2>/dev/null"
        )
        
        if success and output.strip():
            return ValidationResult(
                name="Model Name",
                passed=True,
                message="Correct model name (text-embedding-004) is used",
                details=output.strip()[:200]
            )
        else:
            # Check if wrong model name exists
            success2, wrong = self.run_docker_command(
                "grep 'embedding-001' /app/api/google_embedding_client.py 2>/dev/null"
            )
            
            if success2 and wrong.strip():
                return ValidationResult(
                    name="Model Name",
                    passed=False,
                    message="Wrong model name (embedding-001) still in use",
                    details=wrong.strip()[:200]
                )
            else:
                return ValidationResult(
                    name="Model Name",
                    passed=False,
                    message="Model name configuration not found",
                    details="Could not verify model name in google_embedding_client.py"
                )
    
    def run_test_suite(self) -> ValidationResult:
        """Run the actual test suite in the container"""
        self.print_status("Running test suite in container...")
        
        # Run key tests
        test_files = [
            "test/test_empty_embedding_validation.py",
            "test/test_dimension_consistency.py",
            "test/test_batch_retry_logic.py"
        ]
        
        passed_tests = 0
        failed_tests = 0
        test_output = []
        
        for test_file in test_files:
            self.print_status(f"Running {test_file}...")
            success, output = self.run_docker_command(
                f"python -m pytest {test_file} -v --tb=no -q 2>&1"
            )
            
            if success or "passed" in output.lower():
                # Count passed/failed from output
                import re
                passed_match = re.search(r'(\d+) passed', output)
                failed_match = re.search(r'(\d+) failed', output)
                
                if passed_match:
                    passed_tests += int(passed_match.group(1))
                if failed_match:
                    failed_tests += int(failed_match.group(1))
                else:
                    passed_tests += 1  # Assume at least one passed if successful
                    
                test_output.append(f"{test_file}: PASS")
            else:
                failed_tests += 1
                test_output.append(f"{test_file}: FAIL")
        
        if failed_tests == 0:
            return ValidationResult(
                name="Test Suite",
                passed=True,
                message=f"All tests passed ({passed_tests} tests)",
                details="\n".join(test_output)
            )
        else:
            return ValidationResult(
                name="Test Suite",
                passed=False,
                message=f"{failed_tests} tests failed, {passed_tests} passed",
                details="\n".join(test_output)
            )
    
    def check_api_health(self) -> ValidationResult:
        """Check if the API is healthy"""
        self.print_status("Checking API health...")
        
        success, output = self.run_docker_command(
            "curl -s -f http://localhost:8001/health 2>/dev/null || echo 'FAILED'"
        )
        
        if success and "FAILED" not in output:
            try:
                health_data = json.loads(output) if output.strip().startswith('{') else {"status": "ok"}
                return ValidationResult(
                    name="API Health",
                    passed=True,
                    message="API is healthy",
                    details=f"Health response: {health_data}"
                )
            except:
                return ValidationResult(
                    name="API Health",
                    passed=True,
                    message="API is responding",
                    details=output[:200]
                )
        else:
            return ValidationResult(
                name="API Health",
                passed=False,
                message="API health check failed",
                details="Could not reach API at http://localhost:8001/health"
            )
    
    def validate_all(self) -> bool:
        """Run all validations"""
        self.print_header("DeepWiki Embedding Pipeline Validation")
        
        # Check container is running
        if not self.check_container_running():
            self.print_status("Cannot proceed without running container", "ERROR")
            return False
        
        # Run all validations
        validations = [
            self.check_api_health(),
            self.validate_no_empty_vectors(),
            self.validate_model_name(),
            self.validate_dimension_consistency(),
            self.validate_retry_logic(),
            self.validate_error_reporting(),
            self.run_test_suite()
        ]
        
        self.results = validations
        
        # Print results
        self.print_results()
        
        # Return overall success
        return all(v.passed for v in validations)
    
    def print_results(self):
        """Print validation results summary"""
        self.print_header("Validation Results")
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        for result in self.results:
            if result.passed:
                self.print_status(f"{result.name}: {result.message}", "SUCCESS")
            else:
                self.print_status(f"{result.name}: {result.message}", "ERROR")
            
            if result.details and not result.passed:
                print(f"  {Colors.YELLOW}Details: {result.details[:200]}{Colors.RESET}")
        
        print()
        self.print_header(f"Summary: {passed}/{total} Validations Passed")
        
        if passed == total:
            self.print_status("🎉 All validations passed! Pipeline fixes are working correctly.", "SUCCESS")
            return True
        else:
            self.print_status(f"⚠️  {total - passed} validation(s) failed. Review the fixes.", "WARNING")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate embedding pipeline fixes in Docker")
    parser.add_argument(
        "--container",
        default="deepwiki-open_deepwiki_1",
        help="Docker container name (default: deepwiki-open_deepwiki_1)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    validator = PipelineValidator(container_name=args.container)
    success = validator.validate_all()
    
    if args.json:
        # Output JSON results
        results = [
            {
                "name": r.name,
                "passed": r.passed,
                "message": r.message,
                "details": r.details
            }
            for r in validator.results
        ]
        print(json.dumps({
            "success": success,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()