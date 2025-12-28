# n8n-py-scripts

Python scripts for n8n workflows with proper testing and development environment.

## Overview

This repository contains Python scripts used in n8n Code Steps, organized by project and workflow. The project uses `uv` for dependency management and includes the same Python packages available in the custom n8n Docker runner.

## Project Structure

```
n8n-py-scripts/
├── src/                          # Source code
│   └── {project_name}/          # Project folder
│       └── {workflow_name}/     # Workflow folder
│           └── {step_name}.py   # Step implementation
├── test/                        # Tests
│   ├── fixtures/                # Test fixtures (JSON inputs)
│   │   └── {project_name}/
│   │       └── {workflow_name}/
│   │           ├── {step}_input.json
│   │           └── {step}_expected_output.json
│   └── test_{workflow_name}.py  # Test files
├── pyproject.toml               # Project configuration
└── pytest.ini                   # Pytest configuration
```

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd n8n-py-scripts
```

2. Install dependencies:
```bash
uv sync
```

This will create a virtual environment in `.venv` and install all dependencies.

## Available Packages

The following packages are available (matching the n8n custom Docker runner):

- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing
- **pandas-ta-classic** - Technical analysis for pandas
- **requests** - HTTP library
- **openpyxl** - Excel file handling

## Development

### Creating a New Workflow

1. Create the project and workflow structure:
```bash
mkdir -p src/{project_name}/{workflow_name}
touch src/{project_name}/__init__.py
touch src/{project_name}/{workflow_name}/__init__.py
```

2. Create step files following the naming convention:
```bash
# Example: src/my_project/data_pipeline/step1_fetch_data.py
```

3. Create corresponding test fixtures:
```bash
mkdir -p test/fixtures/{project_name}/{workflow_name}
# Create JSON fixtures for input and expected output
```

4. Write tests in `test/test_{workflow_name}.py`

### Code Quality

The project uses **ruff** for code formatting and linting with best practices configured.

Format code:
```bash
make format
```

Check code style (without making changes):
```bash
make lint
```

Run all checks (lint + tests):
```bash
make check
```

### Running Tests

Run all tests:
```bash
make test
# or directly: uv run pytest
```

Run tests with verbose output:
```bash
make test-verbose
# or directly: uv run pytest -v
```

Run specific test file:
```bash
uv run pytest test/test_example_workflow.py
```

### Makefile Targets

The project includes a Makefile for common development tasks:

```bash
make help          # Show all available targets
make install       # Install dependencies
make format        # Format code with ruff
make lint          # Check code style (no changes)
make test          # Run tests
make test-verbose  # Run tests with verbose output
make check         # Run lint + tests (for CI)
make clean         # Remove cache and build artifacts
make all           # Format, lint, and test
```

### Writing Tests

Tests use JSON fixtures to simulate n8n input data:

```python
import json
from pathlib import Path
import pytest

@pytest.fixture
def step1_input():
    fixtures_dir = Path(__file__).parent / "fixtures" / "project" / "workflow"
    with open(fixtures_dir / "step1_input.json") as f:
        return json.load(f)

def test_process(step1_input):
    from src.project.workflow.step1_process import process
    result = process(step1_input)
    assert result["status"] == "success"
```

## Example

See `src/example_project/example_workflow/` for a complete example showing:
- Data processing with pandas
- Step chaining
- Error handling
- Test fixtures and test cases

## Using in n8n

To use a script in n8n:

1. Copy the function code from `src/{project}/{workflow}/{step}.py`
2. In n8n, add a "Code" node and select "Python"
3. Paste the function and add the execution logic:

```python
# Your function from the src file
def process(data: dict) -> dict:
    # ... your code
    pass

# n8n execution
result = process({"items": $input.all()})
return result
```

## Contributing

1. Create a new branch for your workflow
2. Follow the project structure convention
3. Write tests with fixtures
4. Ensure all tests pass before committing

## License

[Your License Here]
