# Customer Segmentation Analysis using RFM Modeling

A complete Python for Data Science micro-project that segments customers of an
online retailer using RFM (Recency, Frequency, Monetary) analysis — from raw
CSV load and cleaning through RFM scoring, segmentation, statistical analysis,
charts, and business insights.

| Item | Detail |
|---|---|
| Subject | Python for Data Science (BE05000231) — GTU (Gujarat Technological University) |
| Type | Academic Micro-Project (PBL) |
| Status | **Complete** — all 15 WBS phases finished |
| Python | **3.12.10** (verified) — Python **3.14.x is NOT supported** |
| Tests | **491 passed · 0 failed · 0 errors · 0 skipped** |

## Contents

1. [Project Overview](#1-project-overview)
2. [Verified Results](#2-verified-results)
3. [Pipeline](#3-pipeline)
4. [Storage Strategy (OPTION B)](#4-storage-strategy-option-b)
5. [Repository Structure](#5-repository-structure)
6. [Dataset](#6-dataset)
7. [Getting Started](#7-getting-started)
8. [Run the Pipeline](#8-run-the-pipeline)
9. [Testing](#9-testing)
10. [Outputs](#10-outputs)
11. [Documentation](#11-documentation)
12. [Month-wise Submission Breakdown](#12-month-wise-submission-breakdown)
13. [Syllabus Mapping](#13-syllabus-mapping)
14. [License](#14-license)

## 1. Project Overview

**Problem.** An online retailer needs to understand how its customers differ in
recency, frequency, and monetary value so that retention and marketing actions
can target the right groups.

**Objectives.**

- Analyze the Online Retail dataset end to end with a reproducible pipeline.
- Clean and validate raw transaction data (missing values, duplicates,
  invalid records) without altering the immutable raw source.
- Compute per-customer RFM metrics with deterministic 1–5 scoring.
- Segment every customer into meaningful groups using RFM analysis.
- Back the segmentation with descriptive and inferential statistics,
  visualizations, and business insights.

**Key features.**

- Modular, phase-by-phase pipeline (`main.py` + 8 modules under `src/`).
- Deterministic, rule-based segmentation (no ML, per the approved project
  decision) — fully reproducible results.
- OPTION B storage strategy: intermediates stay in memory; the raw dataset is
  write-protected at the code level.
- Descriptive and inferential statistics: Pearson/Spearman correlations,
  normality tests, Kruskal–Wallis and Mann–Whitney comparisons.
- Comprehensive test suite: 13 modules, 491 tests, all passing.

**Methodology.**
- Load and validate the raw CSV (`src/data_loading.py`).
- Handle missing values, remove exact duplicates, remove invalid records
  (cancellation invoices, non-positive quantity/price) (`src/data_cleaning.py`).
- Compute per-customer Recency, Frequency, Monetary metrics with deterministic
  1–5 scoring (`src/rfm_analysis.py`).
- Classify customers with a rule-based five-segment classifier — no ML, per the
  approved project decision (`src/segmentation.py`).
- Run descriptive and inferential statistics: Pearson/Spearman correlations,
  normality tests, Kruskal–Wallis and Mann–Whitney comparisons
  (`src/statistics_analysis.py`).
- Produce matplotlib/seaborn charts (`src/visualization.py`) and a business
  insights report (`src/insights.py`).

**Key outputs.** 4 approved charts in `outputs/charts/`, EDA + insights reports
in `outputs/reports/`, final segmentation of 4,338 customers into 5 segments.

**Technology stack.** Python 3.12.10 · pandas 3.0.5 · NumPy 2.5.2 · SciPy 1.18.0 ·
scikit-learn 1.9.0 · matplotlib 3.11.1 · seaborn 0.13.2 · pytest 9.1.1 (dev/test runner)

## 2. Verified Results

Pipeline: **541,909 raw rows → 524,878 working rows → 4,338 customers.**

| Segment | Customers |
|---|---|
| Champions | 923 |
| Loyal Customers | 983 |
| Average Customers | 1,040 |
| At-Risk Customers | 1,058 |
| Lost Customers | 334 |
| **Total** | **4,338** |

## 3. Pipeline

```
Raw data
  → cleaning (missing values)
  → duplicate removal
  → invalid-record removal
  → RFM analysis
  → customer segmentation
  → statistical analysis
  → visualization
  → insights/reports
```

## 4. Storage Strategy (OPTION B)

Intermediate datasets are processed **in memory** and passed between pipeline
stages:

- `OnlineRetail_cleaned.csv` and `OnlineRetail_deduplicated.csv` are **NOT**
  permanently stored in `data/processed/`.
- The only permanent processed dataset is
  `data/processed/OnlineRetail_invalid_removed.csv`.
- The raw dataset is immutable: attempts to write generated output into
  `data/raw/` raise `ValueError`.

## 5. Repository Structure

```
Customer-Segmentation-RFM/
├── main.py                  # pipeline entry point
├── config.py                # paths/settings
├── requirements.txt         # runtime dependencies (pinned)
├── requirements-dev.txt     # adds the pytest runner
├── src/                     # data_loading, data_cleaning, rfm_analysis,
│                            # segmentation, statistics_analysis,
│                            # visualization, insights
├── tests/                   # 13 test modules (491 tests)
├── data/
│   ├── raw/OnlineRetail.csv
│   └── processed/OnlineRetail_invalid_removed.csv
├── outputs/
│   ├── charts/              # 4 PNG charts
│   └── reports/             # EDA + insights reports
└── docs/
    ├── PROJECT_REPORT.md
    └── pbl_submission/      # MONTH_1.md, MONTH_2.md, MONTH_3.md
```

## 6. Dataset

- Source: the well-known **Online Retail** dataset (UCI Machine Learning
  Repository) — 541,909 transactions from a UK-based online retailer.
- `data/raw/OnlineRetail.csv` — 47,901,468 bytes
  (SHA-256 `BFA47136…EB84EB`; full hash pinned in `src/data_cleaning.py`).
- `data/processed/OnlineRetail_invalid_removed.csv` — 46,962,172 bytes.
- **Note:** these dataset files are relatively large (~90 MB combined) and are
  included in this repository, so cloning may take longer on slow connections.
  Git LFS is not configured.

## 7. Getting Started

> **Important:** Do not use Python 3.14.x for this project. The verified
> project environment is Python 3.12.10, and the pinned dependencies are
> validated against it.

1. Create and activate a virtual environment from the project root:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Verify the interpreter:

   ```powershell
   python --version
   ```

   Expected output: `Python 3.12.10`

   (Throughout this project's verification the interpreter was invoked
   explicitly as `.\.venv\Scripts\python.exe`; both forms are equivalent once
   the virtual environment is activated.)

3. Install the dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

   - `requirements.txt` — the six pinned runtime data-science libraries.
   - `requirements-dev.txt` — `requirements.txt` plus `pytest==9.1.1`
     (not needed to run the pipeline itself).

## 8. Run the Pipeline

```powershell
python main.py
```

This executes load → clean → EDA → RFM → segmentation → statistics → charts →
insights report, writes the 4 charts and 2 reports, and prints the stage
summaries and final segment counts (ending with "Pipeline finished OK").

## 9. Testing

```powershell
python -m pytest tests/ -v
```

Verified result: **491 passed, 0 failed, 0 errors, 0 skipped**
(pytest 9.1.1 on Python 3.12.10, 13 test modules; a quieter run:
`python -m pytest tests/ -q`).

The suite covers loading, cleaning (missing values, duplicates, invalid
records, raw-data write protection), RFM scoring, segmentation, statistical
analysis, visualization, insights, integration, environment, edge cases,
syllabus compliance, and final data validation.

## 10. Outputs

- `outputs/charts/` — `rfm_metric_correlation_scatter.png`,
  `rfm_score_distributions.png`, `segment_monetary_box.png`,
  `segment_size_bar.png`
- `outputs/reports/` — `phase6_eda_report.md`, `phase11_insights_report.md`

## 11. Documentation

- `docs/PROJECT_REPORT.md` — full project report with detailed phase/subphase
  records.
- `docs/pbl_submission/MONTH_1.md`, `MONTH_2.md`, `MONTH_3.md` — frozen
  month-wise PBL submission records.

## 12. Month-wise Submission Breakdown

| Month | Phases | Scope | Record |
|---|---|---|---|
| Month 1 | 1–5 | Initiation, requirements/scope, dataset, data loading, data cleaning | `docs/pbl_submission/MONTH_1.md` |
| Month 2 | 6–10 | EDA, RFM calculation, segmentation, statistical analysis, visualization | `docs/pbl_submission/MONTH_2.md` |
| Month 3 | 11–15 | Insights & findings, testing & validation, final integration, documentation, final review/viva | `docs/pbl_submission/MONTH_3.md` |

## 13. SYLLABUS MAPPING

Mapping of the implemented work to syllabus-level requirements
(subject BE05000231). Every row points to real code, tests, or artifacts in
this repository.

| Syllabus work area | Project implementation | Tests / evidence |
|---|---|---|
| Data loading and preparation | `src/data_loading.py` — CSV load, InvoiceDate datetime parsing | `tests/test_data_loading.py` |
| Data cleaning and validation | `src/data_cleaning.py` — missing values, duplicates, invalid records (R1–R3) | `tests/test_data_cleaning.py`, `tests/test_data_validation.py`; `data/processed/*.csv` |
| Exploratory data analysis | `build_phase6_eda_summary()` in `src/statistics_analysis.py` | `outputs/reports/phase6_eda_report.md`; `tests/test_statistics_analysis.py` |
| Descriptive/statistical analysis | Pearson/Spearman correlations, normality, Kruskal-Wallis & Mann-Whitney tests in `src/statistics_analysis.py` (Phase 9) | `tests/test_statistics_analysis.py` |
| RFM analysis | Recency/Frequency/Monetary calculation and deterministic 1–5 scoring in `src/rfm_analysis.py` | `tests/test_rfm_analysis.py` |
| Customer segmentation | Rule-based five-segment classifier in `src/segmentation.py` (no ML by approved decision) | `tests/test_segmentation.py` |
| Visualizations (**Unit 7 — Data Visualization**) | matplotlib + seaborn chart functions in `src/visualization.py` | Four PNG charts in `outputs/charts/`; `tests/test_visualization.py` |
| Business insights | Segment/revenue/final-findings generator in `src/insights.py` | `outputs/reports/phase11_insights_report.md`; `tests/test_insights.py` |
| Testing and validation | 13 test modules in `tests/` — 491 tests, all passing | `.\.venv\Scripts\python.exe -m pytest tests -q` |
| Documentation/reporting | `docs/PROJECT_REPORT.md`, `docs/pbl_submission/MONTH_1.md`–`MONTH_3.md` | `tests/test_syllabus_compliance.py` |

## 14. License

License: Not currently specified.   


made by me 
