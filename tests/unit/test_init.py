"""Unit tests for package initialization."""


def test_version_import() -> None:
    """Test that version can be imported."""
    from ukcompanies import __version__

    assert __version__ == "0.1.0"
    assert isinstance(__version__, str)


def test_package_imports() -> None:
    """Test that package can be imported."""
    import ukcompanies

    assert hasattr(ukcompanies, "__version__")
    assert ukcompanies.__version__ == "0.1.0"
