"""
tests/test_environment.py - Environment Testing (Phase 0.14)

Purpose:
    Verify that the project development environment is fully functional
    and ready for implementation work (core WBS Phases 1-15).

Scope:
    This test suite validates ONLY the development environment:
      1. Python runtime version compliance
      2. Required library imports and version correctness
      3. Centralized project configuration (config.py) path resolution
      4. Approved project directory structure existence
      5. Source code module importability (Phase 0.13 foundation)
      6. Scope protection - no unauthorized packages installed

    This does NOT test project data, RFM calculations, visualization,
    or any core-WBS functionality. Those belong to later phases
    (core WBS Phases 3-15) and are intentionally out of scope here.

Framework:
    Python built-in unittest suites, executed through pytest - the single
    approved development/test dependency declared in requirements-dev.txt.

Run from project root:
    .venv/Scripts/python.exe -m pytest tests -q
"""

import importlib
import pathlib
import sys
import types
import unittest

# ---------------------------------------------------------------------------
# Project root - added to sys.path so config and src are importable
# regardless of how the test is invoked.
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Approved environment specifications
# (Source: README.md - Phase 0 decisions)
# ---------------------------------------------------------------------------

# Python version: 3.12.10 (Phase 0.4)
EXPECTED_PYTHON = (3, 12, 10)

# Required libraries: {import_name: (pip_name, expected_version)}
# (Source: README.md Section 10 / requirements.txt)
REQUIRED_LIBRARIES = {
    "pandas": ("pandas", "3.0.5"),
    "numpy": ("numpy", "2.5.2"),
    "scipy": ("scipy", "1.18.0"),
    "sklearn": ("scikit-learn", "1.9.0"),
    "matplotlib": ("matplotlib", "3.11.1"),
    "seaborn": ("seaborn", "0.13.2"),
}

# Approved directory structure (Source: README.md Section 6 / config.py)
APPROVED_DIRECTORIES = [
    "data",
    "data/raw",
    "data/processed",
    "src",
    "notebooks",
    "outputs",
    "outputs/charts",
    "outputs/tables",
    "outputs/reports",
    "tests",
    "docs",
]

# Root-level Python files (Source: README.md Section 6 / Phase 0.13)
APPROVED_ROOT_FILES = ["config.py", "main.py", "requirements.txt"]

# Source modules created in Phase 0.13 (Python Source Code Foundation)
SRC_MODULES = [
    "data_loading",
    "data_cleaning",
    "rfm_analysis",
    "statistics_analysis",
    "segmentation",
    "visualization",
]

# Packages explicitly NOT approved for the project - must not be installed.
# (Source: README.md Section 10: "Optional Libraries: NOT INSTALLED")
#
# Sole exception: the pytest runner, authorized ONLY while requirements-dev.txt
# exists at the repo root and explicitly declares "pytest". That exception is
# checked per-run below and NEVER extends to anything in this blocklist.
UNAUTHORIZED_PACKAGES = [
    "jupyter",
    "notebook",
    "ipykernel",
    "bs4",
    "openpyxl",
]


def _runner_exception_active():
    """True ONLY if requirements-dev.txt exists AND declares ``pytest``.

    The declaration must appear as a non-comment requirement line whose
    distribution name equals "pytest" (e.g. ``pytest==9.1.1``).
    """
    path = PROJECT_ROOT / "requirements-dev.txt"
    if not path.is_file():
        return False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name = line.partition("==")[0].strip().lower()
        if name == "pytest":
            return True
    return False

# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestPythonRuntime(unittest.TestCase):
    """Verify the Python runtime matches the approved version."""

    def test_python_version(self):
        """Python must be exactly 3.12.10 as approved in Phase 0.4."""
        actual = sys.version_info[:3]
        self.assertEqual(
            actual,
            EXPECTED_PYTHON,
            f"Expected Python {EXPECTED_PYTHON[0]}.{EXPECTED_PYTHON[1]}"
            f".{EXPECTED_PYTHON[2]}, got {actual[0]}.{actual[1]}.{actual[2]}",
        )

    def test_running_from_venv(self):
        """Tests must execute inside the project .venv."""
        venv_python = (PROJECT_ROOT / ".venv" / "Scripts" / "python.exe").resolve()
        self.assertEqual(
            pathlib.Path(sys.executable).resolve(),
            venv_python,
            f"sys.executable ({sys.executable}) is not the project .venv Python",
        )


class TestRequiredLibraries(unittest.TestCase):
    """Verify all six required libraries import with correct versions."""

    def test_libraries_import_and_version(self):
        """Each required library must import with its approved version."""
        for import_name, (pip_name, expected_version) in REQUIRED_LIBRARIES.items():
            with self.subTest(library=pip_name):
                module = importlib.import_module(import_name)
                actual_version = getattr(module, "__version__", None)
                self.assertIsNotNone(
                    actual_version,
                    f"{pip_name} has no __version__ attribute",
                )
                self.assertEqual(
                    actual_version,
                    expected_version,
                    f"{pip_name} version mismatch: expected {expected_version}, "
                    f"got {actual_version}",
                )

    def test_libraries_coexist_in_single_process(self):
        """All six libraries must coexist in a single Python process."""
        for import_name, (pip_name, _) in REQUIRED_LIBRARIES.items():
            with self.subTest(library=pip_name):
                importlib.import_module(import_name)
                self.assertIn(import_name, sys.modules)


class TestProjectConfiguration(unittest.TestCase):
    """Verify centralized project configuration (config.py) is correct."""

    def test_config_importable(self):
        """config.py must be importable from the project root."""
        import config
        self.assertTrue(hasattr(config, "PROJECT_ROOT"))

    def test_project_root_matches(self):
        """config.PROJECT_ROOT must point to the actual project root."""
        import config
        self.assertEqual(config.PROJECT_ROOT, PROJECT_ROOT)

    def test_config_has_all_paths(self):
        """config.py must define all approved path constants."""
        import config
        expected_attrs = [
            "DATA_DIR",
            "RAW_DATA_DIR",
            "PROCESSED_DATA_DIR",
            "SRC_DIR",
            "NOTEBOOKS_DIR",
            "OUTPUTS_DIR",
            "CHARTS_DIR",
            "TABLES_DIR",
            "REPORTS_DIR",
            "TESTS_DIR",
            "DOCS_DIR",
        ]
        for attr in expected_attrs:
            with self.subTest(attr=attr):
                self.assertTrue(
                    hasattr(config, attr),
                    f"config.py is missing expected attribute: {attr}",
                )

    def test_config_paths_exist_on_disk(self):
        """All config-defined directories must exist on disk."""
        import config
        path_attrs = [
            "RAW_DATA_DIR",
            "PROCESSED_DATA_DIR",
            "SRC_DIR",
            "NOTEBOOKS_DIR",
            "OUTPUTS_DIR",
            "CHARTS_DIR",
            "TABLES_DIR",
            "REPORTS_DIR",
            "TESTS_DIR",
            "DOCS_DIR",
        ]
        for attr in path_attrs:
            with self.subTest(attr=attr):
                path = getattr(config, attr)
                self.assertTrue(
                    path.exists(),
                    f"{attr} path does not exist on disk: {path}",
                )

    def test_config_no_dataset_attributes(self):
        """config.py must NOT define dataset attributes (Phase 3 deferred)."""
        import config
        forbidden = ["RAW_DATA_FILE", "DATASET_NAME", "DATASET_PATH"]
        for attr in forbidden:
            with self.subTest(attr=attr):
                self.assertFalse(
                    hasattr(config, attr),
                    f"config.py defines {attr} — dataset selection belongs to "
                    f"Phase 3 and must not be set here",
                )

    def test_config_only_contains_path_constants(self):
        """config.py must contain only path constants — no business logic."""
        import config
        for attr_name in dir(config):
            if attr_name.startswith("_"):
                continue
            attr_value = getattr(config, attr_name)
            if isinstance(attr_value, (pathlib.PurePath, types.ModuleType)):
                continue
            self.fail(
                f"config.py contains non-path attribute '{attr_name}' = "
                f"{attr_value!r}",
            )


class TestProjectStructure(unittest.TestCase):
    """Verify the approved project directory structure exists."""

    def test_directories_exist(self):
        """All approved directories must exist."""
        for dir_name in APPROVED_DIRECTORIES:
            with self.subTest(directory=dir_name):
                dir_path = PROJECT_ROOT / dir_name
                self.assertTrue(
                    dir_path.is_dir(),
                    f"Expected directory does not exist: {dir_path}",
                )

    def test_root_files_exist(self):
        """All approved root-level files must exist."""
        for file_name in APPROVED_ROOT_FILES:
            with self.subTest(file=file_name):
                file_path = PROJECT_ROOT / file_name
                self.assertTrue(
                    file_path.is_file(),
                    f"Expected file does not exist: {file_path}",
                )

    def test_src_modules_exist(self):
        """All Phase 0.13 source module files must exist."""
        for module_name in SRC_MODULES:
            with self.subTest(module=module_name):
                file_path = PROJECT_ROOT / "src" / f"{module_name}.py"
                self.assertTrue(
                    file_path.is_file(),
                    f"Expected source module does not exist: {file_path}",
                )

    def test_src_init_exists(self):
        """src/__init__.py package marker must exist."""
        self.assertTrue((PROJECT_ROOT / "src" / "__init__.py").is_file())


class TestSourceModules(unittest.TestCase):
    """Verify all source code modules (Phase 0.13 foundation) are importable."""

    def test_src_package_importable(self):
        """The src package must be importable."""
        import src
        self.assertTrue(hasattr(src, "__path__"))

    def test_src_modules_importable(self):
        """Each src module must be importable without errors."""
        for module_name in SRC_MODULES:
            with self.subTest(module=module_name):
                full_name = f"src.{module_name}"
                module = importlib.import_module(full_name)
                self.assertIsNotNone(module)


class TestScopeProtection(unittest.TestCase):
    """Verify no unauthorized packages are installed (scope protection).

    requirements-dev.txt authorizes exactly ONE development dependency: the
    pytest test runner. This does NOT weaken protection for anything else -
    every package in UNAUTHORIZED_PACKAGES stays forbidden unconditionally,
    even if someone accidentally adds it to requirements-dev.txt.
    """

    def test_runner_declaration_present(self):
        """The pytest exception requires an explicit requirements-dev.txt declaration."""
        self.assertTrue(
            _runner_exception_active(),
            "requirements-dev.txt must exist at the repo root and declare "
            "the pytest test runner.",
        )

    def test_no_unauthorized_packages(self):
        """Optional/later-phase packages must NOT be installed.

        pytest passes only while _runner_exception_active() holds; every other
        checked package is rejected regardless of any dev-file contents.
        """
        runner_authorized = _runner_exception_active()
        self.assertTrue(
            runner_authorized,
            "requirements-dev.txt must declare pytest; without that explicit "
            "declaration the pytest installation violates Phase 0 scope rules.",
        )
        for pkg in (*UNAUTHORIZED_PACKAGES, "pytest"):
            if pkg == "pytest" and runner_authorized:
                continue  # sole permitted development dependency, via declaration
            with self.subTest(package=pkg):
                try:
                    importlib.import_module(pkg)
                    installed = True
                except ImportError:
                    installed = False
                if pkg == "pytest":
                    detail = (
                        "'pytest' is installed but its approval depends on an "
                        "explicit 'pytest' declaration in requirements-dev.txt, "
                        "which is currently missing."
                    )
                else:
                    detail = (
                        f"'{pkg}' is installed but is NOT an approved project "
                        f"dependency (not in requirements.txt). This violates "
                        f"Phase 0 scope rules."
                    )
                self.assertFalse(installed, detail)


if __name__ == "__main__":
    unittest.main(verbosity=2)



