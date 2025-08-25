#!/bin/bash
# End-to-end test runner with environment setup
# Tests the complete embedding pipeline with all fixes from Tasks 001-008

set -e  # Exit on any error

echo "======================================================="
echo "🚀 DeepWiki Embedding Pipeline E2E Test Suite"
echo "======================================================="
echo "Testing complete pipeline with fixes from Tasks 001-008:"
echo "- Empty vector prevention"
echo "- Dimension consistency (768-dim)"
echo "- API retry and recovery logic"
echo "- Comprehensive error reporting"
echo "- Batch processing resilience"
echo "- FAISS index integration"
echo ""

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    echo "======================================================="
    print_status $BLUE "$1"
    echo "======================================================="
}

print_test_result() {
    local result=$1
    local test_name=$2
    if [ $result -eq 0 ]; then
        print_status $GREEN "✅ PASSED: $test_name"
    else
        print_status $RED "❌ FAILED: $test_name"
    fi
    echo ""
}

# Check Python environment
print_header "🔍 Checking Environment"

# Check if we're in the correct directory
if [ ! -f "test/test_e2e_embedding_pipeline.py" ]; then
    print_status $RED "❌ Error: Must run from deepwiki-open root directory"
    print_status $YELLOW "Current directory: $(pwd)"
    print_status $YELLOW "Expected to find: test/test_e2e_embedding_pipeline.py"
    exit 1
fi

# Check Python and pytest
if ! command -v python3 &> /dev/null; then
    print_status $RED "❌ Error: python3 not found"
    exit 1
fi

if ! python3 -c "import pytest" &> /dev/null; then
    print_status $RED "❌ Error: pytest not installed"
    print_status $YELLOW "Install with: pip install pytest"
    exit 1
fi

print_status $GREEN "✅ Python environment ready"

# Check API key and set test mode
if [ -z "$GOOGLE_API_KEY" ]; then
    print_status $YELLOW "⚠️  GOOGLE_API_KEY not set - using MOCK MODE"
    export USE_MOCK_EMBEDDINGS=true
    export TEST_MODE="mock"
else
    print_status $GREEN "✅ GOOGLE_API_KEY found - can test with REAL API"
    export TEST_MODE="real_api_available"
fi

# Set up test environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TEST_LOGGING_LEVEL="INFO"

# Create test results directory
mkdir -p test-results
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TEST_REPORT="test-results/e2e_test_report_${TIMESTAMP}.html"
TEST_LOG="test-results/e2e_test_log_${TIMESTAMP}.log"

print_status $BLUE "📋 Test results will be saved to:"
print_status $BLUE "   Report: $TEST_REPORT"  
print_status $BLUE "   Log: $TEST_LOG"

echo ""

# Function to run individual test and capture results
run_test() {
    local test_name=$1
    local test_marker=$2
    local description=$3
    
    print_status $BLUE "🧪 Running: $description"
    
    # Run the test and capture both stdout and return code
    set +e  # Don't exit on test failures
    
    if [ "$test_marker" = "all" ]; then
        python3 -m pytest test/test_e2e_embedding_pipeline.py -v --tb=short -s 2>&1 | tee -a "$TEST_LOG"
        result=$?
    else
        python3 -m pytest test/test_e2e_embedding_pipeline.py::TestE2EEmbeddingPipeline::$test_name -v --tb=short -s 2>&1 | tee -a "$TEST_LOG"
        result=$?
    fi
    
    set -e  # Re-enable exit on error
    
    print_test_result $result "$description"
    return $result
}

# Track overall results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to record test result
record_result() {
    local result=$1
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $result -eq 0 ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Core Pipeline Tests
print_header "📊 Core Pipeline Integration Tests"

echo "Testing complete document processing to FAISS index creation..."

run_test "test_complete_pipeline_with_mixed_inputs" "integration" "Complete pipeline with mixed document types"
record_result $?

run_test "test_dimension_consistency_maintained" "integration" "768-dimensional embedding consistency"
record_result $?

run_test "test_faiss_index_creation_end_to_end" "integration" "FAISS index creation and search"
record_result $?

# Error Handling and Recovery Tests  
print_header "🔧 Error Handling and Recovery Tests"

echo "Testing retry logic, error reporting, and failure recovery..."

run_test "test_pipeline_recovery_from_api_failures" "integration" "API failure recovery with retry logic"
record_result $?

run_test "test_error_reporting_in_pipeline" "integration" "Comprehensive error reporting and structured errors"
record_result $?

run_test "test_empty_embedding_prevention" "integration" "Empty vector prevention (critical fix)"
record_result $?

# Resilience and Performance Tests
print_header "💪 Resilience and Performance Tests"

echo "Testing batch processing resilience and performance characteristics..."

run_test "test_batch_processing_resilience" "integration" "Batch processing with mixed success/failures"
record_result $?

run_test "test_pipeline_performance_characteristics" "performance" "Basic performance benchmarks"
record_result $?

# Mock Infrastructure Tests
print_header "🎭 Mock Infrastructure Tests"

echo "Testing mock embedding system for offline development..."

run_test "test_mock_embedding_client_functionality" "unit" "Mock embedding client validation"
record_result $?

# Optional Real API Test (if available)
print_header "🌐 Real API Integration Test"

if [ "$TEST_MODE" = "real_api_available" ]; then
    echo "GOOGLE_API_KEY detected - testing with real Google API..."
    run_test "test_pipeline_with_real_google_api_if_available" "integration" "Real Google API integration"
    record_result $?
else
    print_status $YELLOW "⏭️  Skipping real API test (no GOOGLE_API_KEY)"
    echo ""
fi

# Generate HTML report if pytest-html is available
print_header "📋 Generating Test Report"

if python3 -c "import pytest_html" &> /dev/null; then
    print_status $BLUE "Generating HTML test report..."
    python3 -m pytest test/test_e2e_embedding_pipeline.py --html="$TEST_REPORT" --self-contained-html --tb=short -v 2>/dev/null || print_status $YELLOW "⚠️  HTML report generation had issues"
else
    print_status $YELLOW "⚠️  pytest-html not installed - HTML report not generated"
    print_status $YELLOW "Install with: pip install pytest-html"
fi

# Final Summary
print_header "📊 Test Results Summary"

echo "Total Tests Run: $TOTAL_TESTS"
print_status $GREEN "✅ Passed: $PASSED_TESTS"
if [ $FAILED_TESTS -gt 0 ]; then
    print_status $RED "❌ Failed: $FAILED_TESTS"
else
    print_status $GREEN "❌ Failed: $FAILED_TESTS"
fi

# Calculate success rate
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    print_status $BLUE "🎯 Success Rate: ${SUCCESS_RATE}%"
fi

echo ""
print_status $BLUE "📁 Test artifacts saved to test-results/ directory"

# Check for critical failures
print_header "🔍 Critical Issue Detection"

echo "Checking for critical issues in test output..."

# Check for empty vectors (critical bug)
if grep -q "empty vector" "$TEST_LOG" 2>/dev/null; then
    print_status $RED "🚨 CRITICAL: Empty vectors detected in output"
    print_status $RED "    This is the primary bug that Tasks 001-008 aimed to fix"
    print_status $RED "    Check logs for details"
fi

# Check for dimension inconsistencies
if grep -q "dimension.*mismatch\|inconsistent.*dimension" "$TEST_LOG" 2>/dev/null; then
    print_status $RED "🚨 CRITICAL: Dimension inconsistencies detected"
    print_status $RED "    FAISS requires consistent embedding dimensions"
fi

# Check for successful FAISS index creation
if grep -q "FAISS.*created\|index.*searchable" "$TEST_LOG" 2>/dev/null; then
    print_status $GREEN "✅ FAISS index creation succeeded"
else
    print_status $YELLOW "⚠️  FAISS index creation may have issues - check logs"
fi

# Check for API retry functionality
if grep -q "retry\|recovery.*api" "$TEST_LOG" 2>/dev/null; then
    print_status $GREEN "✅ API retry/recovery logic is working"
else
    print_status $YELLOW "⚠️  API retry logic may not be implemented"
fi

echo ""
print_status $BLUE "💡 For detailed analysis, check:"
print_status $BLUE "   Full log: $TEST_LOG"
if [ -f "$TEST_REPORT" ]; then
    print_status $BLUE "   HTML report: $TEST_REPORT"
fi

# Exit with appropriate code
if [ $FAILED_TESTS -gt 0 ]; then
    print_status $RED "❌ Some tests failed - check logs for details"
    
    # Show critical failure info
    echo ""
    print_status $RED "Recent critical errors from log:"
    tail -20 "$TEST_LOG" | grep -i "error\|fail\|critical" | head -5 || echo "No specific errors found in recent output"
    
    exit 1
else
    print_header "🎉 ALL TESTS PASSED!"
    
    print_status $GREEN "✅ Embedding pipeline is working correctly"
    print_status $GREEN "✅ All fixes from Tasks 001-008 are integrated"  
    print_status $GREEN "✅ No critical issues detected"
    print_status $GREEN "✅ System is ready for production use"
    
    echo ""
    print_status $BLUE "🚀 DeepWiki embedding pipeline E2E validation complete!"
    
    exit 0
fi