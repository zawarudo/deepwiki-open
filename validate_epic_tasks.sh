#!/bin/bash

# Validation script for epic-setup-api-testing-with-tdd-loop-agent tasks
# This script validates all completed tasks (001-005)

# Don't exit on errors - we want to see all validation results
set +e

EPIC_WORKTREE="/home/ubuwarudo/Personal/epic-setup-api-testing-with-tdd-loop-agent"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "Validating Epic Tasks 001-005"
echo "================================================"

# Check if worktree exists
if [ ! -d "$EPIC_WORKTREE" ]; then
    echo -e "${RED}✗ Worktree not found at $EPIC_WORKTREE${NC}"
    exit 1
fi

cd "$EPIC_WORKTREE"

echo -e "\n${YELLOW}Task 001: Validate pytest infrastructure${NC}"
echo "------------------------------------------------"

# Check pytest is installed
if python3 -m pytest --version > /dev/null 2>&1; then
    echo -e "${GREEN}✓ pytest installed${NC}"
    python3 -m pytest --version | head -1
else
    echo -e "${RED}✗ pytest not installed${NC}"
fi

# Check pytest-asyncio
if python3 -c "import pytest_asyncio; print(f'pytest-asyncio {pytest_asyncio.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓ pytest-asyncio installed${NC}"
else
    echo -e "${RED}✗ pytest-asyncio not installed${NC}"
fi

# Check test directory structure
if [ -d "api/tests" ]; then
    echo -e "${GREEN}✓ api/tests directory exists${NC}"
    echo "  Test files found:"
    ls -la api/tests/*.py 2>/dev/null | awk '{print "    - " $NF}' | head -10
else
    echo -e "${RED}✗ api/tests directory missing${NC}"
fi

echo -e "\n${YELLOW}Task 002: Validate test fixtures${NC}"
echo "------------------------------------------------"

# Check conftest.py
if [ -f "api/tests/conftest.py" ]; then
    echo -e "${GREEN}✓ conftest.py exists${NC}"
    echo "  Fixtures defined:"
    grep -E "^@pytest\.fixture|^async def |^def " api/tests/conftest.py | head -5 | sed 's/^/    /'
else
    echo -e "${RED}✗ conftest.py missing${NC}"
fi

# Check fixture files
if [ -d "api/tests/fixtures" ]; then
    echo -e "${GREEN}✓ fixtures directory exists${NC}"
    echo "  Fixture files:"
    ls -la api/tests/fixtures/*.py 2>/dev/null | awk '{print "    - " $NF}' | head -5
else
    echo -e "${YELLOW}⚠ fixtures directory not found (may be optional)${NC}"
fi

echo -e "\n${YELLOW}Task 003: Validate embedding client tests${NC}"
echo "------------------------------------------------"

if [ -f "api/tests/test_embedding_client.py" ]; then
    echo -e "${GREEN}✓ test_embedding_client.py exists${NC}"
    
    # Count test functions
    TEST_COUNT=$(grep -c "^def test_\|^async def test_" api/tests/test_embedding_client.py || echo "0")
    echo "  Number of tests: $TEST_COUNT"
    
    # Run the tests
    echo "  Running embedding client tests..."
    python3 -m pytest api/tests/test_embedding_client.py --tb=short -q 2>&1 > /tmp/test_embedding.log
    if grep -q "passed\|failed" /tmp/test_embedding.log; then
        PASSED=$(grep -o "[0-9]* passed" /tmp/test_embedding.log | grep -o "[0-9]*" | head -1)
        FAILED=$(grep -o "[0-9]* failed" /tmp/test_embedding.log | grep -o "[0-9]*" | head -1)
        echo -e "  Results: ${GREEN}${PASSED:-0} passed${NC}, ${RED}${FAILED:-0} failed${NC}"
    fi
else
    echo -e "${RED}✗ test_embedding_client.py missing${NC}"
fi

echo -e "\n${YELLOW}Task 004: Validate vector validation tests${NC}"
echo "------------------------------------------------"

if [ -f "api/tests/test_vector_validation.py" ]; then
    echo -e "${GREEN}✓ test_vector_validation.py exists${NC}"
    
    # Count test functions
    TEST_COUNT=$(grep -c "^def test_\|^async def test_" api/tests/test_vector_validation.py || echo "0")
    echo "  Number of tests: $TEST_COUNT"
    
    # Run the tests
    echo "  Running vector validation tests..."
    python3 -m pytest api/tests/test_vector_validation.py --tb=short -q 2>&1 > /tmp/test_vector.log
    if grep -q "passed\|failed" /tmp/test_vector.log; then
        PASSED=$(grep -o "[0-9]* passed" /tmp/test_vector.log | grep -o "[0-9]*" | head -1)
        FAILED=$(grep -o "[0-9]* failed" /tmp/test_vector.log | grep -o "[0-9]*" | head -1)
        echo -e "  Results: ${GREEN}${PASSED:-0} passed${NC}, ${RED}${FAILED:-0} failed${NC}"
    fi
else
    echo -e "${RED}✗ test_vector_validation.py missing${NC}"
fi

echo -e "\n${YELLOW}Task 005: Validate pipeline integration tests${NC}"
echo "------------------------------------------------"

if [ -f "api/tests/test_rag_pipeline.py" ]; then
    echo -e "${GREEN}✓ test_rag_pipeline.py exists${NC}"
    
    # Count test functions
    TEST_COUNT=$(grep -c "^def test_\|^async def test_" api/tests/test_rag_pipeline.py || echo "0")
    echo "  Number of tests: $TEST_COUNT"
    
    # Run the tests (may fail due to API key)
    echo "  Running pipeline tests..."
    python3 -m pytest api/tests/test_rag_pipeline.py --tb=short -q 2>&1 > /tmp/test_pipeline.log
    if grep -q "passed\|failed" /tmp/test_pipeline.log; then
        PASSED=$(grep -o "[0-9]* passed" /tmp/test_pipeline.log | grep -o "[0-9]*" | head -1)
        FAILED=$(grep -o "[0-9]* failed" /tmp/test_pipeline.log | grep -o "[0-9]*" | head -1)
        echo -e "  Results: ${GREEN}${PASSED:-0} passed${NC}, ${RED}${FAILED:-0} failed${NC}"
    fi
    
    # Check for API key errors
    if grep -q "API key not valid\|GOOGLE_API_KEY" /tmp/test_pipeline.log 2>/dev/null; then
        echo -e "  ${YELLOW}⚠ API key issue detected (expected - root cause identified)${NC}"
    fi
else
    echo -e "${RED}✗ test_rag_pipeline.py missing${NC}"
fi

echo -e "\n${YELLOW}Root Cause Validation${NC}"
echo "------------------------------------------------"

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${RED}✗ GOOGLE_API_KEY not set (confirms root cause)${NC}"
else
    echo -e "${GREEN}✓ GOOGLE_API_KEY is set${NC}"
    # Test if key is valid by making a simple request
    echo "  Testing API key validity..."
fi

# Check for empty vector handling in code
echo -e "\n${YELLOW}Empty Vector Handling Check${NC}"
echo "------------------------------------------------"

if [ -f "api/rag.py" ]; then
    if grep -q "_validate_and_filter_embeddings\|empty.*vector\|len(vector) == 0" api/rag.py; then
        echo -e "${GREEN}✓ Empty vector validation found in rag.py${NC}"
        grep -n "empty.*vector\|len(vector) == 0" api/rag.py | head -3 | sed 's/^/    Line /'
    fi
fi

if [ -f "api/google_embedding_client.py" ]; then
    if grep -q "return \[\]\|embedding.*\[\]" api/google_embedding_client.py; then
        echo -e "${GREEN}✓ Empty array returns found in google_embedding_client.py${NC}"
        grep -n "return \[\]" api/google_embedding_client.py | head -3 | sed 's/^/    Line /'
    fi
fi

echo -e "\n${YELLOW}Summary Report${NC}"
echo "================================================"

# Count all test files
TOTAL_TEST_FILES=$(find api/tests -name "test_*.py" -type f 2>/dev/null | wc -l)
echo "Total test files created: $TOTAL_TEST_FILES"

# Run all tests and get summary
echo -e "\nRunning complete test suite..."
python3 -m pytest api/tests/ --tb=no -q 2>&1 > /tmp/all_tests.log
tail -5 /tmp/all_tests.log

echo -e "\n${GREEN}Validation Complete!${NC}"
echo "================================================"
echo "Next steps:"
echo "  1. Set GOOGLE_API_KEY environment variable"
echo "  2. Run Task 006 to implement validation fixes"
echo "  3. Run Task 007 for Docker verification"