"""Integration tests for package installation and functionality."""

import subprocess
import sys
import tempfile
from pathlib import Path


def test_package_build_succeeds():
    """Test that package can be built without errors."""
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel"],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"

    # Verify wheel file exists
    dist_dir = Path(__file__).parent.parent.parent / "dist"
    wheel_files = list(dist_dir.glob("*.whl"))
    assert len(wheel_files) > 0, "No wheel file found after build"


def test_cli_entry_point_after_installation():
    """Test that CLI works after package installation."""
    # Test CLI help command works
    result = subprocess.run(
        [sys.executable, "-m", "ukcompanies", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"CLI help failed: {result.stderr}"
    assert "UK Companies House API CLI" in result.stdout
    assert "search" in result.stdout


def test_package_imports_work():
    """Test that package imports work correctly."""
    result = subprocess.run(
        [sys.executable, "-c", "import ukcompanies; print(ukcompanies.__version__)"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert "0.1.0" in result.stdout


def test_fresh_venv_installation():
    """Test installation in a fresh virtual environment."""
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "test_venv"

        # Create virtual environment
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Venv creation failed: {result.stderr}"

        # Get python executable in venv
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"

        # Install package from built wheel
        dist_dir = Path(__file__).parent.parent.parent / "dist"
        wheel_files = list(dist_dir.glob("*.whl"))
        assert len(wheel_files) > 0, "No wheel file found for installation test"

        result = subprocess.run(
            [str(python_exe), "-m", "pip", "install", str(wheel_files[0])],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Package installation failed: {result.stderr}"

        # Test import works
        result = subprocess.run(
            [str(python_exe), "-c", "import ukcompanies; print('Import successful')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Import test failed: {result.stderr}"
        assert "Import successful" in result.stdout

        # Test CLI works
        result = subprocess.run(
            [str(python_exe), "-m", "ukcompanies", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"CLI test failed: {result.stderr}"
        assert "UK Companies House API CLI" in result.stdout
