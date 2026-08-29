"""
main.py — Main Entry Point

Project: Customer Segmentation Analysis using RFM Modeling

Responsibility (PHASE 13 — FINAL INTEGRATION):
    This module is the project's entry point and orchestration layer.
    It coordinates the approved end-to-end workflow across the existing
    ``src/`` modules WITHOUT duplicating any business logic:

        Phase 4  Data Loading            -> src.data_loading
        Phase 5  Data Cleaning           -> src.data_cleaning
        Phase 6  EDA                     -> src.statistics_analysis (Phase 6 part)
        Phase 7  RFM Analysis            -> src.rfm_analysis
        Phase 8  Customer Segmentation   -> src.segmentation
        Phase 9  Statistical Analysis    -> src.statistics_analysis (Phase 9 part)
        Phase 10 Visualization           -> src.visualization
        Phase 11 Insights & Findings     -> src.insights

    Every stage reuses the existing public functions exactly as validated by
    the Phase 12 suites (480 tests). No RFM is recalculated independently,
    no segmentation rule is duplicated, no alternative cleaning pipeline or
    insights module is introduced here.

Output locations come from ``config.py`` (data/processed/, outputs/charts/,
outputs/reports/) exactly as used by the individual phases.

Usage:
    .venv\\Scripts\\python.exe main.py            # run the full pipeline
"""

from __future__ import annotations

import sys
import time

import config
from src.data_loading import load_raw_dataset
from src.data_cleaning import (
    handle_missing_values,
    remove_duplicates,
    remove_invalid_records,
    save_invalid_removed_dataset,
)
from src.rfm_analysis import build_rfm_analysis
from src.segmentation import assign_customer_segments, summarize_segments
from src.statistics_analysis import (
    build_phase6_eda_summary,
    summarize_normality_tests,
    summarize_segment_comparison_tests,
    summarize_segment_profiles,
    summarize_statistical_correlations,
)
from src.visualization import (
    plot_rfm_metric_correlation_scatter,
    plot_rfm_score_distributions,
    plot_segment_monetary_box,
    plot_segment_size_bar,
)
from src.insights import (
    build_phase11_insights,
    render_phase11_insights_markdown,
)


def _log(message):
    """Print a concise pipeline progress line."""
    print(message, flush=True)


def run_full_pipeline():
    """Execute the complete approved analysis workflow end-to-end.

    Returns:
        dict: per-stage results keyed by stage name, containing the real
        intermediate outputs produced by the existing phase functions.
    """
    started = time.perf_counter()
    results = {}

    # ------------------------------------------------------------------
    # PHASE 4 — DATA LOADING
    # ------------------------------------------------------------------
    _log("[1/8] Phase 4 - loading raw dataset ...")
    raw = load_raw_dataset()
    results["raw_rows"] = int(len(raw))
    _log(f"      loaded {results['raw_rows']:,} rows x {len(raw.columns)} columns")

    # ------------------------------------------------------------------
    # PHASE 5 — CLEANING & PREPARATION (established order 5.1 -> 5.2 -> 5.3)
    # ------------------------------------------------------------------
    _log("[2/8] Phase 5 - cleaning: missing values, duplicates, invalid records ...")
    cleaned = handle_missing_values(raw)

    deduplicated = remove_duplicates(cleaned)

    working = remove_invalid_records(deduplicated)
    path_working = save_invalid_removed_dataset(dataframe=working)

    results["cleaning"] = {
        "working_path": path_working,
        "working_rows": int(len(working)),
    }
    _log(f"      working dataset: {results['cleaning']['working_rows']:,} rows "
         f"-> {path_working.name}")

    # ------------------------------------------------------------------
    # PHASE 6 — EXPLORATORY DATA ANALYSIS
    # ------------------------------------------------------------------
    _log("[3/8] Phase 6 - exploratory data analysis ...")
    eda = build_phase6_eda_summary(dataframe=working)
    results["eda"] = eda
    _log("      EDA summary sections: " + ", ".join(sorted(eda)))

    # ------------------------------------------------------------------
    # PHASE 7 — RFM CALCULATION + SCORING
    # ------------------------------------------------------------------
    _log("[4/8] Phase 7 - RFM calculation and scoring ...")
    rfm = build_rfm_analysis(dataframe=working)
    scored_table = rfm["rfm_table"]
    results["rfm"] = rfm
    results["customer_count"] = int(scored_table["CustomerID"].nunique())
    _log(f"      reference date: {rfm['reference_date'].date()} | "
         f"customers: {results['customer_count']:,}")

    # ------------------------------------------------------------------
    # PHASE 8 — CUSTOMER SEGMENTATION (approved rule-based classification)
    # ------------------------------------------------------------------
    _log("[5/8] Phase 8 - customer segmentation ...")
    segmented = assign_customer_segments(scored_table)
    segment_summary = summarize_segments(segmented)
    results["segmented_table"] = segmented
    results["segment_summary"] = segment_summary
    _log("      segments: " + ", ".join(
        f"{name}={count}" for name, count in segment_summary.items()
    ))

    # ------------------------------------------------------------------
    # PHASE 9 — STATISTICAL ANALYSIS
    # ------------------------------------------------------------------
    _log("[6/8] Phase 9 - statistical analysis ...")
    statistical_summary = {
        "dataset": working,
        "rfm_table": scored_table,
        "segmented_table": segmented,
        "segment_summary": segment_summary,
        "correlations": summarize_statistical_correlations(segmented),
        "normality_tests": summarize_normality_tests(segmented),
        "segment_profiles": summarize_segment_profiles(segmented),
        "segment_comparison_tests": summarize_segment_comparison_tests(segmented),
    }
    results["statistical_summary"] = statistical_summary
    _log("      correlations / normality / profiles / comparison tests complete")

    # ------------------------------------------------------------------
    # PHASE 10 — VISUALIZATION (the four approved charts)
    # ------------------------------------------------------------------
    _log("[7/8] Phase 10 - generating approved visualizations ...")
    chart_functions = {
        "rfm_score_distributions": plot_rfm_score_distributions,
        "segment_size_bar": plot_segment_size_bar,
        "segment_monetary_box": plot_segment_monetary_box,
        "rfm_metric_correlation_scatter": plot_rfm_metric_correlation_scatter,
    }
    charts = {name: fn(segmented=segmented)
              for name, fn in chart_functions.items()}
    results["charts"] = charts
    _log(f"      saved {len(charts)} charts to {config.CHARTS_DIR.name}/")

    # ------------------------------------------------------------------
    # PHASE 11 — INSIGHTS & FINDINGS + REPORT (reuses the same Phase 9
    # summary, so nothing downstream is recomputed or duplicated)
    # ------------------------------------------------------------------
    _log("[8/8] Phase 11 - insights, findings and report ...")
    insights = build_phase11_insights(summary=statistical_summary)
    markdown = render_phase11_insights_markdown(insights)

    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = config.REPORTS_DIR / "phase11_insights_report.md"
    report_path.write_text(markdown, encoding="utf-8")

    results["insights_keys"] = sorted(insights)
    results["report_path"] = report_path

    elapsed = time.perf_counter() - started
    results["elapsed_seconds"] = round(elapsed, 1)
    _log(f"      report written -> {report_path}")
    _log(f"Pipeline finished OK in {elapsed:.1f}s")
    return results


def main(argv=None):
    """Entry point for the integrated end-to-end project execution."""
    del argv  # reserved for future CLI options; no CLI scope in the WBS
    try:
        run_full_pipeline()
    except Exception as err:  # top-level integration boundary
        print(f"PIPELINE FAILED: {type(err).__name__}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())