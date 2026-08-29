# Centralized project configuration for Customer-Segmentation-RFM
# DO NOT add business logic, RFM calculations, or dataset selection here.

import pathlib

# PROJECT ROOT: directory containing this config.py file
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent

# Approved directory structure (established in Phase 0.2)
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

SRC_DIR = PROJECT_ROOT / "src"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"
TABLES_DIR = OUTPUTS_DIR / "tables"
REPORTS_DIR = OUTPUTS_DIR / "reports"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Dataset selection is deliberately NOT defined here.
# Dataset selection belongs to Phase 3 — do not define RAW_DATA_FILE,
# DATASET_NAME, or DATASET_PATH here.

# RFM methodology parameters are deliberately NOT defined here.
# Those belong to later methodology phases.

# No business logic, analysis, or visualization code belongs in this file.