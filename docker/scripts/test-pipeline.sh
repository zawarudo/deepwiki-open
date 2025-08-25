#!/bin/bash

# =============================================================================
# DeepWiki Embedding Pipeline - Docker Test Suite
# =============================================================================
# This script rebuilds and tests the Docker container with all embedding fixes
# from the fix-api-pipeline-errors epic
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}           DeepWiki Embedding Pipeline - Docker Test Suite                    ${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# Function to print colored status
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check for required environment variables
check_env() {
    print_status "Checking environment variables..."
    
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example if available..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
        else
            print_error "No .env or .env.example found. Please create .env with required API keys."
            exit 1
        fi
    fi
    
    # Check for API keys
    if grep -q "GOOGLE_API_KEY=" .env && grep -q "OPENAI_API_KEY=" .env; then
        print_success "API keys found in .env"
    else
        print_warning "API keys may be missing. Tests will run in mock mode."
        echo "USE_MOCK_EMBEDDINGS=true" >> .env
    fi
}

# Step 1: Stop and clean existing containers
cleanup_containers() {
    print_status "Cleaning up existing containers..."
    
    # Stop running containers
    docker-compose down 2>/dev/null || true
    
    # Remove old images to force rebuild
    docker rmi deepwiki-open_deepwiki:latest 2>/dev/null || true
    docker rmi deepwiki-open-deepwiki:latest 2>/dev/null || true
    
    print_success "Cleanup complete"
}

# Step 2: Rebuild the Docker image
rebuild_image() {
    print_status "Rebuilding Docker image with latest fixes..."
    
    # Build with no cache to ensure all fixes are included
    if docker-compose build --no-cache; then
        print_success "Docker image rebuilt successfully"
    else
        print_error "Failed to rebuild Docker image"
        exit 1
    fi
}

# Step 3: Start the container
start_container() {
    print_status "Starting Docker container with both backend and frontend..."
    
    # Start in detached mode
    if docker-compose up -d; then
        print_success "Container started"
        
        # Wait for services to be ready
        print_status "Waiting for services to initialize (API + Frontend)..."
        sleep 15  # Give more time for both services
        
        # Check API health
        print_status "Checking Backend API..."
        if curl -f http://localhost:8001/health >/dev/null 2>&1; then
            print_success "✅ Backend API is healthy at http://localhost:8001"
        else
            print_warning "Backend API may still be starting up"
        fi
        
        # Check Frontend
        print_status "Checking Frontend..."
        if curl -f http://localhost:9001 >/dev/null 2>&1; then
            print_success "✅ Frontend is running at http://localhost:9001"
        else
            print_warning "Frontend may still be starting up"
        fi
        
        echo ""
        print_success "Services available at:"
        echo "  📡 Backend API: http://localhost:8001"
        echo "  🌐 Frontend UI: http://localhost:9001"
        echo ""
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Step 4: Run embedding pipeline tests
run_tests() {
    print_status "Running embedding pipeline tests..."
    echo ""
    
    # Track test results
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0
    
    # Define test suites with new paths
    declare -a TEST_SUITES=(
        "test/embeddings/test_emergency_fix.py:Task 000 - Emergency Fix"
        "test/embeddings/test_empty_embedding_validation.py:Task 001 - Empty Embedding Validation"
        "test/embeddings/test_dimension_consistency.py:Task 003 - Dimension Consistency"
        "test/embeddings/test_batch_retry_logic.py:Task 005 - Batch Retry Logic"
        "test/embeddings/test_error_reporting.py:Task 007 - Error Reporting"
        "test/integration/test_e2e_embedding_pipeline.py:Task 009 - End-to-End Pipeline"
    )
    
    # Run each test suite
    for suite in "${TEST_SUITES[@]}"; do
        IFS=':' read -r test_file test_name <<< "$suite"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        
        echo -e "${BLUE}Testing: ${test_name}${NC}"
        
        if docker-compose exec -T -e PYTHONPATH=/app deepwiki pytest "$test_file" -v --tb=short 2>&1 | tee /tmp/test_output.log; then
            # Check if tests actually passed
            if grep -q "passed" /tmp/test_output.log && ! grep -q "failed" /tmp/test_output.log; then
                print_success "$test_name tests passed"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                print_error "$test_name tests had failures"
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
        else
            print_error "Failed to run $test_name tests"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        echo ""
    done
    
    # Summary
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${BLUE}                              TEST SUMMARY                                    ${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
    echo "Total Test Suites: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "All test suites passed!"
    else
        print_warning "Some tests failed. Check logs for details."
    fi
}

# Step 5: Test Frontend Integration
test_frontend() {
    print_status "Testing Frontend Integration..."
    echo ""
    
    # Check if frontend is accessible
    print_status "Testing frontend home page..."
    if curl -s http://localhost:9001 | grep -q "DeepWiki\|Next.js\|React"; then
        print_success "Frontend is serving content"
    else
        print_warning "Could not verify frontend content"
    fi
    
    # Check if frontend can reach backend
    print_status "Testing frontend-backend connection..."
    # The frontend should be configured to call the backend API
    if docker-compose logs 2>&1 | tail -100 | grep -q "SERVER_BASE_URL.*8001"; then
        print_success "Frontend is configured to connect to backend"
    else
        print_warning "Frontend-backend connection not verified"
    fi
    
    # Test a frontend API call (if applicable)
    print_status "Testing API integration through frontend..."
    if curl -s http://localhost:9001/api/health 2>/dev/null | grep -q "ok\|healthy"; then
        print_success "Frontend API proxy is working"
    else
        # This is okay, not all setups proxy through frontend
        print_status "Direct API access at http://localhost:8001"
    fi
    
    echo ""
}

# Step 6: Validate fixes are working
validate_fixes() {
    print_status "Validating embedding pipeline fixes..."
    echo ""
    
    # Check for empty vectors in logs
    print_status "Checking for empty vectors..."
    if docker-compose logs api 2>&1 | grep -E "\[\]|append\(\[\]\)" > /dev/null; then
        print_error "Found empty vectors in logs - fix may not be working"
    else
        print_success "No empty vectors found in logs"
    fi
    
    # Check for dimension validation
    print_status "Checking dimension validation..."
    if docker-compose logs api 2>&1 | grep -E "768.*dimension" > /dev/null; then
        print_success "Dimension validation is active"
    else
        print_warning "Could not confirm dimension validation"
    fi
    
    # Check for retry logic
    print_status "Checking retry logic..."
    if docker-compose logs api 2>&1 | grep -E "retry|backoff|attempt" > /dev/null; then
        print_success "Retry logic detected in logs"
    else
        print_warning "No retry activity detected (may not have encountered errors)"
    fi
    
    # Check for enhanced error reporting
    print_status "Checking error reporting..."
    if docker-compose logs api 2>&1 | grep -E "EmbeddingError|document_id|suggested_action" > /dev/null; then
        print_success "Enhanced error reporting is active"
    else
        print_warning "Enhanced error reporting not detected (may not have encountered errors)"
    fi
}

# Step 6: Generate test report
generate_report() {
    print_status "Generating test report..."
    
    # Create reports directory
    mkdir -p test-reports
    
    # Generate HTML report
    if docker-compose exec -T -e PYTHONPATH=/app deepwiki pytest test/ \
        --html=/app/test-reports/docker-test-report.html \
        --self-contained-html \
        -q 2>/dev/null; then
        
        # Copy report to host
        docker cp $(docker-compose ps -q deepwiki):/app/test-reports/docker-test-report.html \
            ./test-reports/docker-test-report-$(date +%Y%m%d-%H%M%S).html 2>/dev/null || true
        
        print_success "Test report generated in test-reports/"
    else
        print_warning "Could not generate HTML report"
    fi
}

# Step 7: Show container stats
show_stats() {
    print_status "Container resource usage:"
    docker stats --no-stream deepwiki-open_deepwiki_1 2>/dev/null || \
    docker stats --no-stream deepwiki-open-deepwiki-1 2>/dev/null || \
    print_warning "Could not get container stats"
}

# Main execution
main() {
    echo "Starting Docker test suite at $(date)"
    echo ""
    
    # Run all steps
    check_env
    cleanup_containers
    rebuild_image
    start_container
    test_frontend
    run_tests
    validate_fixes
    generate_report
    show_stats
    
    echo ""
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${BLUE}                           TEST SUITE COMPLETE                                ${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
    
    # Ask if user wants to keep container running
    echo ""
    read -p "Keep container running for manual testing? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Stopping container..."
        docker-compose down
        print_success "Container stopped"
    else
        print_success "Container is running. Access the app at:"
        echo "  - API: http://localhost:8001"
        echo "  - Web: http://localhost:9001"
        echo ""
        echo "To stop later, run: docker-compose down"
    fi
    
    echo ""
    print_success "Docker test suite completed at $(date)"
}

# Handle errors
trap 'print_error "Test suite failed. Check logs for details."; docker-compose logs --tail=50' ERR

# Run main function
main