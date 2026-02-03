# Repository Guidelines

## Project Structure & Module Organization

- `src/`: ML code. Pipelines in `src/pipelines/`, steps in `src/steps/`, helpers in `src/utils/`.
- `governance/`: platform code (hooks, validation steps, Docker settings, Terraform under `governance/stacks/terraform/`).
- `configs/`: environment YAMLs like `configs/local.yaml`, `configs/staging.yaml`, `configs/production.yaml`.
- `scripts/`: promotion/rollback/snapshot utilities.
- `tests/`: pytest suite. Supporting content lives in `docs/`, `demo/`, `notebooks/`.

## Build, Test, and Development Commands

- `make install-dev`: install dev dependencies and pre-commit hooks.
- `make setup`: full local setup (`install-dev` + `zenml-init`).
- `make run-training`: run the training pipeline locally.
- `make format` / `make lint` / `make type-check`: Ruff formatting/linting and mypy checks.
- `make test` / `make test-cov`: run tests, optionally with coverage (HTML report in `htmlcov/`).

## Coding Style & Naming Conventions

- Python style: PEP 8, 4-space indentation, max line length 88.
- Use type hints on all functions/returns; Google-style docstrings for public APIs.
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, constants in `UPPER_SNAKE_CASE`.
- Imports: standard library, third-party, then local; Ruff sorts via `make format`.

## Testing Guidelines

- Framework: pytest (see `tests/`).
- File names: `test_<module>.py`; test functions `test_<behavior>`.
- Keep tests isolated; use fixtures from `tests/conftest.py`.
- Run targeted tests with `pytest tests/test_steps.py::test_<name>` when iterating.

## Rules of Thumb

- Keep governance in `governance/` and ML logic in `src/`; avoid mixing concerns.
- Avoid pipeline-level conditionals; put data-dependent branching inside steps.

## Core Demo Files (Change Deliberately)

- `src/pipelines/training.py`
- `src/pipelines/champion_challenger.py`
- `src/pipelines/realtime_inference.py`
- `src/pipelines/import_model.py`
- `scripts/promote_cross_workspace.py`
- `.github/workflows/promote-to-production.yml`

## Commit & Pull Request Guidelines

- Branches: `develop` is the default PR target; use `feature/*`, `fix/*`, or `docs/*`.
- Commit messages: imperative mood, first line < 50 chars, add a blank line + body if needed, and reference issues (e.g., `Fixes #123`).
- Before opening a PR: run `make dev-check` and `make test`.
- PRs should explain what and why, link issues, and follow the repository’s PR template.

## Configuration & Safety Notes

- Environment behavior is driven by `configs/*.yaml`; keep changes explicit and environment-specific.
- Do not commit secrets or cloud credentials. Use local tooling or environment variables for sensitive values.
