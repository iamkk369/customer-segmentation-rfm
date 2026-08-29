# MONTH 2 SUBMISSION — Phases 6–10

## 1. Phase Mapping (Month 2)

| Phase | Title | Status |
|---|---|---|
| 6 | Exploratory Data Analysis | COMPLETE — `src/statistics_analysis.py` + `tests/test_statistics_analysis.py` + `outputs/reports/phase6_eda_report.md` |
| 7 | RFM Calculation | COMPLETE — `src/rfm_analysis.py` + `tests/test_rfm_analysis.py` (21 dedicated tests, validated on the 524,878-row real dataset) |
| 8 | Customer Segmentation | COMPLETE — `src/segmentation.py` + `tests/test_segmentation.py` (19 dedicated tests, validated on the real Phase 7 RFM output: 4,338 customers, deterministic score-based segmentation) |
| 9 | Statistical Analysis | COMPLETE — `src/statistics_analysis.py` extended (Phase 6 EDA preserved + Phase 9 statistics) + Phase 9 tests in `tests/test_statistics_analysis.py` (22 tests, validated on the real Phase 7/8 outputs: Pearson/Spearman correlations, normality, segment profiles, Kruskal-Wallis/Mann-Whitney) |
| 10 | Data Visualization | COMPLETE — `src/visualization.py` + `tests/test_visualization.py` (14 dedicated tests; four deterministic charts saved to `outputs/charts/`, generated from the real Phase 5→7→8 pipeline output: 4,338 customers) |

> **Honesty Note (Phase 7):** Phase 7 (RFM Calculation) is **COMPLETE** — `src/rfm_analysis.py` implements Recency / Frequency / Monetary calculation, customer-level aggregation, and tie-safe deterministic 1–5 scoring, verified by the dedicated `tests/test_rfm_analysis.py` (21 tests) against the real 524,878-row Phase 5 working dataset. No permanent RFM CSV/report/chart is produced (no explicit output requirement was found in the repository).
>
> **Honesty Note (Phase 8):** Phase 8 (Customer Segmentation) is **COMPLETE** — `src/segmentation.py` implements deterministic, interpretable score-based segmentation (Champions / Loyal Customers / Average Customers / At-Risk Customers / Lost Customers) that consumes the real Phase 7 RFM output, verified by the dedicated `tests/test_segmentation.py` (19 tests) against 4,338 real customers. No permanent segmentation CSV/report/chart is produced (no explicit output requirement was found in the repository).
>
> **Honesty Note (Phase 9):** Phase 9 (Statistical Analysis) is **COMPLETE** — `src/statistics_analysis.py` now holds both the preserved Phase 6 EDA work and the deterministic Phase 9 statistics (Pearson/Spearman RFM correlations, D'Agostino-Pearson normality, per-segment profiles, Kruskal-Wallis & Mann-Whitney comparison tests), verified by the Phase 9 tests in `tests/test_statistics_analysis.py` (22 tests) against the real Phase 7/8 outputs (4,338 customers). No permanent statistical CSV/report/chart is produced (no explicit output requirement was found in the repository).
>
> **Honesty Note (Phase 10):** Phase 10 (Data Visualization) is **COMPLETE** — `src/visualization.py` implements the approved minimum chart set (`rfm_score_distributions.png`, `segment_size_bar.png`, `segment_monetary_box.png`, `rfm_metric_correlation_scatter.png`), rendered deterministically with matplotlib/seaborn from the real Phase 5→7→8 pipeline output and saved into the existing `outputs/charts/` directory, verified by the dedicated `tests/test_visualization.py` (14 tests). These are the only permanent file outputs in Month 2; no insights (Phase 11) or integration (Phase 13) logic is included.

## 2. Concrete Proposed Submission Structure (based on the ACTUAL repository)

```
Month 2/
├── config.py                     # Shared Phase 0–4 configuration
├── main.py                       # Shared entry point (Phase 0.13 stub)
├── requirements.txt              # Shared Phase 0 dependencies
├── data/
│   └── processed/
│       └── OnlineRetail_invalid_removed.csv   # Phase 5 working dataset (Month 1 output — required by Phase 6/7)
├── src/
│   ├── __init__.py               # Shared package marker
│   ├── data_loading.py           # Phase 4 module (required so shared env test can import all src modules)
│   ├── data_cleaning.py          # Phase 5 module (shared src set, as above)
│   ├── statistics_analysis.py    # Phase 6 EDA + Phase 9 statistics implementation
│   ├── rfm_analysis.py           # Phase 7 implementation
│   ├── segmentation.py           # Phase 8 implementation (was foundation skeleton)
│   └── visualization.py          # Phase 10 implementation (was foundation skeleton)
├── outputs/
│   ├── charts/
│   │   ├── rfm_score_distributions.png        # Phase 10 chart
│   │   ├── segment_size_bar.png               # Phase 10 chart
│   │   ├── segment_monetary_box.png           # Phase 10 chart
│   │   └── rfm_metric_correlation_scatter.png # Phase 10 chart
│   └── reports/
│       └── phase6_eda_report.md  # Phase 6 deliverable report
└── tests/
    ├── __init__.py               # Shared test package marker
    ├── test_environment.py       # Phase 0 baseline test (shared environment gate)
    ├── test_statistics_analysis.py # Phase 6 + Phase 9 test
    ├── test_rfm_analysis.py      # Phase 7 test
    ├── test_segmentation.py      # Phase 8 test
    └── test_visualization.py     # Phase 10 test
```

**Required support directory skeleton** (so the shared `test_environment.py` baseline passes): `data/raw/`, `src/`, `outputs/charts/`, `outputs/tables/`, `outputs/reports/`, `tests/`, `docs/`, `notebooks/`.

## 3. File Classification

| Question | Answer |
|---|---|
| Which source files are required? | `src/statistics_analysis.py` (Phase 6 + Phase 9); `src/rfm_analysis.py` (Phase 7); `src/segmentation.py` (Phase 8); `src/visualization.py` (Phase 10) |
| Which shared files are required? | `config.py`, `requirements.txt`, `src/__init__.py`, `tests/__init__.py`, `tests/test_environment.py`, `main.py` |
| Which configuration / dependency files are required? | `config.py`, `requirements.txt` |
| Which data files are required? | `data/processed/OnlineRetail_invalid_removed.csv` — the Phase 5 working dataset used by Phase 6 and Phase 7 |
| Which test files verify the phase? | `tests/test_statistics_analysis.py` (Phase 6 + Phase 9); `tests/test_rfm_analysis.py` (Phase 7); `tests/test_segmentation.py` (Phase 8); `tests/test_visualization.py` (Phase 10); `tests/test_environment.py` (shared baseline) |
| What command runs / tests it? | Section 4 command on a fresh checkout |

## 4. Legitimate Cross-Month Dependency (documented, preserved — no duplicate)

- Month 2 legitimately reuses the Month 1 Phase 5 working dataset `data/processed/OnlineRetail_invalid_removed.csv`. It is therefore shipped inside the Month 2 package (the same real file, produced by `src/data_cleaning.py` in Month 1). No artificial duplicate implementation is created.

## 5. Execution / Run Instructions

Run from the **Month 2** root on any Windows machine with VS Code (Python 3.12.x):

```bash
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected result: `tests/test_environment.py` (baseline), `tests/test_statistics_analysis.py` (Phase 6 + Phase 9), `tests/test_rfm_analysis.py` (Phase 7), `tests/test_segmentation.py` (Phase 8), and `tests/test_visualization.py` (Phase 10) all pass. The Phase 10 tests generate the four approved charts into `outputs/charts/`.

## 6. Phase-Level Executability Summary

| Phase | Runnable with only Month 2 files? | Verification |
|---|---|---|
| 6 | Yes | `tests/test_statistics_analysis.py` (524,878-row dataset, real metrics) |
| 7 | Yes | `tests/test_rfm_analysis.py` (21 tests; 524,878-row real dataset; R/F/M + scoring verified) |
| 8 | Yes | `tests/test_segmentation.py` (19 tests; real Phase 7 RFM output — 4,338 customers, deterministic segmentation) |
| 9 | Yes | Phase 9 tests in `tests/test_statistics_analysis.py` (22 tests; real Phase 7/8 outputs — 4,338 customers; correlations, normality, segment profiles, Kruskal-Wallis/Mann-Whitney) |
| 10 | Yes | `tests/test_visualization.py` (14 tests; four deterministic charts rendered from the real Phase 5→7→8 output and saved to `outputs/charts/`) |

## 7. Professor Execution Test (Month 2)

> **"Can the Month 2 submission be copied to another Windows machine, opened in VS Code, dependencies installed, and run without requiring Month 3 files?"**

**Answer: YES.** All Month 2 functionality (Phase 6 EDA, Phase 7 RFM, Phase 8 segmentation, Phase 9 statistical analysis, and Phase 10 visualization — each with its dedicated tests) runs independently of Month 3. The Phase 10 charts are saved into `outputs/charts/` when the test suite (or `build_phase10_visualizations()`) runs. Phases 11–15 belong to Month 3 and are not required here.

## 8. Not included in this package (correctly, per the actual plan)

- Phases 11–15 (Month 3): Insights, final testing, integration, documentation, review — not shipped here.