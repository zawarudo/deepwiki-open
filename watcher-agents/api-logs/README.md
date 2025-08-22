# API Log Monitoring Agent

An intelligent, autonomous monitoring system that continuously analyzes API logs to detect early error signs, identify patterns, and generate actionable reports for human feedback.

## Features

### 🔍 Early Error Detection
- Detects critical errors, exceptions, and warnings
- Identifies error clusters and patterns
- Recognizes early warning signs before they become critical

### 📊 Pattern Analysis
- Analyzes error trends and velocity
- Detects repeated error patterns
- Identifies anomalies and unusual behaviors
- Tracks common error terms and frequencies

### 📝 Intelligent Reporting
- Generates comprehensive analysis reports
- Provides severity assessments (critical/high/medium/low)
- Offers actionable recommendations
- Creates timeline of events

### 🔄 Feedback Loop
- Collects human feedback on reports
- Learns from feedback to improve analysis
- Tracks action taken on reports
- Generates feedback analysis reports

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config/default_config.json` to customize:

```json
{
  "check_interval": 30,        // Seconds between checks
  "log_lines": 500,           // Number of log lines to analyze
  "report_threshold": 3,       // Errors before generating report
  "report_cooldown": 300,      // Seconds between reports
  "docker_compose_file": "docker-compose.dev.yml",
  "container_name": "api"
}
```

## Usage

### Continuous Monitoring
Run the agent in continuous monitoring mode:
```bash
python3 main_agent.py
```

### Single Analysis
Run a single analysis cycle:
```bash
python3 main_agent.py --once
```

### With Custom Config
Use a custom configuration file:
```bash
python3 main_agent.py --config custom_config.json
```

### Verbose Output
Enable detailed logging:
```bash
python3 main_agent.py --verbose
```

## Report Generation

Reports are automatically generated when:
- Severity reaches "high" or "critical"
- Error count exceeds threshold
- Early warning patterns are detected frequently

Reports are saved to `reports/` directory with timestamps.

## Feedback Collection

After reviewing a report, provide feedback:

```bash
python3 feedback_collector.py reports/api_log_report_YYYYMMDD_HHMMSS.md
```

View feedback analysis:
```bash
python3 feedback_collector.py --analyze
```

## Architecture

```
watcher-agents/api-logs/
├── main_agent.py              # Main monitoring agent
├── feedback_collector.py      # Feedback collection system
├── analyzers/
│   ├── error_detector.py     # Error detection module
│   ├── pattern_analyzer.py   # Pattern analysis module
│   └── report_generator.py   # Report generation module
├── config/
│   └── default_config.json   # Default configuration
├── reports/                   # Generated reports
├── state/                     # Agent state persistence
└── feedback/                  # Collected feedback

```

## How It Works

1. **Log Fetching**: Retrieves recent logs from Docker container
2. **Error Detection**: Identifies errors, warnings, and critical issues
3. **Pattern Analysis**: Analyzes patterns, trends, and anomalies
4. **Severity Assessment**: Determines overall severity level
5. **Report Generation**: Creates detailed analysis report if needed
6. **State Persistence**: Saves analysis history and patterns
7. **Feedback Loop**: Collects and analyzes human feedback

## Error Categories

The agent categorizes errors into:
- **Database**: SQL, query, connection pool errors
- **Network**: Connection refused, timeouts, socket errors
- **Authentication**: Auth failures, token issues, permissions
- **Validation**: Invalid requests, format errors
- **System**: Memory, CPU, disk errors
- **Application**: General application errors

## Early Warning Patterns

The agent monitors for:
- Rate limiting issues
- Timeout patterns
- Connection problems
- Memory pressure signs
- Slow operations
- Retry patterns
- Service degradation
- Queue buildup
- Authentication issues
- Data corruption signs

## Sample Report

```markdown
# API Log Analysis Report

**Generated:** 2025-08-23 07:45:00
**Severity Level:** 🟠 HIGH

## Executive Summary
- Detected **15 errors** in recent logs
- Found **8 warnings** that may indicate emerging issues
- Identified **3 early warning patterns**
- ⚠️ **Error rate is increasing**

## Key Findings

### 🔴 Errors Detected
**HIGH Priority:**
- Line 234: Application error
- Line 567: Database connection error
...

### 📊 Pattern Analysis
**Error Clustering:**
- Lines 234-245: 12 errors clustered together

**Detected Patterns:**
- Rate Limiting: 5 occurrence(s)
- Timeouts: 8 occurrence(s)
...

## Recommendations
1. Investigate database connection pool settings
2. Consider increasing timeout values
3. Implement request throttling
...
```

## Best Practices

1. **Regular Monitoring**: Run continuously in production
2. **Quick Response**: Address high/critical issues immediately
3. **Feedback Loop**: Provide feedback to improve accuracy
4. **Pattern Learning**: Review historical patterns regularly
5. **Threshold Tuning**: Adjust thresholds based on your system

## Troubleshooting

### No logs fetched
- Ensure Docker is running
- Check docker-compose file path
- Verify container name in config

### Too many false positives
- Adjust error patterns in config
- Provide feedback on reports
- Review and update early warning patterns

### Reports not generating
- Check report_threshold setting
- Verify report_cooldown period
- Review severity calculations

## Contributing

To improve the monitoring agent:
1. Add new error patterns to `error_detector.py`
2. Enhance pattern analysis in `pattern_analyzer.py`
3. Improve report formatting in `report_generator.py`
4. Submit feedback through `feedback_collector.py`

## License

This monitoring agent is part of the deepwiki-open project.