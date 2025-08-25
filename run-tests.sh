#!/bin/bash

# =============================================================================
# DeepWiki Test Runner - Main entry point for testing
# =============================================================================
# This script provides a convenient interface to run various types of tests
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to print colored messages
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Show usage
show_usage() {
    echo -e "${BLUE}DeepWiki Test Runner${NC}"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  all          Run all tests"
    echo "  unit         Run unit tests only"
    echo "  integration  Run integration tests only"
    echo "  embeddings   Run embedding pipeline tests"
    echo "  docker       Run tests in Docker container"
    echo "  coverage     Run tests with coverage report"
    echo "  quick        Run quick smoke tests"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 all               # Run all tests"
    echo "  $0 unit              # Run unit tests only"
    echo "  $0 docker            # Run tests in Docker"
    echo "  $0 coverage          # Generate coverage report"
}

# Check if pytest is installed
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest is not installed. Installing..."
        pip install pytest pytest-cov
    fi
}

# Run all tests
run_all_tests() {
    print_info "Running all tests..."
    pytest test/ -v
}

# Run unit tests
run_unit_tests() {
    print_info "Running unit tests..."
    pytest test/unit/ -v
}

# Run integration tests
run_integration_tests() {
    print_info "Running integration tests..."
    pytest test/integration/ -v
}

# Run embedding tests
run_embedding_tests() {
    print_info "Running embedding pipeline tests..."
    pytest test/embeddings/ -v
}

# Run tests in Docker
run_docker_tests() {
    print_info "Running tests in Docker..."
    if [ -f "./docker/scripts/test-pipeline.sh" ]; then
        # Make sure the script is executable
        chmod +x ./docker/scripts/test-pipeline.sh
        ./docker/scripts/test-pipeline.sh
    else
        print_error "Docker test script not found!"
        print_info "Try: docker-compose exec -e PYTHONPATH=/app deepwiki pytest test/"
    fi
}

# Run tests with coverage
run_coverage_tests() {
    print_info "Running tests with coverage report..."
    pytest test/ --cov=api --cov-report=html --cov-report=term
    print_success "Coverage report generated in htmlcov/index.html"
}

# Run quick smoke tests
run_quick_tests() {
    print_info "Running quick smoke tests..."
    # Run a subset of critical tests
    pytest test/unit/test_lang_config.py test/unit/test_extract_repo_name.py -v
    print_info "Quick tests completed. Run './run-tests.sh all' for full test suite."
}

# Main script logic
main() {
    case "${1:-help}" in
        all)
            check_pytest
            run_all_tests
            ;;
        unit)
            check_pytest
            run_unit_tests
            ;;
        integration)
            check_pytest
            run_integration_tests
            ;;
        embeddings|embedding)
            check_pytest
            run_embedding_tests
            ;;
        docker)
            run_docker_tests
            ;;
        coverage|cov)
            check_pytest
            run_coverage_tests
            ;;
        quick|smoke)
            check_pytest
            run_quick_tests
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown option: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
    
    # Show summary
    if [ $? -eq 0 ]; then
        print_success "Tests completed successfully!"
    else
        print_error "Some tests failed. Check output above for details."
        exit 1
    fi
}

# Run main function
main "$@"