"""segmentation.py — Phase 8: Customer Segmentation.

This module implements the approved Phase 8 scope only:
- Deterministic, interpretable RFM score-based customer segmentation.
- Segment assignment based on the 1..5 RFM scores produced by Phase 7
  (recency_score, frequency_score, monetary_score).
- Integration that consumes the existing Phase 7 RFM customer-level output
  (no RFM re-calculation and no clustering is performed here).
- In-memory segment summary for analysis / reporting.

Segmentation methodology (recorded in README Phase 8):
    Each customer's three 1..5 RFM scores are summed into a combined score
    ``rfm_total`` (range 3..15). The combined score is mapped to exactly one
    named segment through fixed, documented thresholds. The mapping is fully
    deterministic: identical RFM scores always receive the same segment.

    Segment thresholds (approved Phase 8):
        13 .. 15  →  Champions
        10 .. 12  →  Loyal Customers
        7 .. 9    →  Average Customers
        4 .. 6    →  At-Risk Customers
        3 .. 3    →  Lost Customers

Every customer receives exactly one segment.
No permanent CSV / report / chart is produced (no explicit output
requirement exists in the project repository).
"""

from __future__ import annotations

import pandas as pd

from src.rfm_analysis import build_rfm_analysis

# Required Phase 8 input columns (the Phase 7 scored RFM customer table).
REQUIRED_SEGMENT_COLUMNS = ("CustomerID", "recency_score", "frequency_score", "monetary_score")

# RFM score columns used to compute the combined segmentation total.
SCORE_COLUMNS = ("recency_score", "frequency_score", "monetary_score")

# Approved Phase 8 segment thresholds (documented; see module docstring).
SEGMENT_MIN_RFM_TOTAL = 13  # Champions
SEGMENT_LOYAL_RFM_TOTAL = 10  # Loyal Customers
SEGMENT_AVERAGE_MIN_RFM_TOTAL = 7  # Average Customers
SEGMENT_AT_RISK_MIN_RFM_TOTAL = 4  # At-Risk Customers
# rfm_total below SEGMENT_AT_RISK_MIN_RFM_TOTAL -> Lost Customers

SEGMENT_NAMES = (
    "Champions",
    "Loyal Customers",
    "Average Customers",
    "At-Risk Customers",
    "Lost Customers",
)


def _segment_name(rfm_total):
    """Return the single segment name for a combined RFM total score.

    Pure function of ``rfm_total`` (3..15). Lower rfm_total → worse segment.
    """
    if rfm_total >= SEGMENT_MIN_RFM_TOTAL:
        return "Champions"
    if rfm_total >= SEGMENT_LOYAL_RFM_TOTAL:
        return "Loyal Customers"
    if rfm_total >= SEGMENT_AVERAGE_MIN_RFM_TOTAL:
        return "Average Customers"
    if rfm_total >= SEGMENT_AT_RISK_MIN_RFM_TOTAL:
        return "At-Risk Customers"
    return "Lost Customers"


def _validate_scored_input(scored_rfm_table):
    """Validate a Phase 7 scored RFM input for segmentation.

    Raises ``ValueError`` for None/empty input, missing required columns,
    a missing ``CustomerID``, or non-numeric RFM scores. Mirrors the error
    style used by ``src.rfm_analysis`` and ``src.statistics_analysis``.
    """
    if scored_rfm_table is None or scored_rfm_table.empty:
        raise ValueError("A non-empty scored RFM table is required for segmentation.")

    required = set(REQUIRED_SEGMENT_COLUMNS)
    missing = sorted(required - set(scored_rfm_table.columns))
    if missing:
        raise ValueError(f"Segmentation input is missing required columns: {missing}")

    for column in SCORE_COLUMNS:
        if not pd.api.types.is_numeric_dtype(scored_rfm_table[column]):
            raise ValueError(
                f"Segmentation score column '{column}' must be numeric."
            )


def assign_customer_segments(scored_rfm_table):
    """Assign exactly one segment to each customer in a scored RFM table.

    Args:
        scored_rfm_table (pandas.DataFrame): Phase 7 scored RFM customer-level
            table. Must contain ``CustomerID``, ``recency_score``,
            ``frequency_score``, ``monetary_score`` (one row per CustomerID).

    Returns:
        pandas.DataFrame: A copy of the input with a new ``segment`` column
        added (one row per CustomerID). The source table is not modified.

    Raises:
        ValueError: If the input is empty, missing a required column /
            ``CustomerID``, or contains non-numeric RFM scores.
    """
    _validate_scored_input(scored_rfm_table)

    working = scored_rfm_table.copy()
    working["_rfm_total"] = working[list(SCORE_COLUMNS)].sum(axis=1)
    working["segment"] = working["_rfm_total"].apply(_segment_name)
    return working.drop(columns=["_rfm_total"])


def build_segmentation(dataframe=None):
    """Build the full Phase 8 segmentation result from the real Phase 7 output.

    Consumes the existing Phase 7 RFM result
    (``src.rfm_analysis.build_rfm_analysis``) and segments all customers.
    No RFM calculation is duplicated here.

    Args:
        dataframe (pandas.DataFrame, optional): transaction-level dataset. When
            None, the approved Phase 5 working dataset
            (``data/processed/OnlineRetail_invalid_removed.csv``) is loaded and
            the Phase 7 RFM pipeline runs on the real data.

    Returns:
        dict: ``{"dataset", "rfm_table", "segmented_table", "segment_summary"}``
        where ``segmented_table`` is the scored RFM table with the added
        ``segment`` column and ``segment_summary`` is the segment count dict.
    """
    rfm_result = build_rfm_analysis(dataframe=dataframe)
    segmented = assign_customer_segments(rfm_result["rfm_table"])
    summary = summarize_segments(segmented)
    return {
        "dataset": rfm_result["dataset"],
        "rfm_table": rfm_result["rfm_table"],
        "segmented_table": segmented,
        "segment_summary": summary,
    }


def summarize_segments(segmented):
    """Return an in-memory count summary of assigned segments.

    Args:
        segmented (pandas.DataFrame): segmented table (must contain a
            ``segment`` column).

    Returns:
        dict: mapping ``{segment_name: count}`` in the approved segment order
        (best segment first).

    Raises:
        ValueError: If the input is empty or missing the ``segment`` column.
    """
    if segmented is None or segmented.empty:
        raise ValueError("A non-empty segmented table is required for a summary.")
    if "segment" not in segmented.columns:
        raise ValueError("Segmented table is missing the required 'segment' column.")

    return {
        segment: int((segmented["segment"] == segment).sum()) for segment in SEGMENT_NAMES
    }
