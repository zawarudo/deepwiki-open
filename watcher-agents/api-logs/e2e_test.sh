#!/bin/bash

# E2E API Log Monitoring Test
# Simple, Docker-based, one-command monitoring

set -e

echo "🧪 E2E API Log Monitoring Test"
echo "=============================="

# Test 1: Basic health check
echo -e "\n📋 Test 1: Basic Health Check"
if docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | \
   grep -qE "ERROR|Exception|Traceback"; then
    echo "❌ Errors detected in logs"
    ERROR_COUNT=$(docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | \
                  grep -cE "ERROR|Exception|Traceback" || true)
    echo "   Found $ERROR_COUNT error(s)"
else
    echo "✅ No errors in recent logs"
fi

# Test 2: Warning detection
echo -e "\n📋 Test 2: Warning Detection"
WARNING_COUNT=$(docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | \
                grep -cE "WARNING" || true)
if [ "$WARNING_COUNT" -gt 0 ]; then
    echo "⚠️  Found $WARNING_COUNT warning(s)"
else
    echo "✅ No warnings detected"
fi

# Test 3: Performance issues
echo -e "\n📋 Test 3: Performance Issues"
TIMEOUT_COUNT=$(docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | \
                grep -ciE "timeout|slow|latency" || true)
if [ "$TIMEOUT_COUNT" -gt 0 ]; then
    echo "⏱️  Found $TIMEOUT_COUNT performance issue(s)"
else
    echo "✅ No performance issues detected"
fi

# Test 4: HTTP errors
echo -e "\n📋 Test 4: HTTP Error Codes"
HTTP_ERRORS=$(docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | \
              grep -oE '"code":[[:space:]]*[45][0-9]{2}' | wc -l || true)
if [ "$HTTP_ERRORS" -gt 0 ]; then
    echo "🌐 Found $HTTP_ERRORS HTTP error(s)"
    docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | \
    grep -oE '"code":[[:space:]]*[45][0-9]{2}' | sort | uniq -c | head -5
else
    echo "✅ No HTTP errors detected"
fi

# Test 5: Critical issues
echo -e "\n📋 Test 5: Critical Issues"
if docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | \
   grep -qiE "CRITICAL|FATAL|PANIC|OutOfMemory"; then
    echo "🚨 CRITICAL ISSUES DETECTED!"
    docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | \
    grep -iE "CRITICAL|FATAL|PANIC|OutOfMemory" | head -5
    EXIT_CODE=2
else
    echo "✅ No critical issues"
    EXIT_CODE=0
fi

# Summary
echo -e "\n📊 Test Summary"
echo "==============="
docker-compose -f ../../docker-compose.dev.yml logs --tail=500 api 2>&1 | \
awk '
BEGIN { 
    print "Issue Type     | Count"
    print "---------------|------"
}
/ERROR|Exception/ { errors++ }
/WARNING/ { warnings++ }
/timeout/i { timeouts++ }
/"code":[[:space:]]*[45][0-9]{2}/ { http++ }
/CRITICAL|FATAL/ { critical++ }
END {
    printf "Critical       | %d\n", critical+0
    printf "Errors         | %d\n", errors+0
    printf "Warnings       | %d\n", warnings+0
    printf "Timeouts       | %d\n", timeouts+0
    printf "HTTP Errors    | %d\n", http+0
    print ""
    
    # Overall health score
    score = 100
    score -= critical * 20
    score -= errors * 5
    score -= warnings * 2
    score -= timeouts * 3
    score -= http * 2
    if (score < 0) score = 0
    
    printf "Health Score: %d/100\n", score
    
    if (score >= 90) {
        print "Status: 🟢 HEALTHY"
    } else if (score >= 70) {
        print "Status: 🟡 DEGRADED"
    } else if (score >= 50) {
        print "Status: 🟠 UNHEALTHY"
    } else {
        print "Status: 🔴 CRITICAL"
    }
}'

exit $EXIT_CODE