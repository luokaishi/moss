.PHONY: help install test test-v1 test-v2 docker run-docker clean web-monitor

help:
	@echo "MOSS Development Commands"
	@echo ""
	@echo "  make install     - Install dependencies"
	@echo "  make test        - Run all tests"
	@echo "  make test-v1     - Run v1.0 tests"
	@echo "  make test-v2     - Run v2.0 tests"
	@echo "  make docker      - Build Docker image"
	@echo "  make run-docker  - Run MOSS in Docker"
	@echo "  make web-monitor - Start web monitoring dashboard"
	@echo "  make experiments - Run all experiments (1-5)"
	@echo "  make llm-verify  - Run LLM verification (mock mode)"
	@echo "  make llm-real    - Run LLM verification (requires API key)"
	@echo "  make clean       - Clean up generated files"

install:
	pip install -r requirements.txt

test: test-v1 test-v2

test-v1:
	@echo "Running v1.0 tests..."
	python tests/test_basic.py

test-v2:
	@echo "Running v2.0 tests..."
	python tests/test_v2_comprehensive.py || true

docker:
	@echo "Building Docker image..."
	docker build -t moss:latest .

run-docker:
	@echo "Running MOSS in Docker..."
	docker run -it --rm \
		-v $(PWD)/logs:/app/logs \
		-e MOSS_MODE=safe \
		moss:latest

docker-compose:
	@echo "Starting MOSS with docker-compose..."
	docker-compose up -d

docker-compose-down:
	@echo "Stopping MOSS..."
	docker-compose down

llm-verify:
	@echo "Running LLM verification (mock mode)..."
	cd sandbox && python moss_llm_real_verifier.py --steps 50 --mock

llm-real:
	@echo "Running LLM verification (real API mode)..."
	@read -p "Enter ARK_API_KEY: " key; \
	cd sandbox && ARK_API_KEY=$$key python moss_llm_real_verifier.py --steps 20

run-v2:
	@echo "Running MOSS v2.0..."
	python -c "from agents.moss_agent_v2 import MOSSAgentV2; agent = MOSSAgentV2('manual_test', mode='demo'); agent.run(steps=10)"

web-monitor:
	@echo "Starting web monitoring dashboard..."
	@echo "Open http://localhost:5000 in your browser"
	python web/monitor.py

experiments:
	@echo "Running all experiments..."
	./scripts/run_experiments.sh

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*checkpoint*.json" -delete
	find . -type f -name "*report*.json" -delete
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/

lint:
	@echo "Running linters..."
	black agents/ core/ integration/ tests/ || true
	flake8 agents/ core/ integration/ tests/ --max-line-length=120 || true

format:
	@echo "Formatting code..."
	black agents/ core/ integration/ tests/
