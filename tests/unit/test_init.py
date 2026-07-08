"""Unit tests for package initialization."""

import re


def test_version_import() -> None:
    """Test that version can be imported."""
    from ukcompanies import __version__

    assert isinstance(__version__, str)
    assert re.match(r"^\d+\.\d+\.\d+", __version__), __version__


def test_package_imports() -> None:
    """Test that package can be imported."""
    import ukcompanies

    assert hasattr(ukcompanies, "__version__")
    assert re.match(r"^\d+\.\d+\.\d+", ukcompanies.__version__)
