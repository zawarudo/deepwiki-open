# API Error Checking Hook

## Overview
This hook automatically checks Docker API logs for errors, warnings, and issues. It provides quick feedback about API health during your development workflow.

## Files Created
- **Hook Script**: `.ai/claude_hooks/check-api-errors-hook.sh` - The executable bash script
- **Command**: `.ai/claude_commands/check-api-errors.md` - Detailed analysis command

## How to Use

### 1. Configure in Claude Settings
Add this hook to your Claude Code settings by configuring it for specific events:

```json
{
  "hooks": {
    "after-edit": ".ai/claude_hooks/check-api-errors-hook.sh",
    "after-command": ".ai/claude_hooks/check-api-errors-hook.sh",
    "on-error": ".ai/claude_hooks/check-api-errors-hook.sh"
  }
}
```

### 2. Available Hook Events
You can configure this hook to run on various events:

- **`after-edit`**: Checks API logs after file modifications
- **`after-command`**: Runs after executing commands
- **`on-error`**: Triggers when an error occurs
- **`before-commit`**: Checks API health before git commits
- **`periodic`**: Can be set to run periodically during sessions

### 3. What the Hook Does

The hook performs quick checks for:
- **Critical Errors**: FATAL, CRITICAL, PANIC messages
- **Regular Errors**: ERROR, Exception, Traceback patterns  
- **Warnings**: WARNING, WARN messages
- **API Issues**: Connection refused, timeouts, HTTP errors (401, 403, 500, etc.)

### 4. Output Examples

#### When errors are found:
```
🔍 Checking API logs for errors...
⚠️ ERRORS FOUND:
api-1  | ERROR - Database connection failed
api-1  | ERROR - Authentication service unavailable

⚡ WARNINGS FOUND:  
api-1  | WARNING - Rate limit approaching threshold

💡 Run '/check-api-errors' command for detailed analysis
```

#### When no issues:
```
🔍 Checking API logs for errors...
✅ No errors or warnings detected in recent API logs
```

### 5. Using with the Command

For detailed analysis, use the Claude command:
```
/check-api-errors
```

This provides:
- Full error context and stack traces
- Timestamp analysis
- Pattern detection
- Specific recommendations for fixes
- Follow-up action suggestions

### 6. Best Practices

1. **Development Workflow**: Configure as `after-edit` hook to catch issues immediately after code changes
2. **Testing**: Use as `after-command` when running tests to monitor API behavior
3. **Debugging**: Enable as `on-error` to automatically check logs when errors occur
4. **CI/CD**: Can be integrated into build pipelines for automated monitoring

### 7. Customization

You can modify the hook script to:
- Change the number of log lines checked (default: 200)
- Add custom error patterns specific to your API
- Integrate with notification systems
- Filter out known/acceptable warnings
- Add specific checks for your services

### 8. Troubleshooting

If the hook isn't working:
1. Ensure Docker is running: `docker ps`
2. Check hook permissions: `ls -la .ai/claude_hooks/check-api-errors-hook.sh`
3. Verify docker-compose file exists: `ls docker-compose.dev.yml`
4. Test manually: `./.ai/claude_hooks/check-api-errors-hook.sh`

## Integration Example

To use this in your development workflow:

1. **During Development**:
   ```bash
   # Configure hook in Claude settings
   # Edit API files
   # Hook automatically checks for errors after each edit
   ```

2. **Manual Check**:
   ```bash
   # Run the command for detailed analysis
   /check-api-errors
   ```

3. **In CI/CD**:
   ```yaml
   - name: Check API Health
     run: ./.ai/claude_hooks/check-api-errors-hook.sh
   ```