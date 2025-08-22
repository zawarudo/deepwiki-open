FROM python:3.9-slim

WORKDIR /app

# Copy the monitoring scripts
COPY analyzers/ ./analyzers/
COPY *.py ./
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p reports state feedback logs

# No additional dependencies needed - using stdlib only

# Default command runs monitoring
CMD ["python3", "main_agent.py"]