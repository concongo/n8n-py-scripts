"""Shared test utilities."""

import importlib.util
from functools import wraps
from pathlib import Path

import pytest


def with_n8n_items(
    module_fixture_name: str, items_fixture_name: str = "n8n_items"
):
    """Decorator that injects n8n items into a module before running a test.

    Args:
        module_fixture_name: Name of the fixture containing the loaded module
        items_fixture_name: Name of the fixture containing the n8n items (default: "n8n_items")

    Usage:
        @with_n8n_items(module_fixture_name="extract_filename_module")
        def test_something(self, extract_filename_module):
            result = extract_filename_module.extract_filename()
            assert result["filename"].endswith(".csv")
    """

    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            # Get the pytest request object to access fixtures
            request = kwargs.get("request")
            if request is None:
                raise ValueError("Decorator requires pytest 'request' fixture")

            # Get the module and items fixtures
            module = request.getfixturevalue(module_fixture_name)
            items = request.getfixturevalue(items_fixture_name)

            # Inject items into module
            module._items = items

            # Call the original test function
            return test_func(*args, **kwargs)

        # Mark the wrapper to request the 'request' fixture
        wrapper = pytest.mark.usefixtures("request")(wrapper)
        return wrapper

    return decorator


def load_module(
    module_name: str,
    module_path: Path | None = None,
    src_relative_path: str | None = None,
    test_file: Path | None = None,
):
    """Load a Python module dynamically from a file path.

    Args:
        module_name: The name to assign to the loaded module
        module_path: Absolute path to the .py file to load (mutually exclusive with src_relative_path)
        src_relative_path: Path relative to src/ directory (e.g., "portfolio_analysis/upload_position_file")
        test_file: Path to the test file (required when using src_relative_path, defaults to None)

    Returns:
        The loaded module object

    Examples:
        # Load from absolute path
        module = load_module(
            "extract_filename",
            module_path=Path("src/portfolio_analysis/upload_position_file/extract_filename.py")
        )

        # Load from src-relative path
        module = load_module(
            "extract_filename",
            src_relative_path="portfolio_analysis/upload_position_file",
            test_file=Path(__file__)
        )
    """
    if module_path is None and src_relative_path is None:
        raise ValueError(
            "Either module_path or src_relative_path must be provided"
        )

    if module_path is not None and src_relative_path is not None:
        raise ValueError(
            "Only one of module_path or src_relative_path can be provided"
        )

    if src_relative_path is not None:
        if test_file is None:
            raise ValueError(
                "test_file must be provided when using src_relative_path"
            )
        module_path = (
            test_file.parents[1]
            / "src"
            / src_relative_path
            / f"{module_name}.py"
        )

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
