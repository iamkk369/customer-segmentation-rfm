# MONTH 3 SUBMISSION — Phases 11–15

## 1. Phase Mapping (Month 3)

| Phase | Title                              | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ----- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 11    | Insights & Findings                | COMPLETE — subphases 11.1 (Customer Insights), 11.2 (Segment Insights), 11.3 (Revenue Insights) and 11.4 (Final Findings) all COMPLETE: `src/insights.py` implemented (segment RFM-score/Recency, revenue, and final-findings synthesis), `tests/test_insights.py` (92 tests) passing, full regression 365 tests OK, real-data report (incl. §1.1 Segment RFM-Score & Recency Characteristics, §1.2 Revenue Insights, and **Final Findings (11.4)**) at `outputs/reports/phase11_insights_report.md`; Phase 11 fully closed |
| 12    | Testing & Validation               | COMPLETE — 12.1 (Functional Testing): dedicated functional validation across Phases 4–11 (`tests/test_functional.py`, 23 tests). 12.2 (Data Validation): data-integrity validation of the real pipeline (`tests/test_data_validation.py`, 45 tests; raw SHA-256/size, Phase 5 processed schema/row-chain, customer/RFM/segment/Phase-11 consistency). 12.3 (RFM Calculation Testing): EXISTING Phase 7 implementation independently validated on real data (`tests/test_rfm_analysis.py`, 39 tests incl. 18 dedicated; per-customer values recomputed from source rows and matched element-wise, documented scoring rule cross-checked independently; `src/rfm_analysis.py` verified correct and UNMODIFIED). 12.4 (Edge-Case Testing): `tests/test_edge_cases.py` (13 tests) covering documented Phase 7 raise paths, minimal-table RFM boundaries, segmentation minimal-input edges; NO source defect found. 12.5 (Syllabus Compliance Testing): `tests/test_syllabus_compliance.py` (16 tests) validating ONLY the approved README §2.4 mapping (Units 1–7 / CO-1..CO-5) — exactly the six approved TR-2 libraries pinned+importable, AST-proven absence of unapproved third-party imports in `src/`, Unit 2 CSV/exception handling, Units 3–7 workflow coverage, evidence artifacts (four approved charts, Phase 11 report); compliance categories: automated / documentary / later-WBS-not-yet-testable / non-compliance NONE. Full regression **480 tests OK**. Phase 13–15 NOT STARTED |
| 13    | Final Integration                  | COMPLETE — `main.py` upgraded from the Phase 0.13 stub to the real orchestration layer (13.1): chains the existing public phase functions only — Phase 4 load → Phase 5 cleaning (5.1→5.2→5.3 with the three processed CSVs persisted) → Phase 6 EDA → Phase 7 RFM+scoring → Phase 8 segmentation → Phase 9 statistics (exact `build_phase9_statistical_summary` structure) → Phase 10 four approved charts → Phase 11 insights + report via `build_phase11_insights(summary=...)` + `render_phase11_insights_markdown` (single-pass, zero duplicated logic). Real end-to-end execution verified on the OnlineRetail dataset (13.2): finished OK in ~19.4 s — 541,909 raw rows → 524,878 working rows → reference date 2011-12-09 → 4,338 customers → Champions=923/Loyal=983/Average=1040/At-Risk=1058/Lost=334 → statistics complete → 4 charts → report rewritten. Error check (13.3) fixed one genuine integration defect before running (report generation would have rebuilt the whole pipeline a second time; now reuses the computed insights object) and corrected one wrong test expectation (pandas 3.x datetime64[us]; loading read-only, implementation unchanged). Specification check (13.4): dataset/deps/Phase 4–11 methodology unchanged, Phase 12 validation intact (`tests/test_integration.py` added, 12 tests; full regression **492 tests OK**); Phase 14–15 NOT STARTED |
| 14    | Documentation                      | COMPLETE - all five subphases: 14.1 Project Report (16-section foundation), 14.2 Methodology (report section 17, fifteen documented stages reproduced from source), 14.3 Results (report section 18, verified values with sums re-checked), 14.4 Screenshots/Charts (report section 19, four approved figures with resolving references) and 14.5 Conclusion (report section 20: objectives-revisited table, principal conclusions with labelled interpretation, syllabus contribution, five honest limitations incl. rule-based/no-ML/no-causality/no-deployment, closing statement). docs/PROJECT_REPORT.md now fully documents the project as implemented and verified through Phase 13. Phases 1-14 COMPLETE; Phase 15 NOT STARTED |
| 15    | Final Review / Presentation / Viva | COMPLETE - full final audit executed: repository inspection; WBS consistency (Phases 1-14 records verified); source-code audit (no TODO/FIXME/stubs/hard-coded results); real end-to-end run of main.py exit 0 (wall ~19.1 s, pipeline-internal 14.2 s, all stage values matching baselines); full regression 492 tests OK in ~352 s; programmatic 49-gate audit re-verifying raw SHA-256/size/rows, processed schema chain, RFM formulas recomputed per customer, score ranges 1-5, all nine segmentation rule boundaries, segment counts 923/983/1040/1058/334, revenue totals/shares, Pearson r=0.9519, KW H=3177.53 recomputed live, four valid PNGs with resolving report refs, insight-layer completeness, doc consistency (20-section report), six approved pinned libraries; no unsupported academic claims found; root clean. All 15 WBS phases COMPLETE - project finished |

> **Honesty Note:** Phases 11, 12 and 13 are all COMPLETE with executable code and passing tests. Phase 11 closed via subphases 11.1-11.4 (92 insight tests). Phase 12 closed via five dedicated suites: 12.1 Functional Testing (23 tests), 12.2 Data Validation (45 tests; raw SHA-256 + size verified unchanged; customer = 4,338; segment counts sum to 4,338 with exactly five approved names; total revenue GBP 10,642,110.80), 12.3 RFM Calculation Testing (18 dedicated; values independently recomputed from source transactions), 12.4 Edge-Case Testing (13 tests), and 12.5 Syllabus Compliance Testing (16 tests validating ONLY the approved README section 2.4 mapping Units 1-7 / CO-1..CO-5; six approved libraries pinned and importable with zero unapproved third-party imports proven by AST scan; scikit-learn remains approved/pinned while segmentation deliberately uses rule-based scoring per the approved Phase 8 record - reported as documentary scope, not fabricated ML usage). Phase 13 Final Integration is COMPLETE: main.py chains the existing public phase functions end-to-end with zero duplicated logic and executed successfully on the real dataset (~19.4 s) producing the verified outputs above; one genuine integration defect (duplicate pipeline rebuild for the report) was fixed during 13.3 before running, and a validation batch environment never modified any src/ module. Full regression **492 tests OK** (480 baseline + 12 integration tests). Phase 14 (Documentation) and Phase 15 (Final Review / Presentation / Viva) still have no executable code or artifacts and remain NOT STARTED. This document does NOT claim those remaining items are done today. Phase 14 is IN PROGRESS: subphases 14.1 (Project Report), 14.2
 (Methodology, report §17), 14.3 (Results, report §18) and 14.4
 (Screenshots/Charts, report §19) are COMPLETE - docs/PROJECT_REPORT.md carries
 the full verified foundation, the implemented-methodology narrative, the
 results narrative built strictly from existing verified artifacts (all sums
 re-checked), and the four-chart figure documentation; and finally 14.5
 (Conclusion, report §20) - so PHASE 14 IS COMPLETE in full. Phase 15 (Final
 Review / Presentation / Viva) is also COMPLETE: a 49-gate programmatic audit
 re-verified every auditable value live (RFM recomputed per customer, all nine
 segmentation boundaries, revenue/share/correlation/KW statistics, four valid
 charts, raw SHA-256/size, doc consistency), main.py ran end-to-end with exit 0
 (~19.1 s wall), and the full regression passed at 492 tests. docs/PROJECT_REPORT.md
 documents the project exactly as implemented and verified. ALL 15 WBS PHASES ARE
 COMPLETE - no phase remains.

## 2. Concrete Proposed Submission Structure (based on the ACTUAL repository + planned integration)

```
Month 3/
├── config.py                     # Shared configuration (carried from Month 1)
├── main.py                       # Entry point — FULL PIPELINE ORCHESTRATION (Phase 13)
├── requirements.txt              # Shared dependencies (carried from Month 1)
├── data/
│   ├── raw/
│   │   └── OnlineRetail.csv                    # Month 1 Phase 3 dataset (preserved)
│   └── processed/
│       └── OnlineRetail_invalid_removed.csv    # Phase 5 working dataset (Month 1 output)
├── src/
│   ├── __init__.py
│   ├── data_loading.py            # Phase 4 (Month 1)
│   ├── data_cleaning.py           # Phase 5 (Month 1)
│   ├── statistics_analysis.py     # Phase 6 (Month 2) + Phase 9 statistical analysis
│   ├── rfm_analysis.py            # Phase 7 (Month 2)
│   ├── segmentation.py            # Phase 8 (Month 2) — implemented by Month 3
│   └── visualization.py           # Phase 10 (Month 2) — implemented by Month 3
├── outputs/
│   ├── charts/                    # Phase 10 chart outputs
│   ├── tables/                    # Phase 9/12 table outputs
│   └── reports/
│       ├── phase6_eda_report.md   # Month 2 Phase 6 report (carried)
│       └── phase11_insights_report.md  # Phase 11 insights report (new)
└── tests/
    ├── __init__.py
    ├── test_environment.py            # Phase 0 baseline (carried)
    ├── test_data_loading.py           # Phase 4 (Month 1, carried)
    ├── test_data_cleaning.py          # Phase 5 (Month 1, carried)
    ├── test_statistics_analysis.py    # Phase 6 (Month 2, carried)
    ├── test_rfm_analysis.py           # Phase 7/9 test (planned)
    ├── test_segmentation.py           # Phase 8 test (planned)
    └── test_visualization.py          # Phase 10 test (planned)
```

## 3. File Classification

| Question                                             | Answer                                                                                                    |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Which source files are required?                     | All `src/` modules from Months 1–2 plus Phase 8/9/10 implementations landing in Month 3                   |
| Which shared files are required?                     | `config.py`, `requirements.txt`, `src/__init__.py`, `tests/__init__.py`, `main.py`                        |
| Which configuration / dependency files are required? | `config.py`, `requirements.txt`                                                                           |
| Which data files are required?                       | `data/raw/OnlineRetail.csv`, `data/processed/OnlineRetail_invalid_removed.csv` (both produced in Month 1) |
| Which test files verify the phase?                   | Full test suite — `tests/` files from Months 1–2 plus new Phase 7/8/10/12 tests                           |
| What command runs / tests it?                        | Section 4 command on a fresh checkout                                                                     |

## 4. Execution / Run Instructions (planned for Month 3)

```bash
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py                       # full RFM → segmentation pipeline
.venv\Scripts\python.exe -m unittest discover -s tests -v   # complete validation
```

## 5. Legitimate Cross-Month Dependencies (documented, preserved — no duplicates)

- Month 3 legitimately depends on the Month 1 dataset/loading/cleaning components and the Month 2 EDA/RFM components. Per the project dependency rule, the required working components are shipped inside the Month 3 package (the real Month 1 / Month 2 files) — no artificial duplicates are introduced.

## 6. Professor Execution Test (Month 3)

> **"Can the final Month 3 submission be copied to another Windows machine, opened in VS Code, dependencies installed, and run?"**

**Answer: YES for the analysis pipeline (verified in Phase 13.2).** Phases 1-13 are all implemented and Phase 12 validated them; `main.py` now orchestrates the complete workflow end-to-end against the real dataset and was executed successfully (`python main.py`, ~19.4 s: 541,909 raw rows -> 524,878 working rows -> 4,338 customers -> five segments -> statistics -> four charts -> Phase 11 report). Remaining caveats stated honestly: cross-machine reproducibility still depends on the pinned environment installing cleanly from requirements.txt and on data/raw/OnlineRetail.csv being copied intact; Phase 14 documentation consolidation and Phase 15 final review / viva artifacts remain pending (Section 7).

## 7. Missing Components Required Before Month 3 Is Executable

ALL FIFTEEN WBS PHASES ARE NOW COMPLETE (Phases 1–14 as recorded above, plus Phase 15:
final review, verification, presentation readiness, viva preparation and release check).
There are no remaining pending deliverables from the approved 15-phase WBS. The only
items reserved for the academic institution are instructor-side reviews (e.g., exact CO
wording confirmation), which are documented in the README Phase 15 record.
