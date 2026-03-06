FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install numpy flask requests psutil

# Copy MOSS code
COPY . /app/

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python3", "-c", "
import sys
sys.path.insert(0, '/app')
from moss.agents.moss_agent import MOSSAgent
import time
agent = MOSSAgent(agent_id='moss_docker_001')
print(f'MOSS Agent started: {agent.agent_id}')
try:
    while True:
        result = agent.step()
        report = agent.get_report()
        state = report['allocator_stats']['current_state']
        decisions = report['stats']['total_decisions']
        print(f'State: {state}, Decisions: {decisions}')
        time.sleep(60)
except KeyboardInterrupt:
    print('Shutting down...')
"]
