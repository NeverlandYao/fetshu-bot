# List all recipes
default:
    just -l

# Install dependencies
[group('setup')]
install:
    uv sync

# Install dev dependencies
[group('setup')]
install-dev:
    uv sync --all-extras

# Run the FastAPI development server
[group('dev')]
dev:
    uv run python -m src.bootstrap --reload

# Run the application (production mode)
[group('dev')]
run:
    uv run python -m src.bootstrap --no-reload

# Run bootstrap entry point (same as dev)
[group('dev')]
start:
    uv run python -m src.bootstrap

# Format code with ruff
[group('lint')]
fmt:
    uv run ruff format .

# Check code formatting without making changes
[group('lint')]
fmt-check:
    uv run ruff format --check .

# Lint code with ruff
[group('lint')]
lint:
    uv run ruff check .

# Lint and auto-fix issues
[group('lint')]
lint-fix:
    uv run ruff check --fix .

# Run all linting checks (format + lint)
[group('lint')]
check: fmt-check lint

# Format and fix all issues
[group('lint')]
fix: fmt lint-fix

# Run tests (when implemented)
[group('test')]
test:
    uv run pytest

# Run tests with coverage (when implemented)
[group('test')]
test-cov:
    uv run pytest --cov=src --cov-report=html --cov-report=term

# Clean up generated files
[group('clean')]
clean:
    rm -rf .ruff_cache
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf .coverage
    rm -rf dist
    rm -rf *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Update dependencies
[group('setup')]
update:
    uv lock --upgrade

# Show outdated dependencies
[group('setup')]
outdated:
    uv pip list --outdated
