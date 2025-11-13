"""Test project structure and basic imports.

This test verifies that the project structure is set up correctly
and basic imports work as expected.
"""

import sys
from pathlib import Path

# Add project root to path for testing
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_package_import():
    """Test that the confluence2eml package can be imported."""
    import confluence2eml
    assert confluence2eml.__version__ == "0.1.0"


def test_main_module_exists():
    """Test that the main module exists and is importable."""
    # The main module should be importable
    import importlib.util
    main_module_path = project_root / "confluence2eml" / "main.py"
    assert main_module_path.exists(), "confluence2eml/main.py should exist"


def test_project_structure():
    """Test that required project files exist."""
    required_files = [
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "README.md",
        "confluence2eml/main.py",
        "confluence2eml/__init__.py",
        "confluence2eml/core/__init__.py",
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        assert full_path.exists(), f"Required file {file_path} should exist"


def test_dependencies_listed():
    """Test that core dependencies are listed in requirements.txt."""
    requirements_file = project_root / "requirements.txt"
    assert requirements_file.exists()
    
    content = requirements_file.read_text()
    required_deps = [
        "confluence-markdown-exporter",
        "markdown",
        "beautifulsoup4",
        "premailer",
        "requests",
    ]
    
    for dep in required_deps:
        assert dep in content, f"Dependency {dep} should be in requirements.txt"

