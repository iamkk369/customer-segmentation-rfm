"""rfm_analysis.py — Phase 7: RFM Calculation.

This module implements the approved Phase 7 scope only:
- Recency calculation
- Frequency calculation
- Monetary calculation
- Customer-level RFM table
- RFM scoring

No segmentation logic is implemented here.
"""

from __future__ import annotations

import math

import pandas as pd

import config

PHASE7_DATASET_FILENAME = "OnlineRetail_invalid_removed.csv"


def _get_phase7_dataset_path():
    """Return the approved Phase 5 final working dataset for Phase 7."""
    return (config.PROCESSED_DATA_DIR / PHASE7_DATASET_FILENAME).resolve()


def load_phase7_dataset():
    """Load the actual final Phase 5 working dataset for RFM analysis."""
    dataset_path = _get_phase7_dataset_path()
    if not dataset_path.is_file():
        raise FileNotFoundError(
            f"Phase 7 dataset not found: {dataset_path}. "
            "Expected the approved Phase 5 output in data/processed/."
        )
    return pd.read_csv(dataset_path, parse_dates=["InvoiceDate"], low_memory=False)


def _calculate_transaction_revenue(dataframe):
    """Return row-level monetary value using Quantity * UnitPrice."""
    return dataframe["Quantity"] * dataframe["UnitPrice"]


def calculate_customer_rfm(dataframe=None, reference_date=None):
    """Return the customer-level RFM table.

    The dataset is the real approved Phase 5 working dataset. A single row is
    produced per customer with:
    - CustomerID
    - last_purchase
    - recency_days
    - frequency
    - monetary

    The project uses the latest transaction date in the working dataset as the
    reference date unless a caller supplies an explicit value.
    """
    if dataframe is None:
        dataframe = load_phase7_dataset()

    # InvoiceNo is required because the approved Frequency metric counts
    # DISTINCT orders (InvoiceNo) per customer.
    required_columns = {"CustomerID", "InvoiceDate", "Quantity", "UnitPrice", "InvoiceNo"}
    missing = sorted(required_columns - set(dataframe.columns))
    if missing:
        raise ValueError(f"Phase 7 input is missing required columns: {missing}")

    if len(dataframe) == 0:
        raise ValueError(
            "Phase 7 input is empty; a non-empty transaction dataset is required."
        )

    working = dataframe.copy()
    working["revenue"] = _calculate_transaction_revenue(working)
    if reference_date is None:
        reference_date = working["InvoiceDate"].max()

    customer_metrics = (
        working.groupby("CustomerID", as_index=False)
        .agg(
            last_purchase=("InvoiceDate", "max"),
            frequency=("InvoiceNo", "nunique"),
            monetary=("revenue", "sum"),
        )
        .sort_values("CustomerID")
        .reset_index(drop=True)
    )

    customer_metrics["recency_days"] = (
        pd.Timestamp(reference_date) - customer_metrics["last_purchase"]
    ).dt.days

    return customer_metrics[
        ["CustomerID", "last_purchase", "recency_days", "frequency", "monetary"]
    ].reset_index(drop=True)


def _score_values(values, higher_is_better=True):
    """Assign a deterministic 1..5 score to values, preserving ties.

    Approved Phase 7 scoring behavior:
    - Scores are integers in the range 1..5.
    - When ``higher_is_better=True`` (Frequency, Monetary), larger raw values
      receive higher scores.
    - When ``higher_is_better=False`` (Recency), smaller raw values receive
      higher scores (lower recency_days is better).
    - Identical raw values ALWAYS receive the identical score (tie rule):
      each value's score depends only on the counts of values strictly below
      it and up-to-and-including it, never on row order.
    - The mapping is fully deterministic: repeated executions on the same
      input produce identical scores.
    """
    values = pd.Series(values).astype(float)
    if len(values) == 0:
        return pd.Series([], dtype=int)

    # Position of each value in (0, 1], using the midpoint of the fractions of
    # the population strictly below and up-to-and-including the value. Tied
    # values share identical (below, inclusive) counts, hence identical scores.
    below = values.apply(lambda v: int((values < v).sum()))
    inclusive = values.apply(lambda v: int((values <= v).sum()))
    n = len(values)
    position = (below + inclusive) / (2.0 * n)

    scores = (position * 5.0).astype(int) + 1  # maps to 1..5
    scores = scores.clip(1, 5)

    if not higher_is_better:
        # Reverse direction: smaller raw value receives a higher score.
        scores = 6 - scores

    return scores.astype(int).reset_index(drop=True)


def score_rfm_table(rfm_table):
    """Add RFM score columns to a customer-level RFM table."""
    if rfm_table is None or rfm_table.empty:
        raise ValueError("A non-empty customer-level RFM table is required.")

    scored = rfm_table.copy()
    scored["recency_score"] = _score_values(scored["recency_days"], higher_is_better=False)
    scored["frequency_score"] = _score_values(scored["frequency"], higher_is_better=True)
    scored["monetary_score"] = _score_values(scored["monetary"], higher_is_better=True)
    return scored


def build_rfm_analysis(dataframe=None, reference_date=None):
    """Construct the full Phase 7 RFM output for downstream use."""
    if dataframe is None:
        dataframe = load_phase7_dataset()

    rfm_table = calculate_customer_rfm(dataframe=dataframe, reference_date=reference_date)
    scored_table = score_rfm_table(rfm_table)
    return {
        "dataset": dataframe,
        "rfm_table": scored_table,
        "reference_date": pd.Timestamp(reference_date) if reference_date is not None else dataframe["InvoiceDate"].max(),
    }


def summarize_rfm_for_reporting(rfm_table):
    """Return a compact summary used for report generation or validation."""
    if rfm_table is None or rfm_table.empty:
        raise ValueError("A non-empty RFM table is required for reporting.")

    return {
        "customer_count": int(rfm_table["CustomerID"].nunique()),
        "avg_recency_days": float(rfm_table["recency_days"].mean()),
        "avg_frequency": float(rfm_table["frequency"].mean()),
        "avg_monetary": float(rfm_table["monetary"].mean()),
        "min_recency_days": int(rfm_table["recency_days"].min()),
        "max_recency_days": int(rfm_table["recency_days"].max()),
        "median_frequency": float(rfm_table["frequency"].median()),
        "median_monetary": float(rfm_table["monetary"].median()),
    }
