import inspect
import pytest


def pytest_collection_modifyitems(config, items):
    """Automatically mark async tests to run with asyncio.

    This catches coroutine test functions and applies both the
    pytest-asyncio and anyio markers to be compatible with either plugin.
    """
    for item in items:
        func = getattr(item, "function", None)
        if func is not None and inspect.iscoroutinefunction(func):
            item.add_marker(pytest.mark.asyncio)
            item.add_marker(pytest.mark.anyio)
