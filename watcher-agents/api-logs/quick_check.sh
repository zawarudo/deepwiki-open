#!/bin/bash

# Quick API Health Check - One-liner style analysis

# Quick error check with summary
quick_check() {
    echo "🔍 Quick API Health Check"
    docker-compose -f ../../docker-compose.dev.yml logs --tail=200 api 2>&1 | \
    awk '
    BEGIN { 
        errors=0; warnings=0; critical=0; timeouts=0; http_errors=0 
    }
    /CRITICAL|FATAL|PANIC/ { critical++ }
    /ERROR|Exception|Traceback/ { errors++ }
    /WARNING/ { warnings++ }
    /[Tt]imeout/ { timeouts++ }
    /"code":[[:space:]]*[45][0-9]{2}/ { http_errors++ }
    END {
        print "=================="
        print "❌ Critical:", critical
        print "🔴 Errors:", errors
        print "⚠️  Warnings:", warnings
        print "⏱️  Timeouts:", timeouts
        print "🌐 HTTP Errors:", http_errors
        print "=================="
        
        if (critical > 0) {
            print "🚨 CRITICAL ISSUES DETECTED!"
            exit 2
        } else if (errors > 10) {
            print "⚠️ HIGH ERROR RATE!"
            exit 1
        } else if (errors > 5 || warnings > 10) {
            print "⚡ ELEVATED ISSUES"
            exit 0
        } else {
            print "✅ SYSTEM HEALTHY"
            exit 0
        }
    }'
    return $?
}

# One-liner versions for quick checks
case "${1:-check}" in
    check)
        quick_check
        ;;
    
    errors)
        # Just show errors
        echo "🔴 Recent Errors:"
        docker-compose -f ../../docker-compose.dev.yml logs --tail=500 api 2>&1 | \
        grep -E "ERROR|Exception|Traceback" | head -20
        ;;
    
    warnings)
        # Just show warnings
        echo "⚠️ Recent Warnings:"
        docker-compose -f ../../docker-compose.dev.yml logs --tail=500 api 2>&1 | \
        grep -E "WARNING" | head -20
        ;;
    
    critical)
        # Just show critical issues
        echo "🚨 Critical Issues:"
        docker-compose -f ../../docker-compose.dev.yml logs --tail=500 api 2>&1 | \
        grep -E "CRITICAL|FATAL|PANIC|500|502|503" | head -10
        ;;
    
    watch)
        # Live monitoring
        watch -n 10 "$0 check"
        ;;
    
    tail)
        # Live tail with error highlighting
        docker-compose -f ../../docker-compose.dev.yml logs -f api 2>&1 | \
        grep --line-buffered -E "ERROR|WARNING|Exception|Traceback|timeout|[45][0-9]{2}" | \
        sed 's/ERROR/\x1b[31mERROR\x1b[0m/g; s/WARNING/\x1b[33mWARNING\x1b[0m/g'
        ;;
    
    summary)
        # Full one-liner summary
        docker-compose -f ../../docker-compose.dev.yml logs --tail=1000 api 2>&1 | \
        grep -E "ERROR|WARNING|Exception|timeout|[45][0-9]{2}" | \
        awk '{if(/ERROR|Exception/) e++; if(/WARNING/) w++; if(/timeout/) t++} END {printf "Errors: %d | Warnings: %d | Timeouts: %d\n", e, w, t}'
        ;;
    
    *)
        echo "Usage: $0 {check|errors|warnings|critical|watch|tail|summary}"
        echo ""
        echo "  check    - Quick health check with counts"
        echo "  errors   - Show recent errors"
        echo "  warnings - Show recent warnings"
        echo "  critical - Show critical issues"
        echo "  watch    - Live monitoring (updates every 10s)"
        echo "  tail     - Live tail with highlighting"
        echo "  summary  - One-line summary"
        ;;
esac