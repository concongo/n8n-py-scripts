.PHONY: help install format lint check test test-verbose clean all

# Default target
help:
	@echo "Available targets:"
	@echo "  make install       - Install dependencies using uv"
	@echo "  make format        - Format code with ruff"
	@echo "  make lint          - Lint code with ruff (check only)"
	@echo "  make check         - Run lint + tests (CI pipeline)"
	@echo "  make test          - Run tests with pytest"
	@echo "  make test-verbose  - Run tests with verbose output"
	@echo "  make clean         - Remove cache and build artifacts"
	@echo "  make all           - Format, lint, and test"

# Install dependencies
install:
	uv sync

# Format code with ruff
format:
	uv run ruff format src/ test/
	uv run ruff check --fix src/ test/

# Lint code with ruff (check only, no fixes)
lint:
	uv run ruff check src/ test/
	uv run ruff format --check src/ test/

# Run tests
test:
	uv run pytest

# Run tests with verbose output
test-verbose:
	uv run pytest -v

# Check everything (for CI)
check: lint test
	@echo "✓ All checks passed!"

# Clean cache and build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned cache and build artifacts"

# Run format, lint, and test
all: format lint test
	@echo "✓ Format, lint, and tests completed successfully!"
