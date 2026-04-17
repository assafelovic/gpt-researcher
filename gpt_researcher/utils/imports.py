"""Helpers for validating optional runtime dependencies."""

import importlib.util


def check_pkg(import_name: str, install_name: str | None = None) -> None:
    """Raise a helpful ImportError when an optional dependency is missing."""
    if importlib.util.find_spec(import_name):
        return

    package_name = install_name or import_name.replace("_", "-")
    raise ImportError(
        f"Required package '{package_name}' is not installed. "
        f"Please install it with: pip install -U {package_name}"
    )
