"""Shared test utilities."""

from functools import wraps

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
