"""visualization.py — Phase 10: Data Visualization.

This module implements the approved Phase 10 scope only. It builds the minimum
required visualizations derived from the actual Phase 6-9 analytical outputs
(real project data) and saves them as PNG charts into the existing
``outputs/charts/`` directory (via ``config.CHARTS_DIR``).

Provided plots (one deterministic chart per function):
    - plot_rfm_score_distributions(...)  -> rfm_score_distributions.png
        Three-panel histogram of the customer-level recency / frequency /
        monetary scores (1..5) from the Phase 7 RFM output.
    - plot_segment_size_bar(...)          -> segment_size_bar.png
        Bar chart of the Phase 8 customer segment sizes.
    - plot_segment_monetary_box(...)      -> segment_monetary_box.png
        Box plot (customer-level) of Monetary by segment.
    - plot_rfm_metric_correlation_scatter(...) -> rfm_metric_correlation_scatter.png
        Scatter grid of the RFM metrics (recency_days, frequency, monetary)
        coloured by segment.

All chart functions are deterministic (fixed figure sizes, fixed colors and a
fixed ``random_state`` seed), do not mutate their input, validate required
columns / empty input (raising ``ValueError`` consistent with the
Phase 6-9 module style), use only the approved matplotlib / seaborn stack and
write into the existing ``outputs/charts/`` directory. No new output directory
is created; no Phase 11 insights / Phase 13 integration logic is added.
"""

from __future__ import annotations

import pathlib

import matplotlib

# Headless PNG backend: no interactive display is required for project charts.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import config

# Chart output directory (existing approved location; config.CHARTS_DIR).
CHARTS_DIR = pathlib.Path(config.CHARTS_DIR)

# Required Phase 10 input columns.
REQUIRED_SEGMENTED_COLUMNS = (
    "CustomerID",
    "recency_days",
    "frequency",
    "monetary",
    "recency_score",
    "frequency_score",
    "monetary_score",
    "segment",
)

# Deterministic plotting configuration.
FIGURE_WIDTH = 12.0
FIGURE_HEIGHT = 4.0

# Segment display order (best segment first, matching src.segmentation).
SEGMENT_ORDER = [
    "Champions",
    "Loyal Customers",
    "Average Customers",
    "At-Risk Customers",
    "Lost Customers",
]
PALETTE = "viridis"
SCATTER_ALPHA = 0.25
SCATTER_SIZE = 12


def _validate_segmented(segmented):
    """Validate a segmented customer table for Phase 10 visualization.

    Raises ``ValueError`` for None/empty input or missing required columns,
    mirroring the error style used by the other ``src`` modules.
    """
    if segmented is None or segmented.empty:
        raise ValueError(
            "A non-empty segmented customer table is required for Phase 10 visualization."
        )
    missing = sorted(set(REQUIRED_SEGMENTED_COLUMNS) - set(segmented.columns))
    if missing:
        raise ValueError(f"Phase 10 visualization input is missing required columns: {missing}")


def _ensure_charts_dir():
    """Ensure the existing ``outputs/charts/`` directory exists.

    Uses ``config.CHARTS_DIR`` (no new directory created); a missing directory
    is created because ``outputs/charts/`` is an approved project directory.
    """
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    return CHARTS_DIR


def _finalize_figure(fig, filename, tight=True):
    """Save a figure into ``outputs/charts/`` and return the resolved path.

    The figure is rendered to a PNG file with a fixed ``dpi`` and then closed.
    """
    out_dir = _ensure_charts_dir()
    output_path = out_dir / filename
    if tight:
        fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def build_phase10_visualization_input(dataframe=None):
    """Return the Phase 10 analytical dataset from the real project flow.

    Consumes the existing Phase 5 -> Phase 7 -> Phase 8 pipeline via
    ``src.statistics_analysis.build_phase9_statistical_input`` and returns the
    segmented customer table (one row per ``CustomerID`` with RFM metrics,
    scores and the ``segment`` column). No analysis is duplicated here.

    Args:
        dataframe (pandas.DataFrame, optional): transaction-level dataset. When
            None, the approved Phase 5 working dataset is loaded and the real
            Phase 7/8 pipeline runs on it.
    """
    from src.statistics_analysis import build_phase9_statistical_input

    return build_phase9_statistical_input(dataframe=dataframe)["segmented_table"]


def plot_rfm_score_distributions(segmented=None):
    """Plot customer-level Recency / Frequency / Monetary score distributions.

    Three-panel bar chart of how many customers hold each 1..5 score for the
    three Phase 7 RFM scores. Deterministic: fixed figure size, fixed colors,
    bars ordered by score value.

    Args:
        segmented (pandas.DataFrame, optional): Phase 8 segmented table. When
            None, the real Phase 5/7/8 pipeline output is used.

    Returns:
        pathlib.Path: path of the saved PNG in ``outputs/charts/``.
    """
    if segmented is None:
        segmented = build_phase10_visualization_input()
    _validate_segmented(segmented)

    panels = [
        ("recency_score", "Recency score"),
        ("frequency_score", "Frequency score"),
        ("monetary_score", "Monetary score"),
    ]
    fig, axes = plt.subplots(
        1, len(panels), figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), sharey=True
    )
    for ax, (column, title) in zip(axes, panels):
        counts = segmented[column].value_counts().sort_index()
        ax.bar([str(int(value)) for value in counts.index], counts.values)
        ax.set_title(title)
        ax.set_xlabel("Score (1..5)")
    axes[0].set_ylabel("Customers")
    fig.suptitle("RFM Score Distributions (customer level)")
    return _finalize_figure(fig, "rfm_score_distributions.png")


def plot_segment_size_bar(segmented=None):
    """Plot the number of customers per Phase 8 segment as a bar chart.

    Deterministic: segments are always drawn in the approved order (best first)
    with a fixed palette; each bar is annotated with its customer count.

    Args:
        segmented (pandas.DataFrame, optional): Phase 8 segmented table. When
            None, the real Phase 5/7/8 pipeline output is used.

    Returns:
        pathlib.Path: path of the saved PNG in ``outputs/charts/``.
    """
    if segmented is None:
        segmented = build_phase10_visualization_input()
    _validate_segmented(segmented)

    sizes = {
        segment: int((segmented["segment"] == segment).sum())
        for segment in SEGMENT_ORDER
    }
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    colors = sns.color_palette(PALETTE, len(SEGMENT_ORDER))
    bars = ax.bar(list(sizes.keys()), list(sizes.values()), color=colors)
    for bar, value in zip(bars, sizes.values()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            str(value),
            ha="center",
            va="bottom",
        )
    ax.set_ylabel("Customers")
    ax.set_title("Customer Segment Sizes")
    return _finalize_figure(fig, "segment_size_bar.png")


def plot_segment_monetary_box(segmented=None):
    """Plot the distribution of customer Monetary value per segment.

    Box plot (customer level) of Monetary by Phase 8 segment, with outliers
    hidden so the segment boxes stay readable on the heavily skewed real
    Monetary distribution. Deterministic: fixed order (best segment first) and
    fixed palette.

    Args:
        segmented (pandas.DataFrame, optional): Phase 8 segmented table. When
            None, the real Phase 5/7/8 pipeline output is used.

    Returns:
        pathlib.Path: path of the saved PNG in ``outputs/charts/``.
    """
    if segmented is None:
        segmented = build_phase10_visualization_input()
    _validate_segmented(segmented)

    present = [segment for segment in SEGMENT_ORDER if segment in set(segmented["segment"])]
    data = segmented[segmented["segment"].isin(present)]
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    sns.boxplot(
        data=data,
        x="segment",
        y="monetary",
        hue="segment",
        order=present,
        hue_order=present,
        palette=PALETTE,
        legend=False,
        showfliers=False,
        ax=ax,
    )
    ax.set_xlabel("Segment")
    ax.set_ylabel("Monetary (£)")
    ax.set_title("Customer Monetary Value by Segment (outliers hidden)")
    return _finalize_figure(fig, "segment_monetary_box.png")


def plot_rfm_metric_correlation_scatter(segmented=None):
    """Plot pairwise RFM metric scatter panels coloured by segment.

    Three scatter panels (frequency vs monetary, recency vs monetary,
    recency vs frequency), one point per customer, coloured by Phase 8
    segment. Deterministic: every customer is plotted (no sampling), with a
    fixed palette and fixed marker size / transparency.

    Args:
        segmented (pandas.DataFrame, optional): Phase 8 segmented table. When
            None, the real Phase 5/7/8 pipeline output is used.

    Returns:
        pathlib.Path: path of the saved PNG in ``outputs/charts/``.
    """
    if segmented is None:
        segmented = build_phase10_visualization_input()
    _validate_segmented(segmented)

    pairs = [
        ("frequency", "monetary", "Frequency", "Monetary (£)"),
        ("recency_days", "monetary", "Recency (days)", "Monetary (£)"),
        ("recency_days", "frequency", "Recency (days)", "Frequency"),
    ]
    present = [segment for segment in SEGMENT_ORDER if segment in set(segmented["segment"])]
    colors = dict(zip(SEGMENT_ORDER, sns.color_palette(PALETTE, len(SEGMENT_ORDER))))

    fig, axes = plt.subplots(1, len(pairs), figsize=(15.0, FIGURE_HEIGHT))
    for index, (ax, (x_col, y_col, x_label, y_label)) in enumerate(zip(axes, pairs)):
        for segment in present:
            group = segmented[segmented["segment"] == segment]
            ax.scatter(
                group[x_col],
                group[y_col],
                s=SCATTER_SIZE,
                alpha=SCATTER_ALPHA,
                color=colors[segment],
                label=segment if index == 0 else None,
            )
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(f"{y_label} vs {x_label}")
    axes[0].legend(loc="upper right", fontsize=8)
    fig.suptitle("RFM Metric Relationships by Segment")
    return _finalize_figure(fig, "rfm_metric_correlation_scatter.png")


def build_phase10_visualizations(dataframe=None):
    """Build every approved Phase 10 chart on real data and save them.

    Runs the real Phase 5 -> Phase 7 -> Phase 8 pipeline (when ``dataframe``
    is None) and renders all four approved Phase 10 visualizations into
    ``outputs/charts/``, returning their saved paths.

    Args:
        dataframe (pandas.DataFrame, optional): transaction-level dataset.
            When None, the approved Phase 5 working dataset is used.

    Returns:
        dict: mapping chart name -> saved PNG path:
            - "rfm_score_distributions"      -> rfm_score_distributions.png
            - "segment_size_bar"             -> segment_size_bar.png
            - "segment_monetary_box"         -> segment_monetary_box.png
            - "rfm_metric_correlation_scatter" ->
              rfm_metric_correlation_scatter.png
    """
    segmented = build_phase10_visualization_input(dataframe=dataframe)
    return {
        "rfm_score_distributions": plot_rfm_score_distributions(segmented),
        "segment_size_bar": plot_segment_size_bar(segmented),
        "segment_monetary_box": plot_segment_monetary_box(segmented),
        "rfm_metric_correlation_scatter": plot_rfm_metric_correlation_scatter(segmented),
    }
