# API Log Monitoring Workflow Prompt

## Objective
Set up and run an intelligent API log monitoring system that detects early error signs, analyzes patterns, and generates actionable reports with human feedback integration.

## Workflow Steps

### 1. Initial Setup
```bash
# Navigate to the monitoring agent directory
cd watcher-agents/api-logs

# Ensure Python dependencies are available
python3 --version  # Should be 3.7+
```

### 2. Configuration Check
Review and customize the configuration if needed:
```bash
# View current configuration
cat config/default_config.json

# Key settings to consider:
# - check_interval: How often to check logs (default: 30 seconds)
# - log_lines: Number of log lines to analyze (default: 500)
# - report_threshold: Errors before report generation (default: 3)
# - docker_compose_file: Path to your docker-compose file
# - container_name: Name of the API container to monitor
```

### 3. Run Single Analysis (Testing)
Start with a single analysis to test the system:
```bash
# Run once to check current state
python3 main_agent.py --once

# Run with verbose output for debugging
python3 main_agent.py --once --verbose
```

### 4. Start Continuous Monitoring
For production monitoring:
```bash
# Start the continuous monitoring loop
python3 main_agent.py

# Or run in background with nohup
nohup python3 main_agent.py > monitoring.log 2>&1 &

# Or use screen/tmux for persistent sessions
screen -S api-monitor
python3 main_agent.py
# Detach with Ctrl+A, D
```

### 5. Monitor Reports
Check generated reports:
```bash
# List all generated reports
ls -la reports/

# View the latest report
ls -t reports/*.md | head -1 | xargs cat

# Watch for new reports
watch -n 60 'ls -la reports/ | tail -5'
```

### 6. Provide Feedback
After reviewing a report, provide feedback to improve the system:
```bash
# Provide feedback on the latest report
LATEST_REPORT=$(ls -t reports/*.md | head -1)
python3 feedback_collector.py "$LATEST_REPORT"

# Follow the interactive prompts to:
# - Rate accuracy (1-5)
# - Rate relevance (1-5)
# - Rate actionability (1-5)
# - Identify false positives
# - Note missed issues
# - Suggest improvements
```

### 7. Analyze Feedback
Review collected feedback to understand system performance:
```bash
# Generate feedback analysis report
python3 feedback_collector.py --analyze
```

### 8. Check System State
Monitor the agent's state and history:
```bash
# View last check timestamp
cat state/last_check.json | python3 -m json.tool

# View error history
cat state/error_history.json | python3 -m json.tool

# Check recent errors
cat state/error_history.json | python3 -c "import json, sys; data=json.load(sys.stdin); [print(f\"{e['timestamp']}: {e['error_count']} errors, {e['warning_count']} warnings\") for e in data.get('errors', [])[-5:]]"
```

## Quick Commands

### Emergency Check
When you need immediate analysis:
```bash
# Quick check with immediate report generation
python3 main_agent.py --once --verbose | tee emergency_check_$(date +%Y%m%d_%H%M%S).log
```

### Pattern Search
Look for specific patterns in logs:
```bash
# Check for specific error patterns
docker-compose -f ../../docker-compose.dev.yml logs --tail=1000 api | grep -E "(ERROR|Exception|Traceback|500|timeout)"
```

### Reset State
Clear history and start fresh:
```bash
# Backup current state
cp -r state state_backup_$(date +%Y%m%d_%H%M%S)

# Clear state files
rm -f state/*.json

# Restart monitoring
python3 main_agent.py
```

## Automation Script

Create a simple automation script `run_monitor.sh`:
```bash
#!/bin/bash

# API Log Monitor Automation Script
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to check if monitor is running
is_running() {
    pgrep -f "python3 main_agent.py" > /dev/null 2>&1
}

# Function to start monitor
start_monitor() {
    if is_running; then
        echo "Monitor is already running"
    else
        echo "Starting API log monitor..."
        nohup python3 main_agent.py > logs/monitor_$(date +%Y%m%d).log 2>&1 &
        echo "Monitor started with PID: $!"
    fi
}

# Function to stop monitor
stop_monitor() {
    if is_running; then
        echo "Stopping API log monitor..."
        pkill -f "python3 main_agent.py"
        echo "Monitor stopped"
    else
        echo "Monitor is not running"
    fi
}

# Function to check status
check_status() {
    if is_running; then
        echo "Monitor is running"
        echo "Recent reports:"
        ls -t reports/*.md 2>/dev/null | head -3
    else
        echo "Monitor is not running"
    fi
}

# Main script logic
case "$1" in
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    restart)
        stop_monitor
        sleep 2
        start_monitor
        ;;
    status)
        check_status
        ;;
    report)
        # Generate immediate report
        python3 main_agent.py --once
        ;;
    feedback)
        # Collect feedback on latest report
        LATEST=$(ls -t reports/*.md 2>/dev/null | head -1)
        if [ -n "$LATEST" ]; then
            python3 feedback_collector.py "$LATEST"
        else
            echo "No reports found"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|report|feedback}"
        exit 1
        ;;
esac
```

Make it executable:
```bash
chmod +x run_monitor.sh
```

Then use:
```bash
./run_monitor.sh start    # Start monitoring
./run_monitor.sh status   # Check status
./run_monitor.sh report   # Generate immediate report
./run_monitor.sh feedback # Provide feedback
./run_monitor.sh stop     # Stop monitoring
```

## Integration with Existing Systems

### Slack Notifications (Example)
Add to `main_agent.py` after report generation:
```python
import requests

def send_slack_notification(report_file, severity):
    if severity in ['high', 'critical']:
        webhook_url = "YOUR_SLACK_WEBHOOK_URL"
        message = {
            "text": f"🚨 API Alert: {severity.upper()} severity detected!",
            "attachments": [{
                "color": "danger" if severity == 'critical' else "warning",
                "title": "API Log Analysis Report",
                "text": f"New report generated: {report_file}",
                "footer": "API Monitor"
            }]
        }
        requests.post(webhook_url, json=message)
```

### Cron Job Setup
For scheduled analysis:
```bash
# Add to crontab for hourly analysis
0 * * * * cd /path/to/watcher-agents/api-logs && python3 main_agent.py --once >> cron_monitor.log 2>&1
```

## Troubleshooting Checklist

1. **No logs fetched?**
   - Check Docker is running: `docker ps`
   - Verify container name: `docker-compose ps`
   - Check path to docker-compose file

2. **Too many false positives?**
   - Review `config/default_config.json`
   - Adjust `early_warning_patterns`
   - Increase `report_threshold`

3. **Reports not generating?**
   - Check `report_cooldown` setting
   - Verify severity calculations
   - Look at `state/last_check.json`

4. **Memory issues?**
   - Reduce `log_lines` in config
   - Clear old reports: `find reports/ -mtime +30 -delete`
   - Restart the monitor

## Success Indicators

✅ Monitor is successfully running when:
- Reports are generated for high-severity issues
- False positive rate is < 20%
- Feedback ratings average > 3.5/5
- Error patterns are detected before system failures
- Response time to critical issues improves

## Next Steps

After successful setup:
1. Customize error patterns for your specific API
2. Integrate with your alerting system
3. Set up automated responses for common issues
4. Review weekly pattern analysis
5. Continuously provide feedback to improve accuracy

---

## Quick Start Command

For immediate monitoring with all features:
```bash
cd watcher-agents/api-logs && \
python3 main_agent.py --once --verbose && \
echo "Initial check complete. Starting continuous monitoring..." && \
python3 main_agent.py
```

This prompt provides a complete workflow to set up, run, monitor, and maintain the API log monitoring system with human feedback integration.