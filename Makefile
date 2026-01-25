.PHONY: help install install-dev setup clean lint format type-check pre-commit run-training run-batch-inference

# Use uv if available, fallback to pip
UV := $(shell command -v uv 2> /dev/null)
ifdef UV
	PIP := uv pip
	SYNC := uv sync
	RUN := uv run
else
	PIP := pip
	SYNC := pip install -e ".[dev]"
	RUN :=
endif

# Default target
help:
	@echo "ZenML Enterprise MLOps Template - Available Commands"
	@echo ""
	@echo "Powered by the Astral stack (uv, ruff)"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install development dependencies"
	@echo "  make setup            Complete local development setup"
	@echo "  make sync             Sync dependencies from lockfile (uv)"
	@echo ""
	@echo "Code Quality (Astral stack):"
	@echo "  make format           Format code with ruff"
	@echo "  make lint             Check code quality with ruff"
	@echo "  make lint-fix         Fix linting issues automatically"
	@echo "  make type-check       Run mypy type checking"
	@echo "  make check            Run all checks (format, lint, type-check)"
	@echo "  make pre-commit       Install pre-commit hooks"
	@echo ""
	@echo "Pipeline Operations:"
	@echo "  make run-training     Run training pipeline locally"
	@echo "  make run-batch        Run batch inference pipeline"
	@echo "  make run-compare      Run champion/challenger comparison"
	@echo "  make build-snapshot   Build pipeline snapshot for deployment"
	@echo "  make deploy-service   Deploy real-time inference service (local)"
	@echo ""
	@echo "ZenML Operations:"
	@echo "  make zenml-init       Initialize ZenML"
	@echo "  make zenml-up         Start ZenML server"
	@echo "  make zenml-down       Stop ZenML server"
	@echo "  make zenml-clean      Clean ZenML local state"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts and caches"
	@echo "  make clean-all        Remove all generated files (including ZenML state)"

# Setup and Installation
install:
ifdef UV
	uv pip install -e .
else
	pip install -e .
endif

install-dev:
ifdef UV
	uv pip install -e ".[dev]"
else
	pip install -e ".[dev]"
endif
	$(MAKE) pre-commit

# Sync from lockfile (uv only)
sync:
ifdef UV
	uv sync --all-extras
else
	@echo "uv not installed. Using pip install instead."
	pip install -e ".[dev]"
endif

setup: install-dev zenml-init
	@echo "Development environment ready!"
	@echo "Run 'make zenml-up' to start the ZenML server"

# Code Quality - Astral stack
format:
	$(RUN) ruff format .
	$(RUN) ruff check --fix .

lint:
	$(RUN) ruff check .

lint-fix:
	$(RUN) ruff check --fix --unsafe-fixes .

type-check:
	$(RUN) mypy src/ governance/ --ignore-missing-imports

# Run all checks
check: format lint type-check
	@echo "All checks passed!"

pre-commit:
ifdef UV
	uv tool install pre-commit
	pre-commit install --install-hooks
else
	pip install pre-commit
	pre-commit install --install-hooks
endif
	@echo "Pre-commit hooks installed"

# Update pre-commit hooks to latest versions
pre-commit-update:
	pre-commit autoupdate

# Pipeline Operations
run-training:
	$(RUN) python run.py --pipeline training

run-batch:
	$(RUN) python run.py --pipeline batch_inference

run-compare:
	$(RUN) python run.py --pipeline champion_challenger

deploy-service:
	@echo "Deploying real-time inference service..."
	$(RUN) zenml pipeline deploy src.pipelines.realtime_inference.inference_service --name readmission-api

build-snapshot:
	@echo "Building pipeline snapshot..."
	$(RUN) python scripts/build_snapshot.py --environment staging --stack local

# ZenML Operations
zenml-init:
	$(RUN) zenml init

zenml-up:
	$(RUN) zenml up

zenml-down:
	$(RUN) zenml down

zenml-clean:
	rm -rf .zen
	rm -f zenml_local.db
	@echo "Local ZenML state cleaned. Run 'make zenml-init' to reinitialize."

# Stack Management
stack-list:
	$(RUN) zenml stack list

stack-describe:
	$(RUN) zenml stack describe

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "Build artifacts cleaned"

clean-all: clean zenml-clean
	rm -rf mlruns/ mlartifacts/
	@echo "All generated files cleaned"

# Documentation
docs:
	@echo "Documentation available in docs/"
	@echo "  - DEVELOPER_GUIDE.md - For data scientists"
	@echo "  - PLATFORM_GUIDE.md  - For MLOps engineers"
	@echo "  - ARCHITECTURE.md    - Design decisions"

# Development workflow
dev-check: format lint type-check
	@echo "All checks passed!"

# CI simulation (run this before pushing)
ci-check: check
	@echo "CI checks passed! Safe to push."

# Lock dependencies (uv only)
lock:
ifdef UV
	uv lock
else
	@echo "uv not installed. Lockfiles require uv."
	@echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
endif

# Show outdated dependencies
outdated:
ifdef UV
	uv pip list --outdated
else
	pip list --outdated
endif

# Upgrade all dependencies
upgrade:
ifdef UV
	uv lock --upgrade
	uv sync
else
	pip install --upgrade -e ".[dev]"
endif
