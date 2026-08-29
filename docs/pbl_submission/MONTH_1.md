# MONTH 1 SUBMISSION — Phases 1–5

## 1. Phase Mapping (Month 1)

| Phase | Title | Status |
|---|---|---|
| 1 | Project Initiation | COMPLETE (documentation only — no code artefact) |
| 2 | Requirements & Scope | COMPLETE (documentation only — no code artefact) |
| 3 | Dataset | COMPLETE — approved dataset shipped in `data/raw/OnlineRetail.csv` |
| 4 | Data Loading & File Handling | COMPLETE — `src/data_loading.py` + `tests/test_data_loading.py` |
| 5 | Data Cleaning & Preparation | COMPLETE — `src/data_cleaning.py` + `tests/test_data_cleaning.py` + `data/processed/` outputs |

## 2. Concrete Submission Structure (matches the ACTUAL repository)

```
Month 1/
├── README.md                   # Month 1 standalone instructions
├── config.py                   # Shared Phase 0 configuration (path constants)
├── main.py                     # Shared entry point (Phase 0.13 stub)
├── requirements.txt            # Shared Phase 0 dependencies
├── data/
│   ├── raw/
│   │   └── OnlineRetail.csv                # Phase 3 approved dataset (47,901,468 bytes)
│   └── processed/
│       ├── OnlineRetail_cleaned.csv        # Phase 5.1 output
│       ├── OnlineRetail_deduplicated.csv   # Phase 5.3 output
│       └── OnlineRetail_invalid_removed.csv # Phase 5 final working dataset
├── src/
│   ├── __init__.py             # Shared package marker
│   ├── data_loading.py         # Phase 4 implementation
│   └── data_cleaning.py        # Phase 5 implementation
├── tests/
│   ├── __init__.py             # Shared test package marker
│   ├── test_environment.py     # Phase 0 baseline test (Month-1 scoped)
│   ├── test_data_loading.py    # Phase 4 test
│   └── test_data_cleaning.py   # Phase 5 test
├── outputs/                    # Approved dirs (reserved; required by config/test_environment)
│   ├── charts/
│   ├── tables/
│   └── reports/
├── notebooks/                  # Approved dir (reserved; required by config/test_environment)
└── docs/                       # Package docs (reserved; required by config/test_environment)
```

The submitted `tests/test_environment.py` is **Month-1 scoped**: it is the Phase 0
baseline environment test with `SRC_MODULES = [data_loading, data_cleaning]` so it
validates only the modules shipped in this package (it does not import the Phase 6+
modules, keeping Month 1 independent).

## 3. File Classification

| Question | Answer |
|---|---|
| Which source files are required? | `src/data_loading.py` (Phase 4), `src/data_cleaning.py` (Phase 5) |
| Which shared files are required? | `config.py`, `requirements.txt`, `src/__init__.py`, `tests/__init__.py`, `tests/test_environment.py`, `main.py` |
| Which configuration / dependency files are required? | `config.py`, `requirements.txt` |
| Which data files are required? | `data/raw/OnlineRetail.csv` (Phase 3 input); `data/processed/OnlineRetail_cleaned.csv`, `data/processed/OnlineRetail_deduplicated.csv`, `data/processed/OnlineRetail_invalid_removed.csv` (Phase 5 outputs) |
| Which test files verify the phase? | `tests/test_environment.py` (Phase 0 baseline), `tests/test_data_loading.py` (Phase 4), `tests/test_data_cleaning.py` (Phase 5) |
| What command runs / tests it? | Section 4 command on a fresh checkout |

## 4. Execution / Run Instructions

Run from the **Month 1** root on any Windows machine with VS Code (Python 3.12.x required):

```bash
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected result: `tests/test_environment.py`, `tests/test_data_loading.py` (Phase 4), and `tests/test_data_cleaning.py` (Phase 5) all pass.

**Honest note on `main.py`:** the end-to-end `main.py` pipeline orchestration is intentionally deferred to Phase 13 (final integration). For Month 1, the implemented Phase 4 + 5 functionality is exercised through the modules' public functions and verified by the unit-test suite against the real dataset. No fake pipeline is invented.

## 5. Professor Execution Test (Month 1)

> **"Can the Month 1 submission be copied to another Windows machine, opened in VS Code, dependencies installed, and run without requiring Month 2 or Month 3 files?"**

**Answer: YES.**

- All required files for Phases 1–5 are included in the `Month 1/` package above.
- No Month 1 file imports `src/statistics_analysis.py`, `src/rfm_analysis.py`, `src/segmentation.py` or `src/visualization.py`, so Month 2/3 files are not needed.
- All six approved libraries (pandas, numpy, scipy, scikit-learn, matplotlib, seaborn) are declared in `requirements.txt`.

## 6. Phase-Level Executability Summary

| Phase | Runnable with only Month 1 files? | Verification |
|---|---|---|
| 1–2 | Yes (documentation) | README.md |
| 3 | Yes | `data/raw/OnlineRetail.csv` present and validated |
| 4 | Yes | `python -m unittest tests.test_data_loading -v` |
| 5 | Yes | `python -m unittest tests.test_data_cleaning -v` (writes `data/processed/`) |

