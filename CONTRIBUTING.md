# Contributing to ZenML Enterprise MLOps Template

Thank you for your interest in contributing to the ZenML Enterprise MLOps Template! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project follows the ZenML Code of Conduct. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- (Optional) Docker for containerized workflows
- (Optional) Cloud provider CLI tools (gcloud, aws, az) for cloud deployments

### Local Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/zenml-io/zenml-enterprise-mlops.git
   cd zenml-enterprise-mlops
   ```

2. **Install dependencies**

   ```bash
   make install-dev
   ```

   Or manually:

   ```bash
   pip install -e ".[dev]"
   ```

3. **Initialize ZenML**

   ```bash
   make zenml-init
   ```

4. **Install pre-commit hooks**

   ```bash
   make pre-commit
   ```

5. **Start the ZenML server (optional)**

   ```bash
   make zenml-up
   ```

## Development Workflow

### Branch Structure

- `main` - Production-ready code
- `develop` - Latest development changes (default branch for PRs)
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

### Making Changes

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

   Follow the code quality standards below.

3. **Test your changes**

   ```bash
   make test
   ```

4. **Format and lint**

   ```bash
   make format
   make lint
   ```

5. **Run type checking**

   ```bash
   make type-check
   ```

6. **Commit your changes**

   ```bash
   git add .
   git commit -m "Description of changes"
   ```

   Commit message format:
   - Use imperative mood ("Add feature" not "Added feature")
   - Keep first line under 50 characters
   - Add detailed description after blank line if needed
   - Reference issues: "Fixes #123"

7. **Push and create PR**

   ```bash
   git push origin feature/your-feature-name
   ```

   Then create a pull request on GitHub.

## Code Quality Standards

### Python Style

- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters (Black/Ruff default)
- Use descriptive variable and function names

### Code Organization

```
src/                    # ML code (data scientists)
├── pipelines/         # Pipeline definitions
├── steps/             # Individual step implementations
└── utils/             # Utility functions

governance/            # Platform code (MLOps engineers)
├── hooks/            # Pipeline hooks for governance
├── steps/            # Shared validation steps
└── stacks/           # Infrastructure as code
```

### Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports

Use `ruff` to automatically sort imports:

```bash
make format
```

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type information in docstrings for clarity
- Add inline comments for complex logic

Example:

```python
def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_estimators: int = 100,
) -> ClassifierMixin:
    """Train a Random Forest classifier.

    Args:
        X_train: Training features
        y_train: Training labels
        n_estimators: Number of trees in the forest

    Returns:
        Trained classifier model
    """
    # Implementation
```

## Testing Guidelines

### Test Organization

```
tests/
├── unit/              # Fast, isolated unit tests
├── integration/       # Integration tests with ZenML
└── conftest.py        # Shared test fixtures
```

### Writing Tests

- Test file names: `test_<module_name>.py`
- Test function names: `test_<functionality>`
- Use pytest fixtures for common setup
- Keep tests isolated and independent
- Mock external dependencies

Example:

```python
def test_data_validation_passes():
    """Test that valid data passes validation."""
    df = pd.DataFrame({'a': range(200), 'b': range(200)})
    result = validate_data_quality(df, min_rows=100)
    assert len(result) == 200

def test_data_validation_fails():
    """Test that invalid data fails validation."""
    df = pd.DataFrame({'a': range(50), 'b': range(50)})
    with pytest.raises(ValueError, match="minimum required"):
        validate_data_quality(df, min_rows=100)
```

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run with coverage
make test-cov

# Run specific test file
pytest tests/unit/test_data_validation.py

# Run specific test
pytest tests/unit/test_data_validation.py::test_data_validation_passes
```

## Documentation

### When to Update Documentation

Update documentation when you:

- Add new features or functionality
- Change existing behavior
- Add new configuration options
- Modify CLI commands or scripts
- Change architectural decisions

### Documentation Files

- `README.md` - Quick start and overview
- `docs/DEVELOPER_GUIDE.md` - For data scientists
- `docs/PLATFORM_GUIDE.md` - For MLOps engineers
- `docs/ARCHITECTURE.md` - Design decisions
- `CONTRIBUTING.md` - This file

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots for UI-related changes
- Keep documentation in sync with code

## Submitting Changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines (run `make dev-check`)
- [ ] All tests pass (run `make test`)
- [ ] New tests added for new functionality
- [ ] Documentation updated if needed
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains what and why

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
```

### Review Process

1. Submit PR to `develop` branch
2. Automated checks run (formatting, linting, tests)
3. Maintainers review code
4. Address review comments
5. PR merged when approved

### After Your PR is Merged

- Delete your feature branch
- Pull latest changes from `develop`
- Your contribution will be included in the next release!

## Common Tasks

### Adding a New Pipeline

1. Create pipeline in `src/pipelines/`
2. Import and register in `src/pipelines/__init__.py`
3. Add to `run.py` CLI options
4. Add tests in `tests/unit/`
5. Document in `docs/DEVELOPER_GUIDE.md`

### Adding a New Governance Hook

1. Create hook in `governance/hooks/`
2. Export from `governance/hooks/__init__.py`
3. Apply to pipelines that need it
4. Add tests in `tests/unit/test_hooks.py`
5. Document in `docs/PLATFORM_GUIDE.md`

### Adding a New Stack Configuration

1. Create Terraform configs in `governance/stacks/terraform/`
2. Add example tfvars file
3. Update README in that directory
4. Document in `docs/PLATFORM_GUIDE.md`

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Feature Requests**: Open a GitHub Issue with "enhancement" label
- **Security Issues**: Email security@zenml.io (do not open public issues)

## Resources

- [ZenML Documentation](https://docs.zenml.io)
- [ZenML GitHub](https://github.com/zenml-io/zenml)
- [ZenML Slack Community](https://zenml.io/slack-invite)

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to making MLOps better for everyone! 🚀
