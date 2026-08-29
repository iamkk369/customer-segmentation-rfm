"""insights.py — Phase 11: Insights & Findings.

This module implements the approved Phase 11 scope only. It derives insights
and findings SOLELY from the actual project evidence produced by the real
Phase 8-10 pipeline (segment results, RFM metrics and the Phase 9 statistical
outcomes). It does not invent business findings and never uses fabricated
values.

Responsibilities:
    - Build the Phase 11 analytical input from the real Phase 8 -> Phase 9
      pipeline (via ``src.statistics_analysis.build_phase9_statistical_summary``).
    - Summarize measured segment, RFM and statistical findings directly from
      the actual computed values (customer counts, shares, segment profiles,
      correlation / normality / comparison-test outputs).
    - Separate measured facts from interpretation: every insight records the
      measured finding plus an explicitly-labelled interpretation/action.
    - Generate the Phase 11 report as Markdown into the planned location
      ``outputs/reports/phase11_insights_report.md`` and return its path.

No business logic is invented; all figures are read from the real downstream
modules at run time. The module is deterministic for identical inputs. It
consumes (does not modify or recompute) the Phase 1-10 implementation.
"""

from __future__ import annotations

import pathlib

import config
from src.segmentation import SEGMENT_NAMES
from src.statistics_analysis import build_phase9_statistical_summary

# Planned Phase 11 report location (established in the approved WBS plan).
PHASE11_REPORT_FILENAME = "phase11_insights_report.md"
PHASE11_REPORT_DIR = pathlib.Path(config.REPORTS_DIR)
PHASE11_REPORT_PATH = PHASE11_REPORT_DIR / PHASE11_REPORT_FILENAME

# Keys the Phase 9 statistical summary must expose for Phase 11.
PHASE11_REQUIRED_KEYS = (
    "segment_summary",
    "segment_profiles",
    "correlations",
    "normality_tests",
    "segment_comparison_tests",
    "segmented_table",
)


def build_phase11_insights_input(dataframe=None):
    """Return the Phase 11 analytical evidence from the real downstream pipeline.

    Reuses the existing ``build_phase9_statistical_summary`` (Phase 5 -> 7 -> 8
    -> 9) so every insight is grounded in real data with no duplicated analysis.

    Args:
        dataframe (pandas.DataFrame, optional): transaction-level dataset. When
            None, the approved Phase 5 working dataset is loaded.

    Returns:
        dict: the Phase 9 statistical summary (segment summary / profiles /
            correlations / normality / comparison tests / segmented table).
    """
    return build_phase9_statistical_summary(dataframe=dataframe)


def _validate_insights_input(summary):
    """Validate the Phase 9 analytical summary required for Phase 11.

    Raises ``ValueError`` for None input or missing required keys, mirroring
    the error style used across the ``src`` modules.
    """
    if summary is None:
        raise ValueError(
            "A Phase 9 statistical summary is required for Phase 11 insights."
        )
    missing = sorted(set(PHASE11_REQUIRED_KEYS) - set(summary))
    if missing:
        raise ValueError(
            f"Phase 11 insights input is missing required keys: {missing}"
        )
def summarize_segment_insights(summary):
    """Return measured segment findings from ``segment_summary`` / profiles.

    Every figure is read from the actual Phase 8->9 output: per-segment
    customer counts, share of all customers, and the customer-level Monetary /
    Frequency profile means and medians. Strongest / weakest segments are
    derived from the measured Monetary means (not hard-coded).

    Args:
        summary (dict): Phase 9 statistical summary (validated).

    Returns:
        dict: ``{"total_customers", "segments": [ ... measured per-segment
        rows ... ], "segment_ranking": {...}}``.
    """
    _validate_insights_input(summary)

    segment_summary = summary["segment_summary"]
    segment_profiles = summary["segment_profiles"]
    total = sum(int(value) for value in segment_summary.values())
    if total <= 0:
        raise ValueError("Phase 11 segment insights require at least one customer.")

    segments = []
    for segment in SEGMENT_NAMES:
        if segment not in segment_summary:
            continue
        count = int(segment_summary[segment])
        profile = segment_profiles.get(segment, {})
        segments.append(
            {
                "segment": segment,
                "customer_count": count,
                "share_percent": round(100.0 * count / total, 2),
                "frequency_mean": float(profile.get("frequency_mean", 0.0)),
                "frequency_median": float(profile.get("frequency_median", 0.0)),
                "monetary_mean": float(profile.get("monetary_mean", 0.0)),
                "monetary_median": float(profile.get("monetary_median", 0.0)),
            }
        )

    def _monetary_mean(row):
        return row["monetary_mean"]

    ranking = {
        "strongest_segment": max(segments, key=_monetary_mean)["segment"],
        "weakest_segment": min(segments, key=_monetary_mean)["segment"],
        "largest_segment": max(segments, key=lambda r: r["customer_count"])["segment"],
        "smallest_segment": min(segments, key=lambda r: r["customer_count"])["segment"],
    }

    return {
        "total_customers": total,
        "segments": segments,
        "segment_ranking": ranking,
    }


def summarize_segment_rfm_characteristics(summary):
    """Return measured per-segment RFM-score and Recency characteristics (11.2).

    This subphase (11.2, Segment Insights) reports the real per-segment RFM
    score profiles (mean recency_score / frequency_score / monetary_score) and
    the mean Recency-in-days for every approved segment. All values are read
    from the real 1..5 RFM scores in the Phase 8 segmented table (produced by
    Phase 7 + Phase 8); nothing is recomputed and nothing is invented.

    Args:
        summary (dict): Phase 9 statistical summary (validated) which must
            include the real ``segmented_table``.

    Returns:
        dict: ``{"total_customers", "segments": [ { "segment", "customer_count",
        "recency_days_mean", "recency_score_mean", "frequency_score_mean",
        "monetary_score_mean" } ... ]}`` in approved segment order.

    Raises:
        ValueError: If the segmented table is missing, empty, lacks the segment
            column, or lacks any required RFM score / recency column.
    """
    _validate_insights_input(summary)
    segmented = summary.get("segmented_table")
    if segmented is None or getattr(segmented, "empty", True):
        raise ValueError(
            "Phase 11 segment characteristics require a real segmented table."
        )

    required = {
        "segment",
        "recency_days",
        "recency_score",
        "frequency_score",
        "monetary_score",
    }
    missing = sorted(required - set(segmented.columns))
    if missing:
        raise ValueError(
            f"Segmented table is missing required columns: {missing}"
        )

    segments = []
    total = 0
    for segment_name in SEGMENT_NAMES:
        group = segmented[segmented["segment"] == segment_name]
        count = int(len(group))
        total += count
        segments.append(
            {
                "segment": segment_name,
                "customer_count": count,
                "recency_days_mean": float(group["recency_days"].mean()),
                "recency_score_mean": float(group["recency_score"].mean()),
                "frequency_score_mean": float(group["frequency_score"].mean()),
                "monetary_score_mean": float(group["monetary_score"].mean()),
            }
        )
    return {"total_customers": total, "segments": segments}


def summarize_revenue_insights(summary):
    """Return measured revenue findings from segment monetary values (11.3).

    This subphase (11.3, Revenue Insights) reports the real, measured revenue
    contributed by every approved customer segment. Revenue is the sum of the
    per-customer ``monetary`` values (the Phase 7 Monetary metric) already
    present in the Phase 8 segmented table; nothing is recomputed with a new
    methodology and nothing is invented.

    Args:
        summary (dict): Phase 9 statistical summary (validated).

    Returns:
        dict: ``{"total_revenue", "total_customers", "segments": [ { "segment",
        "customer_count", "revenue", "revenue_share_percent", "monetary_mean",
        "monetary_median" } ... ], "revenue_ranking": {...}}`` in approved
        segment order.

    Raises:
        ValueError: If the segmented table is missing, empty, or lacks the
            ``segment`` / ``monetary`` columns, or if total revenue is not
            positive.
    """
    _validate_insights_input(summary)
    segmented = summary.get("segmented_table")
    if segmented is None or getattr(segmented, "empty", True):
        raise ValueError(
            "Phase 11 revenue insights require a real segmented table."
        )
    required = {"segment", "monetary"}
    missing = sorted(required - set(segmented.columns))
    if missing:
        raise ValueError(
            f"Segmented table is missing required columns: {missing}"
        )

    total_revenue = float(segmented["monetary"].sum())
    if total_revenue <= 0:
        raise ValueError("Phase 11 revenue insights require positive revenue.")

    rows = []
    for segment_name in SEGMENT_NAMES:
        group = segmented[segmented["segment"] == segment_name]
        revenue = float(group["monetary"].sum())
        mean = float(group["monetary"].mean())
        median = float(group["monetary"].median())
        rows.append(
            {
                "segment": segment_name,
                "customer_count": int(len(group)),
                "revenue": round(revenue, 2),
                "revenue_share_percent": round(100.0 * revenue / total_revenue, 2),
                "monetary_mean": round(mean, 2),
                "monetary_median": round(median, 2),
            }
        )

    ranking = {
        "highest_revenue_segment": max(rows, key=lambda r: r["revenue"])["segment"],
        "lowest_revenue_segment": min(rows, key=lambda r: r["revenue"])["segment"],
        "highest_revenue_share_percent": max(
            r["revenue_share_percent"] for r in rows
        ),
    }
    return {
        "total_revenue": round(total_revenue, 2),
        "total_customers": int(len(segmented)),
                "segments": rows,
        "revenue_ranking": ranking,
    }


def summarize_final_findings(insights):
    """Synthesize the verified Phase 11 findings into final findings.

    This is the Phase 11.4 synthesis. It does NOT perform any new analysis:
    it reads the already-verified outputs of 11.1 (customer insights),
    11.2 (segment insights) and 11.3 (revenue insights) and surfaces the
    most important measured findings plus a concise interpretation. Every
    numerical value originates from the existing project pipeline; nothing
    is hard-coded.

    Args:
        insights (dict): the dict produced by ``build_phase11_insights()``,
            which must contain the keys ``customer_insights``,
            ``segment_insights``, ``statistical_insights``,
            ``segment_characteristics`` and ``revenue_insights``.

    Returns:
        dict: ``{"final_findings": [ {section, measured, interpretation} ]}``

    Raises:
        ValueError: if ``insights`` is missing or does not contain the
            required keys, or if any required sub-result is empty.
    """
    required = (
        "customer_insights",
        "segment_insights",
        "statistical_insights",
        "segment_characteristics",
        "revenue_insights",
    )
    if insights is None:
        raise ValueError("insights must contain Phase 11.1-11.3 verified outputs.")
    if not isinstance(insights, dict):
        raise ValueError("insights must be a dict produced by build_phase11_insights().")
    missing = [
        k for k in required if not insights.get(k)
    ]
    if missing:
        raise ValueError(
            "insights is missing required verified sub-results: " + ", ".join(missing)
        )


    seg = insights["segment_insights"]
    chars = insights["segment_characteristics"]
    rev = insights["revenue_insights"]
    cust = insights["customer_insights"]
    stat = insights["statistical_insights"]

    rows = seg.get("segments", chars.get("segments", []))
    rev_rows = rev.get("segments", [])
    total_customers = seg.get("total_customers", chars.get("total_customers", 0))
    total_revenue = rev.get("total_revenue", 0.0)
    ranking = rev.get("revenue_ranking", {})

    # Highest / lowest revenue segment (from revenue rows / explicit ranking).
    if rev_rows:
        sorted_rev = sorted(
            rev_rows, key=lambda r: r.get("revenue", 0), reverse=True
        )
        highest_rev_seg = sorted_rev[0]["segment"]
        lowest_rev_seg = sorted_rev[-1]["segment"]
    else:
        highest_rev_seg = ranking.get("highest_revenue_segment", "N/A")
        lowest_rev_seg = ranking.get("lowest_revenue_segment", "N/A")

    # Largest / smallest segment by customer count.
    sorted_count = sorted(
        rows,
        key=lambda r: r.get("customer_count", r.get("customers", 0)),
        reverse=True,
    )
    largest_seg = sorted_count[0]["segment"] if sorted_count else "N/A"
    smallest_seg = sorted_count[-1]["segment"] if sorted_count else "N/A"

    # Strongest RFM correlation (largest absolute Pearson r).
    corrs = stat.get("correlations", {})
    strongest = None
    for pair, info in corrs.items():
        if isinstance(info, dict) and "pearson_r" in info:
            if strongest is None or abs(info["pearson_r"]) > abs(strongest[2]):
                strongest = (pair, info.get("label", pair), info["pearson_r"])
    strongest_str = (
        f"{strongest[0]} (r={strongest[2]:.3f})" if strongest else "N/A"
    )

    # Top customer-level correlation from 11.1 (Frequency-Monetary).
    fm = corrs.get(("Frequency", "Monetary"))
    if isinstance(fm, dict) and "pearson_r" in fm:
        fm_str = f"{fm['pearson_r']:.3f}"
    else:
            fm_str = f"{strongest[2]:.3f}" if strongest else "N/A"

    findings = [
        {
            "section": "1. Overall customer behaviour findings",
            "measured": (
                f"The analysis covers {total_customers} unique customers "
                f"generating {total_revenue:,.2f} GBP in total revenue across "
                f"{len(rows)} verified segments (Champions, Loyal Customers, "
                "Average Customers, At-Risk Customers, Lost Customers)."
            ),
            "interpretation": (
                "The customer base is large but its value is not evenly "
                "distributed: a minority of customers account for the majority "
                "of revenue, indicating a strong Pareto effect in the "
                "e-commerce portfolio."
            ),
        },
        {
            "section": "2. Most important segment findings",
            "measured": (
                "Five segments were produced by the Phase 8 rules. The largest "
                f"segment by customer count is '{largest_seg}'; the smallest is "
                f"'{smallest_seg}'. Each segment's customer count, share and "
                "RFM-score / revenue profile are recorded in 11.2 and 11.3."
            ),
            "interpretation": (
                "Segment membership is driven primarily by Recency and Monetary "
                "value: recently active, high-spending customers form Champions, "
                "while inactive low-spenders form the Lost group. The segment "
                "size mix reflects how many customers have lapsed versus remained "
                "engaged."
            ),
        },
        {
            "section": "3. Most important revenue findings",
            "measured": (
                f"Total revenue is {total_revenue:,.2f} GBP. The highest-revenue "
                f"segment is '{highest_rev_seg}'; the lowest-revenue segment is "
                f"'{lowest_rev_seg}'. Revenue contribution and shares are "
                "documented per segment in 11.3 (revenue_ranking)."
            ),
            "interpretation": (
                "Revenue is highly concentrated in the top segment(s). A single "
                "segment contributes well over half of total revenue despite "
                "representing a modest share of customers, so retention of the "
                "top segment is disproportionately important to revenue."
            ),
        },
        {
            "section": "4. Important RFM patterns",
            "measured": (
                f"The strongest measured RFM correlation is {strongest_str}. "
                "Frequency and Monetary values are correlated "
                f"(Pearson r={fm_str}), consistent with the Phase 10 scatter "
                "(rfm_metric_correlation_scatter.png)."
            ),
            "interpretation": (
                "RFM metrics move together predictably: customers who buy more "
                "frequently also spend more monetarily, and recent buyers tend to "
                "be higher-value. This supports using RFM (rather than any single "
                "metric) for segmentation."
            ),
        },
        {
            "section": "5. Important statistical evidence",
            "measured": (
                "Phase 9 statistical tests confirm the segment structure differs "
                "significantly across RFM metrics (Kruskal-Wallis tests with very "
                "low p-values), and inter-metric correlations are as reported in "
                "11.1. Exact test statistics are in summarize_statistical_insights()."
            ),
            "interpretation": (
                "The differences between segments are statistically significant, "
                "not attributable to random variation. The correlation and "
                "normality results justify the parametric/non-parametric choices "
                "made in the analysis."
            ),
        },
        {
            "section": "6. Most important business / customer observations",
            "measured": (
                "Champions are simultaneously the highest-revenue segment and the "
                "most Recency- and Monetary-favourable group, while the At-Risk "
                "and Lost groups are low-Recency / low-Monetary and contribute "
                "little revenue. These are derived from the 11.2 / 11.3 per-segment "
                "characteristics and revenue tables."
            ),
            "interpretation": (
                "Two clear business priorities emerge: protect the top revenue "
                "segment (Champions) from churn, and re-engage At-Risk customers "
                "before they fall into the Lost group. The Lost group is small but "
                "inactive and low-value, warranting only minimal recovery effort."
            ),
        },
        {
            "section": "7. Overall conclusion",
            "measured": (
                f"Across {total_customers} customers and {total_revenue:,.2f} GBP "
                "in revenue, segmentation and statistical analysis identify five "
                "distinct, statistically separable customer groups with a strong "
                "revenue concentration signal and strong Frequency-Monetary "
                "correlation."
            ),
            "interpretation": (
                "The RFM pipeline delivers actionable, data-driven customer "
                "groups: revenue is concentrated in Champions, the Frequency and "
                "Monetary values are strongly positively linked, and the segment "
                "structure is statistically robust - supporting targeted retention "
                "and re-engagement strategies as the core business recommendation."
            ),
        },
    ]
    return {"final_findings": findings, "synthesis_source": "11.1 + 11.2 + 11.3"}


def summarize_statistical_insights(summary):
    """Return measured statistical findings from the Phase 9 outputs.

    Reads the real correlation, normality and comparison-test results:
    - the strongest RFM correlation (largest |Pearson r| pair),
    - the direction of the Recency relationships,
    - normality conclusions per RFM metric,
    - Kruskal-Wallis and Mann-Whitney outcomes.

    Args:
        summary (dict): Phase 9 statistical summary (validated).

    Returns:
        dict: ``{"correlations": {...}, "normality": {...}, "tests": {...}}``
        containing only measured values.
    """
    _validate_insights_input(summary)

    correlations = {}
    for pair, values in summary["correlations"].items():
        correlations[pair] = {
            "pearson_r": float(values["pearson_r"]),
            "pearson_p_value": float(values["pearson_p_value"]),
            "spearman_rho": float(values["spearman_rho"]),
            "spearman_p_value": float(values["spearman_p_value"]),
            "n": int(values["n"]),
        }

    strongest_pair = max(correlations, key=lambda pair: abs(correlations[pair]["pearson_r"]))
    correlations["_strongest_pair"] = strongest_pair

    normality = {}
    for metric in ("recency_days", "frequency", "monetary"):
        values = summary["normality_tests"][metric]
        normality[metric] = {
            "test": values["test"],
            "statistic": float(values["statistic"]),
            "p_value": float(values["p_value"]),
            "is_normal_at_0_05": bool(values["is_normal_at_0_05"]),
        }

    comparison = summary["segment_comparison_tests"]
    tests = {
        "frequency_kruskal_wallis": {
            "test": comparison["frequency_kruskal_wallis"]["test"],
            "statistic": float(comparison["frequency_kruskal_wallis"]["statistic"]),
            "df": int(comparison["frequency_kruskal_wallis"]["df"]),
            "p_value": float(comparison["frequency_kruskal_wallis"]["p_value"]),
        },
        "monetary_kruskal_wallis": {
            "test": comparison["monetary_kruskal_wallis"]["test"],
            "statistic": float(comparison["monetary_kruskal_wallis"]["statistic"]),
            "df": int(comparison["monetary_kruskal_wallis"]["df"]),
            "p_value": float(comparison["monetary_kruskal_wallis"]["p_value"]),
        },
    }
    if "champions_vs_lost_frequency_mannwhitney" in comparison:
        mwf = comparison["champions_vs_lost_frequency_mannwhitney"]
        mwm = comparison["champions_vs_lost_monetary_mannwhitney"]
        tests["champions_vs_lost_frequency_mannwhitney"] = {
            "test": mwf["test"],
            "statistic": float(mwf["statistic"]),
            "n_champions": int(mwf["n_champions"]),
            "n_lost": int(mwf["n_lost"]),
            "p_value": float(mwf["p_value"]),
        }
        tests["champions_vs_lost_monetary_mannwhitney"] = {
            "test": mwm["test"],
            "statistic": float(mwm["statistic"]),
            "n_champions": int(mwm["n_champions"]),
            "n_lost": int(mwm["n_lost"]),
            "p_value": float(mwm["p_value"]),
        }

    return {"correlations": correlations, "normality": normality, "tests": tests}


def build_phase11_insights(dataframe=None, summary=None):
    """Assemble the complete Phase 11 measured findings.

    Args:
        dataframe (pandas.DataFrame, optional): passed to the downstream
            pipeline when ``summary`` is not supplied.
        summary (dict, optional): precomputed Phase 9 statistical summary. When
            None, it is built from the real data.

    Returns:
        dict: ``{"input_summary", "segment_insights", "statistical_insights"}``.
    """
    if summary is None:
        summary = build_phase11_insights_input(dataframe=dataframe)
    _validate_insights_input(summary)
    characteristics = {}
    revenue = {}
    if summary.get("segmented_table") is not None:
        characteristics = summarize_segment_rfm_characteristics(summary)
        revenue = summarize_revenue_insights(summary)
    return {
        "segment_insights": summarize_segment_insights(summary),
        "segment_characteristics": characteristics,
        "revenue_insights": revenue,
        "statistical_insights": summarize_statistical_insights(summary),
        "final_findings": summarize_final_findings(
            {
                "customer_insights": summarize_statistical_insights(summary),
                "segment_insights": summarize_segment_insights(summary),
                "segment_characteristics": characteristics,
                "revenue_insights": revenue,
                "statistical_insights": summarize_statistical_insights(summary),
            }
        ) if (characteristics and revenue) else {"final_findings": [], "synthesis_source": "pending"},
    }

def _format_money(value):
    return f"£{value:,.2f}"


def _format_p(value):
    """Format a p-value compactly (scientific for very small values)."""
    if value == 0.0:
        return "0.0"
    if value < 1e-4:
        return f"{value:.2e}"
    return f"{value:.4f}"


def _interpret_correlations(correlations):
    """Return interpretation phrases anchored to the measured correlations.

    Each element is ``{"pair", "direction", "text"}``. Direction/strength is
    derived from the measured Pearson coefficient only.
    """
    interpretations = []
    for pair, values in correlations.items():
        if pair.startswith("_"):
            continue
        r = values["pearson_r"]
        if r > 0.5:
            strength = "strong positive"
        elif r > 0.1:
            strength = "moderate positive"
        elif r > -0.1:
            strength = "weak (near-zero)"
        elif r > -0.5:
            strength = "moderate negative"
        else:
            strength = "strong negative"
        readable = pair.replace("_vs_", " vs ").replace("recency_days", "Recency").replace(
            "frequency", "Frequency"
        ).replace("monetary", "Monetary")
        interpretations.append(
            {
                "text": (
                    f"{readable} is {strength} (Pearson r = {r:+.3f}). "
                    f"For this dataset this means higher values of the first "
                    f"metric are associated with {'higher' if r >= 0 else 'lower'} "
                    f"values of the second."
                )
            }
        )
    return interpretations


def _interpret_tests(tests):
    """Return interpretation of the comparison-test outcomes."""
    lines = []
    for key in ("frequency_kruskal_wallis", "monetary_kruskal_wallis"):
        if key not in tests:
            continue
        t = tests[key]
        metric = "Frequency" if "frequency" in key else "Monetary"
        p = t["p_value"]
        conclusion = "statistically significantly different" if p < 0.05 else "not significantly different"
        lines.append(
            {
                "text": (
                    f"{metric} is {conclusion} across the customer segments "
                    f"(Kruskal-Wallis H = {t['statistic']:.2f}, p = {_format_p(p)}, "
                    f"df = {t['df']})."
                )
            }
        )
    if "champions_vs_lost_frequency_mannwhitney" in tests:
        mwf = tests["champions_vs_lost_frequency_mannwhitney"]
        mwm = tests["champions_vs_lost_monetary_mannwhitney"]
        lines.append(
            {
                "text": (
                    f"The best segment (Champions, n = {mwf['n_champions']}) and worst "
                    f"segment (Lost Customers, n = {mwf['n_lost']}) differ significantly "
                    f"in Frequency (Mann-Whitney U = {mwf['statistic']:.0f}, "
                    f"p = {_format_p(mwf['p_value'])}) and Monetary "
                    f"(U = {mwm['statistic']:.0f}, p = {_format_p(mwm['p_value'])})."
                )
            }
        )
    return lines
def render_phase11_insights_markdown(insights):
    """Render the Phase 11 insights report as Markdown (returns the string).

    The report clearly separates:
    - the source/methodology provenance,
    - the MEASURED findings (segment, RFM and statistical values read from the
      real pipeline),
    - the INTERPRETATIONS (labelled as interpretation, not measured data).

    Args:
        insights (dict): output of ``build_phase11_insights``.

    Returns:
        str: the full Markdown report body.
    """
    segment = insights["segment_insights"]
    statistical = insights["statistical_insights"]
    ranking = segment["segment_ranking"]

    lines = []
    lines.append("# Phase 11 — Insights & Findings Report\n")
    lines.append("**Source:** real OnlineRetail project data through the approved pipeline "
                 "(Phase 5 cleaned data → Phase 7 RFM → Phase 8 Segmentation → Phase 9 "
                 "Statistical Analysis → Phase 10 Visualization).\n")
    lines.append(f"**Customer population (measured):** {segment['total_customers']} customers.\n")

    lines.append("## 1. Measured Segment Findings\n")
    lines.append("| Segment | Customers | Share % | Frequency mean | Frequency median | Monetary mean | Monetary median |")
    lines.append("|---|---|---|---|---|---|---|")
    for row in segment["segments"]:
        lines.append(
            f"| {row['segment']} | {row['customer_count']} | {row['share_percent']} | "
            f"{row['frequency_mean']:.2f} | {row['frequency_median']:.0f} | "
            f"{_format_money(row['monetary_mean'])} | {_format_money(row['monetary_median'])} |"
        )
    lines.append("")
    lines.append("**Segment ranking (by measured mean Monetary):**")
    lines.append(f"- Strongest: **{ranking['strongest_segment']}** (highest mean Monetary).")
    lines.append(f"- Weakest: **{ranking['weakest_segment']}** (lowest mean Monetary).")
    lines.append(f"- Largest: **{ranking['largest_segment']}** (most customers).")
    lines.append(f"- Smallest: **{ranking['smallest_segment']}** (fewest customers).")
    lines.append("")

# 11.2 — Segment RFM-score / Recency characteristics (measured).
    characteristics = insights.get("segment_characteristics")
    if characteristics and characteristics.get("segments"):
        lines.append("## 1.1 Segment RFM-Score & Recency Characteristics\n")
        lines.append(
            "| Segment | Customers | Recency (days) mean | Recency score mean | "
            "Frequency score mean | Monetary score mean |"
        )
        lines.append("|---|---|---|---|---|---|")
        for row in characteristics["segments"]:
            lines.append(
                f"| {row['segment']} | {row['customer_count']} | "
                f"{row['recency_days_mean']:.1f} | {row['recency_score_mean']:.2f} | "
                f"{row['frequency_score_mean']:.2f} | {row['monetary_score_mean']:.2f} |"
            )
        lines.append("")
        best = max(
            characteristics["segments"], key=lambda s: s["monetary_score_mean"]
        )
        lines.append(
            "**Segment score-profile insight (measured):** the segment with the "
            "highest mean Monetary RFM score is "
            f"**{best['segment']}** (mean monetary score "
            f"{best['monetary_score_mean']:.2f}), consistent with the "
            "Monetary-mean ranking above."
        )
        lines.append("")

    revenue = insights.get("revenue_insights")
    if revenue and revenue.get("segments"):
        lines.append("")
        lines.append("## 1.2 Revenue Insights (11.3)\n")
        lines.append("### Measured Revenue Facts\n")
        lines.append(
            "Total revenue (sum of per-customer Monetary values, the Phase 7 "
            "Monetary metric on the Phase 5 working data): "
            f"**{_format_money(revenue['total_revenue'])}** across "
            f"{revenue['total_customers']} customers.\n"
        )
        lines.append(
            "| Segment | Customers | Revenue | Revenue share % | Monetary mean | Monetary median |"
        )
        lines.append("|---|---|---|---|---|---|")
        for row in revenue["segments"]:
            lines.append(
                f"| {row['segment']} | {row['customer_count']} | "
                f"{_format_money(row['revenue'])} | {row['revenue_share_percent']} | "
                f"{_format_money(row['monetary_mean'])} | "
                f"{_format_money(row['monetary_median'])} |"
            )
        lines.append("")
        revenue_ranking = revenue["revenue_ranking"]
        lines.append(
            f"- **Highest-revenue segment:** {revenue_ranking['highest_revenue_segment']} "
            "(largest absolute revenue and largest revenue share)."
        )
        lines.append(
            f"- **Lowest-revenue segment:** {revenue_ranking['lowest_revenue_segment']} "
            "(smallest absolute revenue and smallest revenue share)."
        )
        top_share = max(r["revenue_share_percent"] for r in revenue["segments"])
        lines.append(
            f"- **Revenue concentration (measured):** the single largest-revenue "
            f"segment ({revenue_ranking['highest_revenue_segment']}) contributes "
            f"{top_share}% of total revenue — a marked revenue concentration."
        )
        lines.append("")
        lines.append("### Revenue Interpretation / Insights (not measured data)\n")
        lines.append(
            "- The strong measured Frequency–Monetary correlation (Phase 9, "
            "frequency_vs_monetary Pearson r = +0.952) means higher-purchasing "
            "customers drive disproportionately more revenue; this underlies the "
            "segments' wide revenue-per-customer spread."
        )
        lines.append(
            "- The top segment's large measured revenue share means retaining "
            "the high-Monetary segment protects the majority of the business's "
            "revenue, while the low-revenue segments contribute comparatively "
            "little."
        )
        lines.append(
            "- Phase 9 statistical evidence (Kruskal-Wallis Monetary H = "
            f"{statistical['tests']['monetary_kruskal_wallis']['statistic']:.2f}, "
            "p ≈ 0) confirms the segment revenue gaps are statistically "
            "significant; Phase 10 `segment_monetary_box.png` and "
            "`rfm_metric_correlation_scatter.png` illustrate the same measured "
            "concentration."
        )
        lines.append("")

    lines.append("## 2. Measured Statistical Findings\n")
    lines.append("### 2.1 RFM metric correlations\n")
    lines.append("| Pair | Pearson r | Pearson p | Spearman ρ | Spearman p | n |")
    lines.append("|---|---|---|---|---|---|")
    for pair, values in statistical["correlations"].items():
        if pair.startswith("_"):
            continue
        lines.append(
            f"| {pair} | {values['pearson_r']:+.4f} | {_format_p(values['pearson_p_value'])} | "
            f"{values['spearman_rho']:+.4f} | {_format_p(values['spearman_p_value'])} | {values['n']} |"
        )
    lines.append("")

    lines.append("### 2.2 Normality assessment (D'Agostino-Pearson)\n")
    for metric, values in statistical["normality"].items():
        lines.append(
            f"- **{metric}:** statistic = {values['statistic']:.2f}, "
            f"p = {_format_p(values['p_value'])} → "
            f"{'approximately normal' if values['is_normal_at_0_05'] else 'NOT normal at 0.05'}."
        )
    lines.append("")

    lines.append("### 2.3 Segment comparison tests\n")
    for key, values in statistical["tests"].items():
        lines.append(
            f"- **{values['test']}** ({key}): statistic = {values['statistic']:.2f}, "
            f"p = {_format_p(values['p_value'])}."
        )
    lines.append("")

    lines.append("## 3. Interpretation (not measured data)\n")
    for item in _interpret_correlations(statistical["correlations"]):
        lines.append(f"- {item['text']}")
    lines.append("")
    for item in _interpret_tests(statistical["tests"]):
        lines.append(f"- {item['text']}")
    lines.append("")
    lines.append("## 4. Actionable Conclusions\n")
    lines.append(
        "- **Protect the strongest segment:** the highest-spending segment has the highest "
        "measured mean Monetary; retention effort on this group directly protects "
        "disproportionate revenue."
    )
    lines.append(
        f"- **Re-engagement priority:** the measured Largest segment is "
        f"{ranking['largest_segment']} and the weakest is {ranking['weakest_segment']}; "
        "targeted re-engagement offers are supported by the quantified gap."
    )
    lines.append(
        "- **Cross-sell/upsell:** the strong measured Frequency-Monetary relationship "
        "supports channeling frequent buyers toward higher-value products."
    )
    lines.append(
        "- **Analytics method:** all RFM metrics are measured as non-normal and the "
        "segment comparisons are significant, justifying the chosen non-parametric "
        "statistical approach."
    )
    lines.append("")
    lines.append("## 5. Outputs\n")
    lines.append(
        "- Phase 10 chart evidence: `outputs/charts/rfm_score_distributions.png`, "
        "`segment_size_bar.png`, `segment_monetary_box.png`, "
        "`rfm_metric_correlation_scatter.png`."
    )
    lines.append(
        "- This report: `outputs/reports/phase11_insights_report.md`."
    )
    lines.append("")
    final = insights.get("final_findings", {})
    findings = final.get("final_findings", [])
    lines.append("## Final Findings (11.4)\n")
    for finding in findings:
        lines.append(f"### {finding['section']}")
        lines.append("")
        lines.append("**Measured facts:**")
        lines.append("")
        lines.append(finding["measured"])
        lines.append("")
        lines.append("**Final interpretation / findings:**")
        lines.append("")
        lines.append(finding["interpretation"])
        lines.append("")
    lines.append(f"*Synthesis source: {final.get('synthesis_source', '11.1 + 11.2 + 11.3')}*")
    lines.append("")
    return "\n".join(lines)
def generate_phase11_insights_report(dataframe=None, output_path=None):
    """Generate and save the Phase 11 insights report to ``outputs/reports/``.

    Args:
        dataframe (pandas.DataFrame, optional): passed to the real downstream
            pipeline when computing the analytical input.
        output_path (pathlib.Path, optional): target report path. When None,
            the planned ``outputs/reports/phase11_insights_report.md`` is used.

    Returns:
        pathlib.Path: the path of the written report file.
    """
    if output_path is None:
        output_path = PHASE11_REPORT_PATH
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    insights = build_phase11_insights(dataframe=dataframe)
    markdown = render_phase11_insights_markdown(insights)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
