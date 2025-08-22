#!/bin/bash

# One-liner API monitoring commands
# Copy and paste these directly into terminal

echo "
# 🚀 ONE-LINER API MONITORING COMMANDS

# Quick health check (instant result)
docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | grep -cE 'ERROR|WARNING|Exception' | xargs -I {} echo 'Issues found: {}'

# Count all issue types
docker-compose -f ../../docker-compose.dev.yml logs --tail=500 api 2>&1 | awk '/ERROR/{e++} /WARNING/{w++} /timeout/{t++} END{printf \"E:%d W:%d T:%d\\n\", e, w, t}'

# Show only critical issues
docker-compose -f ../../docker-compose.dev.yml logs --tail=1000 api 2>&1 | grep -E 'CRITICAL|FATAL|ERROR.*Exception|500|502|503'

# Live monitoring with color
docker-compose -f ../../docker-compose.dev.yml logs -f api 2>&1 | sed 's/ERROR/\\e[31mERROR\\e[0m/g; s/WARNING/\\e[33mWARNING\\e[0m/g'

# Generate instant report
docker-compose -f ../../docker-compose.dev.yml logs --tail=500 api 2>&1 | awk 'BEGIN{print \"API Health Report\"; print \"================\"} /ERROR/{e++} /WARNING/{w++} /timeout/{t++} END{printf \"Errors: %d\\nWarnings: %d\\nTimeouts: %d\\n\", e, w, t; if(e>10) print \"⚠️ HIGH ERROR RATE\"; else if(e>5) print \"⚡ MODERATE ISSUES\"; else print \"✅ HEALTHY\"}'

# Watch mode (updates every 5 seconds)
watch -n 5 'docker-compose -f ../../docker-compose.dev.yml logs --tail=100 api 2>&1 | grep -cE \"ERROR|WARNING\" | xargs -I {} echo \"Current issues: {}\"'

# Export last N errors to file
docker-compose -f ../../docker-compose.dev.yml logs --tail=1000 api 2>&1 | grep -E 'ERROR|Exception' > api_errors_$(date +%Y%m%d_%H%M%S).log

# Check specific time window (last 5 minutes of logs)
docker-compose -f ../../docker-compose.dev.yml logs --since 5m api 2>&1 | grep -cE 'ERROR|WARNING'

# Most frequent error patterns
docker-compose -f ../../docker-compose.dev.yml logs --tail=1000 api 2>&1 | grep ERROR | sed 's/.*ERROR/ERROR/' | sort | uniq -c | sort -rn | head -5

# Performance check
docker-compose -f ../../docker-compose.dev.yml logs --tail=500 api 2>&1 | grep -iE 'took [0-9]+ms' | sed 's/.*took //; s/ms.*//' | awk '{sum+=$1; count++} END {if(count>0) printf \"Avg response time: %.2fms (from %d requests)\\n\", sum/count, count}'
"