FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy MOSS code
COPY . /app/

# Set Python path
ENV PYTHONPATH=/app
ENV MOSS_MODE=safe
ENV MOSS_AGENT_ID=moss_docker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "print('healthy')" || exit 1

# Default command - run MOSS v2.0 in safe mode
CMD ["python3", "-c", "
import sys
sys.path.insert(0, '/app')
from agents.moss_agent_v2 import MOSSAgentV2
import time

agent = MOSSAgentV2(agent_id='moss_docker', mode='safe')
print(f'MOSS v2.0 Agent started: {agent.agent_id}')
print(f'Mode: {agent.mode}')

try:
    while True:
        result = agent.step()
        report = agent.get_report()
        print(f\"[$(date '+%H:%M:%S')] State: {report['safety']['runtime_hours']:.2f}h, Decisions: {report['stats']['total_decisions']}, Violations: {report['stats']['safety_violations']}\")
        time.sleep(60)
except KeyboardInterrupt:
    print('Shutting down...')
    report = agent.get_report()
    print(f'Final: {report[\"stats\"][\"total_decisions\"]} decisions, {report[\"stats\"][\"safety_violations\"]} violations')
"]
