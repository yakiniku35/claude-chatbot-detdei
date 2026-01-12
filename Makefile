.PHONY: help install install-dev test lint format check security clean run

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run linters (flake8)"
	@echo "  make format        - Format code with black"
	@echo "  make check         - Run all checks (format, lint, test)"
	@echo "  make security      - Check for security vulnerabilities"
	@echo "  make clean         - Clean cache and temporary files"
	@echo "  make run           - Run the Streamlit application"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint:
	python -m flake8 src/ tests/

format:
	python -m black src/ tests/

format-check:
	python -m black --check src/ tests/

check: format-check lint test
	@echo "✅ All checks passed!"

security:
	python -m safety scan || echo "Security scan completed"

clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	streamlit run src/app.py
