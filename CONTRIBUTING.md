# Contributing to HappyKube

Thank you for your interest in contributing to HappyKube! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL (or SQLite for local development)
- Redis
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- A Groq API key (from [Groq Console](https://console.groq.com))

### Development Setup

```bash
# Clone the repository
git clone https://github.com/marcobellingeri/HappyKube.git
cd HappyKube

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies (including dev tools)
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your values

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest tests/ -v
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

Follow the project's architecture (Clean Architecture with 4 layers):

- **Domain** (`src/domain/`) — Pure business logic, no external dependencies
- **Infrastructure** (`src/infrastructure/`) — Database, cache, ML, auth
- **Application** (`src/application/`) — Services and DTOs
- **Presentation** (`src/presentation/`) — API routes, bot handlers, middleware

### 3. Code Quality

Before committing, ensure your code passes all checks:

```bash
# Format code
black src/ tests/ --line-length 100

# Lint
ruff check src/ tests/ --fix

# Type check
mypy src/ --ignore-missing-imports

# Security scan
bandit -r src/ -x tests/ -s B101,B104

# Run tests
pytest tests/ -v --cov=src
```

Pre-commit hooks will run these automatically on `git commit`.

### 4. Commit Messages

Use clear, descriptive commit messages:

```
feat: add monthly statistics endpoint
fix: resolve cache key collision for long texts
docs: update API documentation
refactor: extract validation logic to service layer
test: add unit tests for emotion repository
security: harden input validation for webhook endpoint
```

### 5. Submit a Pull Request

1. Push your branch to your fork
2. Open a Pull Request against `main`
3. Fill in the PR template
4. Wait for CI checks to pass
5. Request a review

## Reporting Issues

### Bug Reports

Use the [Bug Report template](https://github.com/marcobellingeri/HappyKube/issues/new?template=bug_report.yml) and include:

- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Python version

### Feature Requests

Use the [Feature Request template](https://github.com/marcobellingeri/HappyKube/issues/new?template=feature_request.yml) and describe:

- The problem you're trying to solve
- Your proposed solution
- Alternatives you've considered

### Security Issues

**Do not open a public issue for security concerns.**
Please refer to our [Security Policy](SECURITY.md) for responsible disclosure.

## Style Guide

- **Formatter**: Black (line-length: 100)
- **Linter**: Ruff with security rules (S-prefix)
- **Type Checker**: mypy (Python 3.12)
- **Tests**: pytest + pytest-asyncio
- **Docstrings**: Google style (only where logic isn't self-evident)

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
