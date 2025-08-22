#!/bin/bash

# Claude hook for checking API errors automatically
# This hook can be triggered on various events to monitor API health

# Function to check for errors in API logs
check_api_errors() {
    echo "🔍 Checking API logs for errors..."
    
    # Capture the last 200 lines of API logs
    LOGS=$(docker-compose -f docker-compose.dev.yml logs --tail=200 api 2>&1)
    
    # Check for critical errors
    CRITICAL_ERRORS=$(echo "$LOGS" | grep -iE "(CRITICAL|FATAL|PANIC)" | head -5)
    if [ ! -z "$CRITICAL_ERRORS" ]; then
        echo "❌ CRITICAL ERRORS FOUND:"
        echo "$CRITICAL_ERRORS"
        echo ""
    fi
    
    # Check for regular errors (look for actual ERROR log level entries)
    # Match lines that have ERROR in the log level position (after timestamp)
    ERRORS=$(echo "$LOGS" | grep -E "ERROR\s+-\s+api\." | head -10)
    if [ ! -z "$ERRORS" ]; then
        echo "⚠️ ERRORS FOUND:"
        echo "$ERRORS"
        echo ""
    fi
    
    # Check for Python exceptions and tracebacks
    EXCEPTIONS=$(echo "$LOGS" | grep -E "(Exception:|Traceback \(most recent call last\)|raise \w+Error)" | head -5)
    if [ ! -z "$EXCEPTIONS" ]; then
        echo "🐛 EXCEPTIONS FOUND:"
        echo "$EXCEPTIONS"
        echo ""
    fi
    
    # Check for warnings (actual WARNING log entries)
    WARNINGS=$(echo "$LOGS" | grep -E "WARNING\s+-\s+api\." | head -5)
    if [ ! -z "$WARNINGS" ]; then
        echo "⚡ WARNINGS FOUND:"
        echo "$WARNINGS"
        echo ""
    fi
    
    # Check for HTTP errors
    HTTP_ERRORS=$(echo "$LOGS" | grep -E "\"code\":\s*(400|401|403|404|500|502|503)" | head -5)
    if [ ! -z "$HTTP_ERRORS" ]; then
        echo "🌐 HTTP ERRORS FOUND:"
        echo "$HTTP_ERRORS"
        echo ""
    fi
    
    # Check for specific API connection issues
    API_ISSUES=$(echo "$LOGS" | grep -iE "(connection refused|timeout|rate limit exceeded|ConnectTimeout|ReadTimeout)" | head -5)
    if [ ! -z "$API_ISSUES" ]; then
        echo "🔌 API CONNECTION ISSUES:"
        echo "$API_ISSUES"
        echo ""
    fi
    
    # If no issues found
    if [ -z "$CRITICAL_ERRORS" ] && [ -z "$ERRORS" ] && [ -z "$EXCEPTIONS" ] && [ -z "$WARNINGS" ] && [ -z "$HTTP_ERRORS" ] && [ -z "$API_ISSUES" ]; then
        echo "✅ No errors or warnings detected in recent API logs"
    else
        echo "💡 Run '/check-api-errors' command for detailed analysis"
    fi
}

# Execute the check
check_api_errors