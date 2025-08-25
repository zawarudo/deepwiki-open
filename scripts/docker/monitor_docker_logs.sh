#!/bin/bash

# =============================================================================
# DeepWiki Docker Logs Monitor
# =============================================================================
# This script monitors Docker logs for embedding pipeline issues and fixes
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
CONTAINER_NAME="${1:-deepwiki-open_deepwiki_1}"
LOG_FILE="docker-monitor-$(date +%Y%m%d-%H%M%S).log"
MONITOR_INTERVAL=5  # seconds between checks

# Counters
EMPTY_VECTOR_COUNT=0
DIMENSION_VALIDATION_COUNT=0
RETRY_COUNT=0
ERROR_COUNT=0
SUCCESS_COUNT=0

# Print header
print_header() {
    clear
    echo -e "${BLUE}${BOLD}================================================================================${NC}"
    echo -e "${BLUE}${BOLD}                     DeepWiki Docker Logs Monitor                              ${NC}"
    echo -e "${BLUE}${BOLD}================================================================================${NC}"
    echo -e "${CYAN}Container: ${CONTAINER_NAME}${NC}"
    echo -e "${CYAN}Started: $(date)${NC}"
    echo -e "${CYAN}Log file: ${LOG_FILE}${NC}"
    echo -e "${BLUE}${BOLD}================================================================================${NC}"
    echo ""
}

# Print statistics
print_stats() {
    echo -e "${BOLD}📊 Current Statistics:${NC}"
    echo -e "  ${GREEN}✅ Successes:${NC} $SUCCESS_COUNT"
    echo -e "  ${RED}❌ Errors:${NC} $ERROR_COUNT"
    echo -e "  ${YELLOW}🔄 Retries:${NC} $RETRY_COUNT"
    echo -e "  ${MAGENTA}📏 Dimension Validations:${NC} $DIMENSION_VALIDATION_COUNT"
    echo -e "  ${RED}⚠️  Empty Vectors Detected:${NC} $EMPTY_VECTOR_COUNT"
    echo ""
}

# Check if container is running
check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        # Try alternative format
        ALT_NAME="${CONTAINER_NAME//_/-}"
        if docker ps --format '{{.Names}}' | grep -q "$ALT_NAME"; then
            CONTAINER_NAME="$ALT_NAME"
            return 0
        fi
        
        echo -e "${RED}❌ Container $CONTAINER_NAME is not running${NC}"
        echo "Available containers:"
        docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
        exit 1
    fi
}

# Monitor for empty vectors
monitor_empty_vectors() {
    local new_empties=$(docker logs "$CONTAINER_NAME" 2>&1 | tail -100 | grep -c '\[\]' || echo 0)
    if [ "$new_empties" -gt 0 ]; then
        EMPTY_VECTOR_COUNT=$((EMPTY_VECTOR_COUNT + new_empties))
        echo -e "${RED}⚠️  [$(date +%H:%M:%S)] Detected empty vector creation!${NC}"
        docker logs "$CONTAINER_NAME" 2>&1 | tail -100 | grep '\[\]' | head -2 >> "$LOG_FILE"
    fi
}

# Monitor dimension validation
monitor_dimensions() {
    local new_dims=$(docker logs "$CONTAINER_NAME" 2>&1 | tail -100 | grep -c '768.*dimension' || echo 0)
    if [ "$new_dims" -gt 0 ]; then
        DIMENSION_VALIDATION_COUNT=$((DIMENSION_VALIDATION_COUNT + new_dims))
        echo -e "${MAGENTA}📏 [$(date +%H:%M:%S)] Dimension validation active (768-dim)${NC}"
    fi
}

# Monitor retry logic
monitor_retries() {
    local new_retries=$(docker logs "$CONTAINER_NAME" 2>&1 | tail -100 | grep -cE 'retry|backoff|attempt [0-9]' || echo 0)
    if [ "$new_retries" -gt 0 ]; then
        RETRY_COUNT=$((RETRY_COUNT + new_retries))
        echo -e "${YELLOW}🔄 [$(date +%H:%M:%S)] Retry logic triggered (${new_retries} new retries)${NC}"
        docker logs "$CONTAINER_NAME" 2>&1 | tail -100 | grep -E 'retry|backoff' | head -2 >> "$LOG_FILE"
    fi
}

# Monitor errors
monitor_errors() {
    local new_errors=$(docker logs "$CONTAINER_NAME" 2>&1 | tail -100 | grep -cE 'ERROR|Exception|Failed|failure' || echo 0)
    if [ "$new_errors" -gt 0 ]; then
        ERROR_COUNT=$((ERROR_COUNT + new_errors))
        echo -e "${RED}❌ [$(date +%H:%M:%S)] Errors detected (${new_errors} new)${NC}"
        
        # Check for enhanced error reporting
        if docker logs "$CONTAINER_NAME" 2>&1 | tail -100 | grep -q 'EmbeddingError\|document_id\|suggested_action'; then
            echo -e "${GREEN}  ✅ Enhanced error reporting is active${NC}"
        fi
    fi
}

# Monitor successes
monitor_success() {
    local new_success=$(docker logs "$CONTAINER_NAME" 2>&1 | tail -100 | grep -cE 'successfully|SUCCESS|passed|✅' || echo 0)
    if [ "$new_success" -gt 0 ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + new_success))
        echo -e "${GREEN}✅ [$(date +%H:%M:%S)] Success events: ${new_success}${NC}"
    fi
}

# Monitor critical fixes
monitor_fixes() {
    echo -e "${BOLD}🔍 Checking Critical Fixes:${NC}"
    
    # Check 1: Empty vector prevention
    if docker logs "$CONTAINER_NAME" 2>&1 | tail -500 | grep -q 'append(\[\])'; then
        echo -e "  ${RED}❌ Empty vector creation detected - FIX NOT WORKING${NC}"
    else
        echo -e "  ${GREEN}✅ No empty vector creation detected${NC}"
    fi
    
    # Check 2: Model name
    if docker logs "$CONTAINER_NAME" 2>&1 | tail -500 | grep -q 'text-embedding-004'; then
        echo -e "  ${GREEN}✅ Correct model name in use (text-embedding-004)${NC}"
    elif docker logs "$CONTAINER_NAME" 2>&1 | tail -500 | grep -q 'embedding-001'; then
        echo -e "  ${RED}❌ Wrong model name detected (embedding-001)${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Model name not detected in recent logs${NC}"
    fi
    
    # Check 3: Dimension validation
    if docker logs "$CONTAINER_NAME" 2>&1 | tail -500 | grep -q '_validate_embedding\|validate_dimension'; then
        echo -e "  ${GREEN}✅ Dimension validation is active${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Dimension validation not detected in recent logs${NC}"
    fi
    
    # Check 4: Retry logic
    if docker logs "$CONTAINER_NAME" 2>&1 | tail -500 | grep -q 'exponential_backoff\|retry.*attempt'; then
        echo -e "  ${GREEN}✅ Retry logic is active${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Retry logic not detected in recent logs${NC}"
    fi
    
    # Check 5: Error reporting
    if docker logs "$CONTAINER_NAME" 2>&1 | tail -500 | grep -q 'EmbeddingError\|BatchSummary'; then
        echo -e "  ${GREEN}✅ Enhanced error reporting is active${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Enhanced error reporting not detected${NC}"
    fi
    
    echo ""
}

# Tail logs with filtering
tail_logs() {
    echo -e "${BOLD}📜 Recent Log Activity:${NC}"
    echo -e "${CYAN}--------------------------------------------------------------------------------${NC}"
    
    # Show last 10 relevant log lines
    docker logs "$CONTAINER_NAME" 2>&1 | tail -20 | \
        grep -E 'embedding|dimension|retry|error|success|validation|768' | \
        tail -10 | \
        sed "s/ERROR/${RED}ERROR${NC}/g" | \
        sed "s/WARNING/${YELLOW}WARNING${NC}/g" | \
        sed "s/SUCCESS/${GREEN}SUCCESS${NC}/g" | \
        sed "s/INFO/${CYAN}INFO${NC}/g"
    
    echo -e "${CYAN}--------------------------------------------------------------------------------${NC}"
}

# Export logs for analysis
export_logs() {
    local export_file="docker-logs-export-$(date +%Y%m%d-%H%M%S).txt"
    echo -e "${BLUE}Exporting logs to ${export_file}...${NC}"
    
    {
        echo "=== DeepWiki Docker Logs Export ==="
        echo "Container: $CONTAINER_NAME"
        echo "Exported: $(date)"
        echo "Statistics:"
        echo "  - Errors: $ERROR_COUNT"
        echo "  - Successes: $SUCCESS_COUNT"
        echo "  - Retries: $RETRY_COUNT"
        echo "  - Dimension Validations: $DIMENSION_VALIDATION_COUNT"
        echo "  - Empty Vectors: $EMPTY_VECTOR_COUNT"
        echo ""
        echo "=== Full Logs ==="
        docker logs "$CONTAINER_NAME" 2>&1
    } > "$export_file"
    
    echo -e "${GREEN}✅ Logs exported to ${export_file}${NC}"
}

# Main monitoring loop
main_loop() {
    while true; do
        print_header
        print_stats
        
        # Run all monitors
        monitor_empty_vectors
        monitor_dimensions
        monitor_retries
        monitor_errors
        monitor_success
        
        echo ""
        monitor_fixes
        tail_logs
        
        echo ""
        echo -e "${CYAN}Press [q] to quit, [e] to export logs, [c] to clear stats, or wait ${MONITOR_INTERVAL}s for refresh...${NC}"
        
        # Read user input with timeout
        if read -t "$MONITOR_INTERVAL" -n 1 key; then
            case $key in
                q|Q)
                    echo -e "\n${BLUE}Monitoring stopped. Log saved to ${LOG_FILE}${NC}"
                    exit 0
                    ;;
                e|E)
                    export_logs
                    sleep 2
                    ;;
                c|C)
                    EMPTY_VECTOR_COUNT=0
                    DIMENSION_VALIDATION_COUNT=0
                    RETRY_COUNT=0
                    ERROR_COUNT=0
                    SUCCESS_COUNT=0
                    echo -e "\n${GREEN}✅ Statistics cleared${NC}"
                    sleep 1
                    ;;
            esac
        fi
    done
}

# Signal handlers
trap 'echo -e "\n${BLUE}Monitoring stopped by user${NC}"; exit 0' INT TERM

# Main execution
main() {
    print_header
    
    # Check container
    check_container
    
    echo -e "${GREEN}✅ Container found: $CONTAINER_NAME${NC}"
    echo -e "${BLUE}Starting monitoring...${NC}"
    echo ""
    
    # Create log file
    echo "=== DeepWiki Docker Monitor Log ===" > "$LOG_FILE"
    echo "Started: $(date)" >> "$LOG_FILE"
    echo "Container: $CONTAINER_NAME" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    # Start monitoring loop
    sleep 2
    main_loop
}

# Run main function
main