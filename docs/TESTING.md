# Testing and Quality Assurance

This document describes the testing and quality assurance procedures for the DEI Policy Chatbot.

## Quick Start

Run all quality checks:
```bash
make check
```

Or run checks individually:
```bash
make format-check  # Check code formatting
make lint          # Run linters
make test          # Run tests with coverage
make security      # Check for security vulnerabilities
```

## Development Dependencies

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

Development dependencies include:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pylint` - Code quality checker
- `mypy` - Static type checker
- `black` - Code formatter
- `flake8` - Style guide enforcement
- `safety` - Security vulnerability scanner

## Testing

### Running Tests

Run all tests:
```bash
python -m pytest tests/ -v
```

Run tests with coverage:
```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Test Structure

Tests are located in the `tests/` directory:
- `tests/test_app.py` - Main application tests

Test coverage includes:
- Language detection (Chinese, Japanese, Korean, English)
- Language instruction generation
- DEI analysis request detection
- Web search trigger detection
- Configuration loading

## Code Quality

### Code Formatting

Format code with Black:
```bash
python -m black src/ tests/
```

Check formatting without making changes:
```bash
python -m black --check src/ tests/
```

Configuration: `pyproject.toml` (line length: 100)

### Linting

Run Flake8:
```bash
python -m flake8 src/ tests/
```

Configuration: `.flake8`

### Type Checking

Run mypy:
```bash
python -m mypy src/
```

Configuration: `pyproject.toml`

## Security

### Dependency Vulnerability Scanning

Check for known vulnerabilities:
```bash
python -m safety scan
```

### Security Best Practices

1. Keep dependencies up to date
2. Review security advisories regularly
3. Use environment variables for sensitive data
4. Never commit secrets to the repository

## Continuous Integration

GitHub Actions automatically runs quality checks on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

The CI pipeline includes:
1. Code formatting check (Black)
2. Linting (Flake8)
3. Tests with coverage (pytest)
4. Security vulnerability scanning (safety)

## Pre-commit Hooks (Optional)

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 25.12.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 7.3.0
    hooks:
      - id: flake8
```

## Troubleshooting

### Import Errors in Tests

If you encounter import errors, ensure the `src/` directory is in the Python path:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```

### Coverage Not Generated

Ensure pytest-cov is installed:
```bash
pip install pytest-cov
```

### Flake8 Configuration Errors

Check `.flake8` for syntax errors. Error codes should match the pattern `^[A-Z]{1,3}[0-9]{0,3}$`.

## Contributing

When contributing code:
1. Write tests for new features
2. Ensure all tests pass
3. Format code with Black
4. Fix linting errors
5. Update documentation as needed
6. Run `make check` before submitting a PR

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Black documentation](https://black.readthedocs.io/)
- [Flake8 documentation](https://flake8.pycqa.org/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
