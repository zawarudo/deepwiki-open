---
command: check-api-errors
description: Check Docker API logs for errors and warnings
---

You are a senior expert developer with a PhD in Computer Science analyzing API logs for errors and warnings.

<scratchpad>
When this command is invoked, I need to:
1. Run the docker-compose command to fetch recent API logs
2. Analyze the output for errors, warnings, and issues
3. Provide insights about any problems found
4. Suggest potential solutions if errors are detected
</scratchpad>

Execute the following command and analyze the output:
```bash
docker-compose -f docker-compose.dev.yml logs --tail=200 api | cat
```

After running the command, carefully analyze the logs for:
- Error messages (look for ERROR, Error, error, CRITICAL, Fatal, etc.)
- Warning messages (look for WARNING, Warning, WARN, warn, etc.)
- Stack traces or exception details
- Failed requests or connections
- Database connection issues
- Configuration problems
- Authentication/authorization failures
- Resource exhaustion (memory, disk, connections)
- Timeout issues
- Any unusual patterns or repeated errors

<answer>
Provide a structured analysis:
1. **Summary**: Brief overview of the log health
2. **Errors Found**: List any errors with their timestamps and details
3. **Warnings Found**: List any warnings with their context
4. **Potential Issues**: Highlight patterns that might indicate problems
5. **Recommendations**: Suggest fixes for any issues found
6. **Next Steps**: Recommend follow-up actions if needed
</answer>

If no errors or warnings are found, report that the API logs appear healthy and mention any notable normal operations observed.