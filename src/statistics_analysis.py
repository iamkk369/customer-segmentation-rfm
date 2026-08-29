"""statistics_analysis.py — Phase 6 EDA + Phase 9 Statistical Analysis.

This module implements two scoped responsibilities on real project data:

    Phase 6 — Exploratory Data Analysis (EDA) for the approved project
    dataset: descriptive, dataset-level, distribution, relationship and
    monthly-trend summaries. All Phase 6 functions are preserved unchanged.

    Phase 9 — Statistical Analysis on the customer / RFM / segment data:
    Pearson and Spearman correlation statistics among the RFM metrics,
    normality assessment (D'Agostino-Pearson omnibus), per-segment
    descriptive profiles, and non-parametric comparison tests
    (Kruskal-Wallis H across segments; Mann-Whitney U pair-wise), computed
    on the real Phase 7 RFM output and the Phase 8 segmentation output.

The Phase 9 procedures are deterministic and use only the approved
libraries (scipy.stats on top of the existing pandas pipeline). No RFM is
recomputed and no Phase 10 visualization / Phase 11 insight logic is added.
"""

from __future__ import annotations

import itertools

import pandas as pd
from scipy import stats

import config
from src.segmentation import SEGMENT_NAMES, build_segmentation

PHASE6_DATASET_FILENAME = "OnlineRetail_invalid_removed.csv"


def _get_phase6_dataset_path():
    """Return the path to the approved Phase 5 working dataset."""
    return (config.PROCESSED_DATA_DIR / PHASE6_DATASET_FILENAME).resolve()


def load_phase6_dataset():
    """Load the approved working dataset for exploratory analysis.

    The dataset used here is the project-approved Phase 5 output, not the raw
    source file. This keeps the EDA read-only and aligned to the specialist
    Phase 6 responsibility area.
    """
    dataset_path = _get_phase6_dataset_path()
    if not dataset_path.is_file():
        raise FileNotFoundError(
            f"Phase 6 dataset not found: {dataset_path}. "
            "Please complete the Phase 5 workflow before running EDA."
        )
    return pd.read_csv(dataset_path, parse_dates=["InvoiceDate"], low_memory=False)


def _calculate_transaction_revenue(dataframe):
    """Return the monetary value of each row in the transaction dataset."""
    return dataframe["Quantity"] * dataframe["UnitPrice"]


def get_dataset_summary(dataframe=None):
    """Return the descriptive, dataset-level summary for Phase 6.1.

    The summary is derived from the approved working dataset and includes the
    dataset dimensions, customer/invoice counts, timeframe, and revenue/quantity
    averages used in the project EDA checks.
    """
    if dataframe is None:
        dataframe = load_phase6_dataset()

    revenue = _calculate_transaction_revenue(dataframe)
    summary = {
        "row_count": int(len(dataframe)),
        "unique_customers": int(dataframe["CustomerID"].nunique()),
        "unique_invoices": int(dataframe["InvoiceNo"].nunique()),
        "unique_countries": int(dataframe["Country"].nunique()),
        "observation_start": dataframe["InvoiceDate"].min(),
        "observation_end": dataframe["InvoiceDate"].max(),
        "total_revenue": float(revenue.sum()),
        "avg_quantity_per_transaction": float(dataframe["Quantity"].mean()),
        "avg_unit_price": float(dataframe["UnitPrice"].mean()),
    }
    summary["top_countries_by_revenue"] = get_top_countries_by_revenue(dataframe)
    return summary


def get_top_countries_by_revenue(dataframe=None):
    """Return the country revenue totals sorted descending."""
    if dataframe is None:
        dataframe = load_phase6_dataset()

    revenue_by_country = (
        dataframe.assign(revenue=_calculate_transaction_revenue(dataframe))
        .groupby("Country", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )
    return {
        row["Country"]: float(row["revenue"])
        for _, row in revenue_by_country.iterrows()
    }


def summarize_numeric_distributions(dataframe=None):
    """Return the distribution summary for Quantity and UnitPrice.

    The result mirrors the required EDA statistics used for Phase 6.2 and keeps
    the values in the same format expected by project tests and reports.
    """
    if dataframe is None:
        dataframe = load_phase6_dataset()

    quantity_summary = dataframe["Quantity"].describe().to_dict()
    unit_price_summary = dataframe["UnitPrice"].describe().to_dict()
    return {
        "quantity": {
            "count": float(quantity_summary["count"]),
            "mean": float(quantity_summary["mean"]),
            "std": float(quantity_summary["std"]),
            "min": float(quantity_summary["min"]),
            "q1": float(quantity_summary["25%"]),
            "median": float(quantity_summary["50%"]),
            "q3": float(quantity_summary["75%"]),
            "max": float(quantity_summary["max"]),
        },
        "unit_price": {
            "count": float(unit_price_summary["count"]),
            "mean": float(unit_price_summary["mean"]),
            "std": float(unit_price_summary["std"]),
            "min": float(unit_price_summary["min"]),
            "q1": float(unit_price_summary["25%"]),
            "median": float(unit_price_summary["50%"]),
            "q3": float(unit_price_summary["75%"]),
            "max": float(unit_price_summary["max"]),
        },
    }


def summarize_monthly_trends(dataframe=None):
    """Return the monthly transaction count and revenue trend for Phase 6.2."""
    if dataframe is None:
        dataframe = load_phase6_dataset()

    monthly = (
        dataframe.assign(
            month=dataframe["InvoiceDate"].dt.to_period("M").astype(str),
            revenue=_calculate_transaction_revenue(dataframe),
        )
        .groupby("month")
        .agg(
            transactions=("InvoiceNo", "nunique"),
            revenue=("revenue", "sum"),
        )
        .sort_index()
    )
    return {
        month: {"transactions": int(row["transactions"]), "revenue": float(row["revenue"])}
        for month, row in monthly.iterrows()
    }


def summarize_relationships(dataframe=None):
    """Return Pearson relationships among transaction-level numeric measures.

    Revenue is derived from the approved transaction fields. No values are
    changed in the supplied DataFrame and no customer-level aggregation is
    introduced, keeping this analysis within Phase 6.
    """
    if dataframe is None:
        dataframe = load_phase6_dataset()

    relationship_frame = dataframe[["Quantity", "UnitPrice"]].copy()
    relationship_frame["revenue"] = _calculate_transaction_revenue(dataframe)
    return relationship_frame.corr(method="pearson").to_dict()


def build_phase6_eda_summary(dataframe=None):
    """Return a complete Phase 6 EDA summary object for downstream use."""
    if dataframe is None:
        dataframe = load_phase6_dataset()
    return {
        "dataset_summary": get_dataset_summary(dataframe),
        "distribution_summary": summarize_numeric_distributions(dataframe),
        "relationship_summary": summarize_relationships(dataframe),
        "monthly_trends": summarize_monthly_trends(dataframe),
    }


# ---------------------------------------------------------------------------
# Phase 9 — Statistical Analysis (customer / RFM / segment data)
# ---------------------------------------------------------------------------

PHASE9_METRIC_COLUMNS = ("recency_days", "frequency", "monetary")
PHASE9_REQUIRED_COLUMNS = ("CustomerID", "recency_days", "frequency", "monetary", "segment")


def _validate_phase9_input(segmented):
    """Validate a Phase 8 segmented customer table for Phase 9 statistics.

    Raises ``ValueError`` for None/empty input, missing required columns, or
    non-numeric RFM metric columns, mirroring the Phase 6/7/8 module style.
    """
    if segmented is None or segmented.empty:
        raise ValueError(
            "A non-empty segmented customer table is required for Phase 9 statistics."
        )

    missing = sorted(set(PHASE9_REQUIRED_COLUMNS) - set(segmented.columns))
    if missing:
        raise ValueError(f"Phase 9 statistical input is missing required columns: {missing}")

    for column in PHASE9_METRIC_COLUMNS:
        if not pd.api.types.is_numeric_dtype(segmented[column]):
            raise ValueError(
                f"Phase 9 statistical column '{column}' must be numeric."
            )


def build_phase9_statistical_input(dataframe=None):
    """Build the Phase 9 analytical dataset from the real Phase 5/7/8 flow.

    Runs the existing Phase 7 RFM pipeline and the Phase 8 segmentation on the
    approved working dataset and returns the full segmentation result
    (``dataset``, ``rfm_table``, ``segmented_table``, ``segment_summary``).
    No RFM / segmentation logic is duplicated here.
    """
    return build_segmentation(dataframe=dataframe)


def summarize_statistical_correlations(segmented=None):
    """Return Pearson and Spearman correlations among the RFM metrics.

    For each pair of customer-level RFM metrics (recency_days, frequency,
    monetary) the function returns the Pearson (linear) and Spearman
    (monotonic) correlation coefficients with their two-sided p-values.

    Args:
        segmented (pandas.DataFrame, optional): Phase 8 segmented table with
            RFM metrics and a ``segment`` column. When None, the real Phase 8
            segmentation output is built from the approved working dataset.

    Returns:
        dict: ``{"<ma>_vs_<mb>": {"n", "pearson_r", "pearson_p_value",
        "spearman_rho", "spearman_p_value"}}`` for every metric pair.
    """
    if segmented is None:
        segmented = build_phase9_statistical_input()["segmented_table"]
    _validate_phase9_input(segmented)

    result = {}
    for column_a, column_b in itertools.combinations(PHASE9_METRIC_COLUMNS, 2):
        x = segmented[column_a].astype(float)
        y = segmented[column_b].astype(float)
        pearson_r, pearson_p = stats.pearsonr(x, y)
        spearman_rho, spearman_p = stats.spearmanr(x, y)
        result[f"{column_a}_vs_{column_b}"] = {
            "n": int(len(x)),
            "pearson_r": float(pearson_r),
            "pearson_p_value": float(pearson_p),
            "spearman_rho": float(spearman_rho),
            "spearman_p_value": float(spearman_p),
        }
    return result


def summarize_normality_tests(segmented=None):
    """Return the D'Agostino-Pearson omnibus normality assessment.

    The D'Agostino-Pearson test (``scipy.stats.normaltest``) combines sample
    skewness and kurtosis. It supports the Phase 9 choice of non-parametric
    comparison tests for the heavily skewed Frequency / Monetary metrics.

    Args:
        segmented (pandas.DataFrame, optional): Phase 8 segmented table. When
            None, the real Phase 8 segmentation output is built.

    Returns:
        dict: ``{metric: {"n", "test", "statistic", "p_value",
        "is_normal_at_0_05"}}`` for every RFM metric column.
    """
    if segmented is None:
        segmented = build_phase9_statistical_input()["segmented_table"]
    _validate_phase9_input(segmented)

    result = {}
    for column in PHASE9_METRIC_COLUMNS:
        statistic, p_value = stats.normaltest(segmented[column].astype(float))
        result[column] = {
            "n": int(len(segmented)),
            "test": "D'Agostino-Pearson omnibus",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "is_normal_at_0_05": bool(p_value >= 0.05),
        }
    return result
def summarize_segment_profiles(segmented=None):
    """Return per-segment descriptive statistics for Frequency and Monetary.

    For every approved segment (in ``SEGMENT_NAMES`` order) the function
    returns the segment size and the mean / median / standard deviation of the
    customer-level Frequency and Monetary metrics, enabling direct comparison
    of segment behaviour on the real data.

    Args:
        segmented (pandas.DataFrame, optional): Phase 8 segmented table. When
            None, the real Phase 8 segmentation output is built.

    Returns:
        dict: ``{segment_name: {"customer_count", "frequency_mean",
        "frequency_median", "frequency_std", "monetary_mean",
        "monetary_median", "monetary_std"}}``.
    """
    if segmented is None:
        segmented = build_phase9_statistical_input()["segmented_table"]
    _validate_phase9_input(segmented)

    profiles = {}
    for segment_name in SEGMENT_NAMES:
        group = segmented[segmented["segment"] == segment_name]
        profiles[segment_name] = {
            "customer_count": int(len(group)),
            "frequency_mean": float(group["frequency"].mean()),
            "frequency_median": float(group["frequency"].median()),
            "frequency_std": float(group["frequency"].std()),
            "monetary_mean": float(group["monetary"].mean()),
            "monetary_median": float(group["monetary"].median()),
            "monetary_std": float(group["monetary"].std()),
        }
    return profiles


def summarize_segment_comparison_tests(segmented=None):
    """Return non-parametric comparison tests across the customer segments.

    Two deterministic procedures are provided:
    - Kruskal-Wallis H test (non-parametric one-way ANOVA) comparing the
      Frequency and Monetary distributions across all five segments.
    - Mann-Whitney U tests (pair-wise) comparing Frequency and Monetary
      between the best segment (Champions) and the worst (Lost Customers).

    Non-parametric tests are appropriate for the skewed RFM metric
    distributions confirmed by the Phase 9 normality assessment.

    Args:
        segmented (pandas.DataFrame, optional): Phase 8 segmented table. When
            None, the real Phase 8 segmentation output is built.

    Returns:
        dict: keys ``frequency_kruskal_wallis`` and ``monetary_kruskal_wallis``
        (each ``{"test", "groups", "df", "statistic", "p_value"}``) plus, when
        both Champions and Lost Customers are present,
        ``champions_vs_lost_frequency_mannwhitney`` and
        ``champions_vs_lost_monetary_mannwhitney`` (each
        ``{"test", "n_champions", "n_lost", "statistic", "p_value"}``).

    Raises:
        ValueError: if fewer than two non-empty segments, or any compared
        segment has fewer than two customers.
    """
    if segmented is None:
        segmented = build_phase9_statistical_input()["segmented_table"]
    _validate_phase9_input(segmented)

    present_segments = [
        name for name in SEGMENT_NAMES if (segmented["segment"] == name).any()
    ]
    if len(present_segments) < 2:
        raise ValueError(
            "Phase 9 segment comparison requires at least two non-empty segments."
        )
    for name in present_segments:
        if int((segmented["segment"] == name).sum()) < 2:
            raise ValueError(
                "Phase 9 segment comparison requires at least 2 customers per "
                f"segment ('{name}' has fewer)."
            )

    groups_frequency = [
        segmented.loc[segmented["segment"] == name, "frequency"].astype(float)
        for name in present_segments
    ]
    groups_monetary = [
        segmented.loc[segmented["segment"] == name, "monetary"].astype(float)
        for name in present_segments
    ]
    frequency_h, frequency_p = stats.kruskal(*groups_frequency)
    monetary_h, monetary_p = stats.kruskal(*groups_monetary)

    result = {
        "frequency_kruskal_wallis": {
            "test": "Kruskal-Wallis H",
            "groups": len(present_segments),
            "df": len(present_segments) - 1,
            "statistic": float(frequency_h),
            "p_value": float(frequency_p),
        },
        "monetary_kruskal_wallis": {
            "test": "Kruskal-Wallis H",
            "groups": len(present_segments),
            "df": len(present_segments) - 1,
            "statistic": float(monetary_h),
            "p_value": float(monetary_p),
        },
    }
    if "Champions" in present_segments and "Lost Customers" in present_segments:
        champions = segmented[segmented["segment"] == "Champions"]
        lost = segmented[segmented["segment"] == "Lost Customers"]
        mw_frequency_u, mw_frequency_p = stats.mannwhitneyu(
            champions["frequency"].astype(float),
            lost["frequency"].astype(float),
            alternative="two-sided",
        )
        mw_monetary_u, mw_monetary_p = stats.mannwhitneyu(
            champions["monetary"].astype(float),
            lost["monetary"].astype(float),
            alternative="two-sided",
        )
        result["champions_vs_lost_frequency_mannwhitney"] = {
            "test": "Mann-Whitney U",
            "n_champions": int(len(champions)),
            "n_lost": int(len(lost)),
            "statistic": float(mw_frequency_u),
            "p_value": float(mw_frequency_p),
        }
        result["champions_vs_lost_monetary_mannwhitney"] = {
            "test": "Mann-Whitney U",
            "n_champions": int(len(champions)),
            "n_lost": int(len(lost)),
            "statistic": float(mw_monetary_u),
            "p_value": float(mw_monetary_p),
        }
    return result


def build_phase9_statistical_summary(dataframe=None):
    """Return the complete Phase 9 statistical summary for downstream use.

    Builds the real Phase 5 -> Phase 7 -> Phase 8 analytical dataset and then
    runs every Phase 9 statistical procedure (correlations, normality tests,
    segment profiles, segment comparison tests) on it. The result is returned
    in memory; no permanent Phase 9 output file is produced.
    """
    analytical = build_phase9_statistical_input(dataframe=dataframe)
    segmented = analytical["segmented_table"]
    return {
        "dataset": analytical["dataset"],
        "rfm_table": analytical["rfm_table"],
        "segmented_table": segmented,
        "segment_summary": analytical["segment_summary"],
        "correlations": summarize_statistical_correlations(segmented),
        "normality_tests": summarize_normality_tests(segmented),
        "segment_profiles": summarize_segment_profiles(segmented),
        "segment_comparison_tests": summarize_segment_comparison_tests(segmented),
    }
