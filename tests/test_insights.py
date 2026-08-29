"""
tests/test_insights.py - Phase 11: Insights & Findings tests.

Internal unit-style tests (Python built-in unittest only, consistent with the
project dependency policy - pytest is NOT an approved dependency).

Coverage:
    - Real-data insight generation (Phase 5 -> 7 -> 8 -> 9 -> 11)
    - Required input validation / invalid-empty handling
    - Expected insight/report structure
    - Measured segment findings (counts, shares, strongest/weakest)
    - Measured statistical findings (correlations, normality, tests)
    - Deterministic rendering for identical input
    - No fabricated values (figures recomputed from the summary, not hard-coded)
    - Compatibility with the Phase 8-10 outputs (report generated & written)
"""

import pathlib
import tempfile
import unittest

from src.insights import (
    PHASE11_REPORT_FILENAME,
    build_phase11_insights,
    generate_phase11_insights_report,
    render_phase11_insights_markdown,
    summarize_segment_insights,
    summarize_segment_rfm_characteristics,
    summarize_statistical_insights,
    summarize_revenue_insights,
    summarize_final_findings,
)


def _fixture_summary():
    """A minimal, valid Phase 9-shaped summary for deterministic tests."""
    return {
        "segment_summary": {
            "Champions": 100,
            "Loyal Customers": 60,
            "Average Customers": 50,
            "At-Risk Customers": 30,
            "Lost Customers": 10,
        },
        "segment_profiles": {
            "Champions": {
                "customer_count": 100,
                "frequency_mean": 12.0,
                "frequency_median": 9.0,
                "frequency_std": 3.0,
                "monetary_mean": 5000.0,
                "monetary_median": 4000.0,
                "monetary_std": 1000.0,
            },
            "Loyal Customers": {
                "customer_count": 60,
                "frequency_mean": 5.0,
                "frequency_median": 5.0,
                "frequency_std": 1.0,
                "monetary_mean": 1500.0,
                "monetary_median": 1200.0,
                "monetary_std": 200.0,
            },
            "Average Customers": {
                "customer_count": 50,
                "frequency_mean": 2.0,
                "frequency_median": 2.0,
                "frequency_std": 0.5,
                "monetary_mean": 800.0,
                "monetary_median": 700.0,
                "monetary_std": 100.0,
            },
            "At-Risk Customers": {
                "customer_count": 30,
                "frequency_mean": 1.0,
                "frequency_median": 1.0,
                "frequency_std": 0.0,
                "monetary_mean": 300.0,
                "monetary_median": 250.0,
                "monetary_std": 50.0,
            },
            "Lost Customers": {
                "customer_count": 10,
                "frequency_mean": 1.0,
                "frequency_median": 1.0,
                "frequency_std": 0.0,
                "monetary_mean": 100.0,
                "monetary_median": 90.0,
                "monetary_std": 20.0,
            },
        },
        "correlations": {
            "recency_days_vs_frequency": {
                "n": 10,
                "pearson_r": -0.4,
                "pearson_p_value": 0.2,
                "spearman_rho": -0.3,
                "spearman_p_value": 0.35,
            },
            "recency_days_vs_monetary": {
                "n": 10,
                "pearson_r": -0.2,
                "pearson_p_value": 0.5,
                "spearman_rho": -0.1,
                "spearman_p_value": 0.7,
            },
            "frequency_vs_monetary": {
                "n": 10,
                "pearson_r": 0.9,
                "pearson_p_value": 0.0001,
                "spearman_rho": 0.8,
                "spearman_p_value": 0.01,
            },
        },
        "normality_tests": {
            "recency_days": {
                "n": 10,
                "test": "D'Agostino-Pearson omnibus",
                "statistic": 1.0,
                "p_value": 0.5,
                "is_normal_at_0_05": True,
            },
            "frequency": {
                "n": 10,
                "test": "D'Agostino-Pearson omnibus",
                "statistic": 20.0,
                "p_value": 0.01,
                "is_normal_at_0_05": False,
            },
            "monetary": {
                "n": 10,
                "test": "D'Agostino-Pearson omnibus",
                "statistic": 25.0,
                "p_value": 0.0,
                "is_normal_at_0_05": False,
            },
        },
        "segment_comparison_tests": {
            "frequency_kruskal_wallis": {
                "test": "Kruskal-Wallis H",
                "groups": 5,
                "df": 4,
                "statistic": 40.0,
                "p_value": 0.001,
            },
            "monetary_kruskal_wallis": {
                "test": "Kruskal-Wallis H",
                "groups": 5,
                "df": 4,
                "statistic": 55.0,
                "p_value": 0.0001,
            },
            "champions_vs_lost_frequency_mannwhitney": {
                "test": "Mann-Whitney U",
                "n_champions": 100,
                "n_lost": 10,
                "statistic": 1000.0,
                "p_value": 0.0001,
            },
            "champions_vs_lost_monetary_mannwhitney": {
                "test": "Mann-Whitney U",
                "n_champions": 100,
                "n_lost": 10,
                "statistic": 1000.0,
                "p_value": 0.0001,
            },
        },
        "segmented_table": None,
    }
class TestInsightValidation(unittest.TestCase):
    """Invalid Phase 11 inputs must raise clear ValueErrors."""

    def test_none_input_raises_for_segment_insights(self):
        with self.assertRaises(ValueError):
            summarize_segment_insights(None)

    def test_none_input_raises_for_statistical_insights(self):
        with self.assertRaises(ValueError):
            summarize_statistical_insights(None)

    def test_missing_keys_raise(self):
        with self.assertRaises(ValueError):
            summarize_segment_insights({})

    def test_build_insights_missing_keys_raise(self):
        with self.assertRaises(ValueError):
            build_phase11_insights(summary={})


class TestSegmentInsights(unittest.TestCase):
    def test_total_customers_recomputed_from_summary(self):
        seg = summarize_segment_insights(_fixture_summary())
        self.assertEqual(seg["total_customers"], 100 + 60 + 50 + 30 + 10)

    def test_strongest_and_weakest_by_measured_monetary(self):
        seg = summarize_segment_insights(_fixture_summary())
        self.assertEqual(seg["segment_ranking"]["strongest_segment"], "Champions")
        self.assertEqual(seg["segment_ranking"]["weakest_segment"], "Lost Customers")

    def test_largest_and_smallest_by_measured_count(self):
        seg = summarize_segment_insights(_fixture_summary())
        self.assertEqual(seg["segment_ranking"]["largest_segment"], "Champions")
        self.assertEqual(seg["segment_ranking"]["smallest_segment"], "Lost Customers")

    def test_shares_sum_to_100(self):
        seg = summarize_segment_insights(_fixture_summary())
        self.assertAlmostEqual(
            sum(r["share_percent"] for r in seg["segments"]), 100.0, places=1
        )


class TestStatisticalInsights(unittest.TestCase):
    def test_three_correlation_pairs_plus_strongest(self):
        st = summarize_statistical_insights(_fixture_summary())
        pairs = set(st["correlations"]) - {"_strongest_pair"}
        self.assertEqual(
            pairs,
            {
                "recency_days_vs_frequency",
                "recency_days_vs_monetary",
                "frequency_vs_monetary",
            },
        )
        self.assertEqual(st["correlations"]["_strongest_pair"], "frequency_vs_monetary")

    def test_normality_flags_recorded(self):
        st = summarize_statistical_insights(_fixture_summary())
        self.assertTrue(st["normality"]["recency_days"]["is_normal_at_0_05"])
        self.assertFalse(st["normality"]["frequency"]["is_normal_at_0_05"])
        self.assertFalse(st["normality"]["monetary"]["is_normal_at_0_05"])

    def test_comparison_tests_recorded(self):
        st = summarize_statistical_insights(_fixture_summary())
        self.assertIn("frequency_kruskal_wallis", st["tests"])
        self.assertIn("champions_vs_lost_frequency_mannwhitney", st["tests"])
class TestReportStructure(unittest.TestCase):
    def test_report_contains_expected_sections(self):
        insights = build_phase11_insights(summary=_fixture_summary())
        markdown = render_phase11_insights_markdown(insights)
        for section in (
            "# Phase 11",
            "Measured Segment Findings",
            "Measured Statistical Findings",
            "Interpretation",
            "Actionable Conclusions",
        ):
            self.assertIn(section, markdown)

    def test_report_is_deterministic(self):
        insights = build_phase11_insights(summary=_fixture_summary())
        first = render_phase11_insights_markdown(insights)
        second = render_phase11_insights_markdown(insights)
        self.assertEqual(first, second)

    def test_report_total_recomputed_not_fabricated(self):
        insights = build_phase11_insights(summary=_fixture_summary())
        markdown = render_phase11_insights_markdown(insights)
        self.assertIn("250 customers", markdown)  # 100+60+50+30+10 (recomputed)


class TestRealDataInsights(unittest.TestCase):
    """Real-data insight generation over the Phase 5 -> 7 -> 8 -> 9 -> 11 flow."""

    @classmethod
    def setUpClass(cls):
        cls.insights = build_phase11_insights()

    def test_real_data_customer_population(self):
        self.assertEqual(self.insights["segment_insights"]["total_customers"], 4338)

    def test_real_data_all_five_segments_present(self):
        segments = self.insights["segment_insights"]["segments"]
        self.assertEqual(len(segments), 5)
        for row in segments:
            self.assertGreater(row["customer_count"], 0)

    def test_real_data_segment_counts_sum_to_population(self):
        rows = self.insights["segment_insights"]["segments"]
        counts = {row["segment"]: row["customer_count"] for row in rows}
        self.assertEqual(sum(counts.values()), 4338)

    def test_real_data_strongest_weakest(self):
        ranking = self.insights["segment_insights"]["segment_ranking"]
        self.assertEqual(ranking["strongest_segment"], "Champions")
        self.assertEqual(ranking["weakest_segment"], "Lost Customers")

    def test_real_data_statistics_complete(self):
        corr = self.insights["statistical_insights"]["correlations"]
        pairs = set(corr) - {"_strongest_pair"}
        self.assertEqual(
            pairs,
            {
                "recency_days_vs_frequency",
                "recency_days_vs_monetary",
                "frequency_vs_monetary",
            },
        )
        self.assertIn("frequency_kruskal_wallis",
                      self.insights["statistical_insights"]["tests"])

    def test_real_data_characteristics_total(self):
        self.assertEqual(
            self.insights["segment_characteristics"]["total_customers"], 4338
        )

    def test_real_data_characteristics_five_segments(self):
        self.assertEqual(
            len(self.insights["segment_characteristics"]["segments"]), 5
        )

    def test_real_data_characteristics_counts_match_segment_insights(self):
        char_counts = {
            row["segment"]: row["customer_count"]
            for row in self.insights["segment_characteristics"]["segments"]
        }
        seg_counts = {
            row["segment"]: row["customer_count"]
            for row in self.insights["segment_insights"]["segments"]
        }
        self.assertEqual(char_counts, seg_counts)
        self.assertEqual(sum(char_counts.values()), 4338)

    def test_real_data_characteristics_counts_sum_to_population(self):
        rows = self.insights["segment_characteristics"]["segments"]
        self.assertEqual(
            sum(row["customer_count"] for row in rows),
            self.insights["segment_characteristics"]["total_customers"],
        )

    def test_real_data_characteristics_strongest_by_monetary_score(self):
        rows = self.insights["segment_characteristics"]["segments"]
        best = max(rows, key=lambda s: s["monetary_score_mean"])
        self.assertEqual(best["segment"], "Champions")


def _segmented_fixture():
    """A small, deterministic segmented table for segment-characteristic tests."""
    import pandas as pd

    rows = []
    # 2 Champions, 2 Loyal, 2 Average, 2 At-Risk, 2 Lost
    data = [
        # seg-year, CustomerID, recency_days, frequency, monetary, R,F,M scores
        ("Champions", 1, 5, 20, 3000, 5, 5, 5, "Champions"),
        ("Champions", 2, 10, 15, 2500, 5, 4, 4, "Champions"),
        ("Loyal Customers", 3, 30, 6, 1200, 4, 3, 4, "Loyal Customers"),
        ("Loyal Customers", 4, 40, 5, 1100, 4, 3, 3, "Loyal Customers"),
        ("Average Customers", 5, 60, 3, 800, 3, 2, 3, "Average Customers"),
        ("Average Customers", 6, 80, 2, 700, 3, 2, 2, "Average Customers"),
        ("At-Risk Customers", 7, 120, 1, 300, 2, 2, 2, "At-Risk Customers"),
        ("At-Risk Customers", 8, 150, 1, 250, 2, 1, 2, "At-Risk Customers"),
        ("Lost Customers", 9, 200, 1, 100, 1, 1, 1, "Lost Customers"),
        ("Lost Customers", 10, 250, 1, 90, 1, 1, 1, "Lost Customers"),
    ]
    df = pd.DataFrame(
        data,
        columns=[
            "segment",
            "CustomerID",
            "recency_days",
            "frequency",
            "monetary",
            "recency_score",
            "frequency_score",
            "monetary_score",
            "segment_check",
        ],
    )
    base = _fixture_summary()
    base["segmented_table"] = df
    return base


class TestSegmentRFMCharacteristics(unittest.TestCase):
    """Phase 11.2 — Segment RFM-score / Recency characteristics."""

    def setUp(self):
        self.segmented_fixture = _segmented_fixture()

    def test_returns_five_segments_in_order(self):
        result = summarize_segment_rfm_characteristics(self.segmented_fixture)
        names = [row["segment"] for row in result["segments"]]
        self.assertEqual(
            names,
            [
                "Champions",
                "Loyal Customers",
                "Average Customers",
                "At-Risk Customers",
                "Lost Customers",
            ],
        )

    def test_total_customers_recomputed(self):
        result = summarize_segment_rfm_characteristics(self.segmented_fixture)
        self.assertEqual(result["total_customers"], 10)

    def test_customer_counts_per_segment(self):
        result = summarize_segment_rfm_characteristics(self.segmented_fixture)
        counts = {row["segment"]: row["customer_count"] for row in result["segments"]}
        self.assertEqual(counts["Champions"], 2)
        self.assertEqual(counts["Lost Customers"], 2)

    def test_recency_score_mean_monotonic(self):
        result = summarize_segment_rfm_characteristics(self.segmented_fixture)
        means = {row["segment"]: row["recency_score_mean"] for row in result["segments"]}
        # Champions must have the best (highest) recency score mean.
        self.assertGreater(means["Champions"], means["Average Customers"])
        self.assertGreater(means["Average Customers"], means["Lost Customers"])

    def test_monetary_score_mean_monotonic(self):
        result = summarize_segment_rfm_characteristics(self.segmented_fixture)
        means = {row["segment"]: row["monetary_score_mean"] for row in result["segments"]}
        self.assertGreater(means["Champions"], means["Average Customers"])
        self.assertGreater(means["Average Customers"], means["Lost Customers"])

    def test_deterministic(self):
        first = summarize_segment_rfm_characteristics(self.segmented_fixture)
        second = summarize_segment_rfm_characteristics(self.segmented_fixture)
        self.assertEqual(first, second)

    def test_input_not_mutated(self):
        import copy

        before = copy.deepcopy(self.segmented_fixture["segmented_table"])
        summarize_segment_rfm_characteristics(self.segmented_fixture)
        import pandas as pd

        pd.testing.assert_frame_equal(
            before, self.segmented_fixture["segmented_table"]
        )

    def test_no_fabrication_total_from_segments(self):
        result = summarize_segment_rfm_characteristics(self.segmented_fixture)
        self.assertEqual(
            result["total_customers"],
            sum(row["customer_count"] for row in result["segments"]),
        )

    def test_each_customer_in_exactly_one_segment(self):
        table = self.segmented_fixture["segmented_table"]
        per_customer = table.groupby("CustomerID")["segment"].nunique()
        self.assertTrue((per_customer == 1).all())
        result = summarize_segment_rfm_characteristics(self.segmented_fixture)
        self.assertEqual(
            int(table["CustomerID"].nunique()),
            sum(row["customer_count"] for row in result["segments"]),
        )
        self.assertEqual(result["total_customers"], int(table["CustomerID"].nunique()))

    def test_missing_segment_column_raises(self):
        fixture = _segmented_fixture()
        fixture["segmented_table"] = fixture["segmented_table"].drop(
            columns=["segment"]
        )
        with self.assertRaises(ValueError):
            summarize_segment_rfm_characteristics(fixture)

    def test_none_segmented_table_raises(self):
        fixture = _segmented_fixture()
        fixture["segmented_table"] = None
        with self.assertRaises(ValueError):
            summarize_segment_rfm_characteristics(fixture)

    def test_empty_segmented_table_raises(self):
        import pandas as pd

        fixture = _segmented_fixture()
        fixture["segmented_table"] = pd.DataFrame()
        with self.assertRaises(ValueError):
            summarize_segment_rfm_characteristics(fixture)

    def test_report_generation_writes_real_data_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / PHASE11_REPORT_FILENAME
            written = generate_phase11_insights_report(dataframe=None, output_path=target)
            self.assertTrue(written.is_file())
            self.assertGreater(written.stat().st_size, 0)
            content = written.read_text(encoding="utf-8")
            self.assertIn("# Phase 11", content)
            self.assertIn("Measured Segment Findings", content)
            self.assertIn("Segment RFM-Score", content)


class TestRevenueInsights(unittest.TestCase):
    """Phase 11.3 — Revenue Insights (measured from real segment monetary)."""

    def setUp(self):
        self.fixture = _segmented_fixture()
        self.revenue = summarize_revenue_insights(self.fixture)

    def test_generates_revenue_insights(self):
        self.assertIn("total_revenue", self.revenue)
        self.assertIn("total_customers", self.revenue)
        self.assertIn("segments", self.revenue)
        self.assertIn("revenue_ranking", self.revenue)

    def test_all_five_segments_present_in_order(self):
        names = [row["segment"] for row in self.revenue["segments"]]
        self.assertEqual(
            names,
            [
                "Champions",
                "Loyal Customers",
                "Average Customers",
                "At-Risk Customers",
                "Lost Customers",
            ],
        )

    def test_total_revenue_is_sum_of_segment_monetary(self):
        table = self.fixture["segmented_table"]
        expected = round(float(table["monetary"].sum()), 2)
        self.assertEqual(self.revenue["total_revenue"], expected)

    def test_segment_revenues_sum_to_total(self):
        total = sum(row["revenue"] for row in self.revenue["segments"])
        self.assertEqual(round(total, 2), self.revenue["total_revenue"])

    def test_total_customers_matches_table(self):
        self.assertEqual(
            self.revenue["total_customers"],
            int(len(self.fixture["segmented_table"])),
        )

    def test_no_fabrication_segment_revenue_from_table(self):
        table = self.fixture["segmented_table"]
        for row in self.revenue["segments"]:
            group = table[table["segment"] == row["segment"]]
            self.assertEqual(row["revenue"], round(float(group["monetary"].sum()), 2))

    def test_revenue_shares_sum_to_100(self):
        shares = sum(r["revenue_share_percent"] for r in self.revenue["segments"])
        self.assertAlmostEqual(shares, 100.0, places=1)

    def test_revenue_share_derived_not_hardcoded(self):
        total = self.revenue["total_revenue"]
        for row in self.revenue["segments"]:
            expected = round(100.0 * row["revenue"] / total, 2)
            self.assertEqual(row["revenue_share_percent"], expected)


    def test_average_and_median_monetary_match_phase9_profiles(self):
        table = self.fixture["segmented_table"]
        for row in self.revenue["segments"]:
            group = table[table["segment"] == row["segment"]]
            self.assertEqual(
                row["monetary_mean"], round(float(group["monetary"].mean()), 2)
            )
            self.assertEqual(
                row["monetary_median"], round(float(group["monetary"].median()), 2)
            )

    def test_known_fixture_values(self):
        rows = {r["segment"]: r for r in self.revenue["segments"]}
        # Fixture: Champions monetary = (3000, 2500); Lost = (100, 90).
        self.assertEqual(rows["Champions"]["monetary_mean"], 2750.0)
        self.assertEqual(rows["Champions"]["monetary_median"], 2750.0)
        self.assertEqual(rows["Lost Customers"]["monetary_mean"], 95.0)
        self.assertEqual(rows["Lost Customers"]["monetary_median"], 95.0)
        self.assertEqual(rows["Champions"]["revenue"], 5500.0)
        self.assertEqual(rows["Lost Customers"]["revenue"], 190.0)

    def test_highest_and_lowest_revenue_segment(self):
        ranking = self.revenue["revenue_ranking"]
        revenues = {r["segment"]: r["revenue"] for r in self.revenue["segments"]}
        self.assertEqual(
            ranking["highest_revenue_segment"], max(revenues, key=revenues.get)
        )
        self.assertEqual(
            ranking["lowest_revenue_segment"], min(revenues, key=revenues.get)
        )
        self.assertEqual(ranking["highest_revenue_segment"], "Champions")
        self.assertEqual(ranking["lowest_revenue_segment"], "Lost Customers")

    def test_highest_revenue_share_percent_consistent(self):
        ranking = self.revenue["revenue_ranking"]
        top = max(r["revenue_share_percent"] for r in self.revenue["segments"])
        self.assertEqual(ranking["highest_revenue_share_percent"], top)

    def test_segment_customer_counts_match_phase8_table(self):
        characteristics = summarize_segment_rfm_characteristics(self.fixture)
        char_counts = {
            r["segment"]: r["customer_count"]
            for r in characteristics["segments"]
        }
        rev_counts = {
            r["segment"]: r["customer_count"]
            for r in self.revenue["segments"]
        }
        self.assertEqual(rev_counts, char_counts)

    def test_revenue_equals_monetary_mean_times_count(self):
        for row in self.revenue["segments"]:
            if row["customer_count"] > 0:
                implied = round(row["monetary_mean"] * row["customer_count"], 2)
                self.assertAlmostEqual(row["revenue"], implied, places=1)

    def test_build_includes_revenue_for_segmented_input(self):
        insights = build_phase11_insights(summary=self.fixture)
        rev = insights["revenue_insights"]
        self.assertEqual(rev["total_revenue"], self.revenue["total_revenue"])
        self.assertEqual(len(rev["segments"]), 5)
        self.assertIn("segment_insights", insights)
        self.assertTrue(insights["segment_characteristics"]["segments"])
        self.assertIn("statistical_insights", insights)

    def test_report_contains_revenue_section_for_real_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / PHASE11_REPORT_FILENAME
            written = generate_phase11_insights_report(
                dataframe=None, output_path=target
            )
            content = written.read_text(encoding="utf-8")
            self.assertIn("Revenue Insights", content)
            self.assertIn("Measured Revenue Facts", content)
            self.assertIn("Revenue Interpretation / Insights", content)

    def test_deterministic(self):
        first = summarize_revenue_insights(_segmented_fixture())
        second = summarize_revenue_insights(_segmented_fixture())
        self.assertEqual(first, second)

    def test_input_not_mutated(self):
        import copy

        import pandas as pd

        before = copy.deepcopy(self.fixture["segmented_table"])
        summarize_revenue_insights(self.fixture)
        pd.testing.assert_frame_equal(before, self.fixture["segmented_table"])

    def test_none_summary_raises(self):
        with self.assertRaises(ValueError):
            summarize_revenue_insights(None)

    def test_missing_keys_raise(self):
        with self.assertRaises(ValueError):
            summarize_revenue_insights({})

    def test_none_segmented_table_raises(self):
        fixture = _segmented_fixture()
        fixture["segmented_table"] = None
        with self.assertRaises(ValueError):
            summarize_revenue_insights(fixture)

    def test_empty_segmented_table_raises(self):
        import pandas as pd

        fixture = _segmented_fixture()
        fixture["segmented_table"] = pd.DataFrame()
        with self.assertRaises(ValueError):
            summarize_revenue_insights(fixture)

    def test_missing_monetary_column_raises(self):
        fixture = _segmented_fixture()
        fixture["segmented_table"] = fixture["segmented_table"].drop(
            columns=["monetary"]
        )
        with self.assertRaises(ValueError):
            summarize_revenue_insights(fixture)


class TestRealDataRevenueInsights(unittest.TestCase):
    """Phase 11.3 — real-data revenue verification through the pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.insights = build_phase11_insights()

    def test_real_data_total_revenue_positive_and_consistent(self):
        rev = self.insights["revenue_insights"]
        self.assertGreater(rev["total_revenue"], 0)
        total = sum(r["revenue"] for r in rev["segments"])
        self.assertAlmostEqual(total, rev["total_revenue"], places=1)

    def test_real_data_shares_sum_to_100(self):
        rev = self.insights["revenue_insights"]
        self.assertAlmostEqual(
            sum(r["revenue_share_percent"] for r in rev["segments"]), 100.0, places=1
        )

    def test_real_data_highest_lowest_revenue_segments(self):
        rev = self.insights["revenue_insights"]
        ranking = rev["revenue_ranking"]
        revenues = {r["segment"]: r["revenue"] for r in rev["segments"]}
        self.assertEqual(
            ranking["highest_revenue_segment"], max(revenues, key=revenues.get)
        )
        self.assertEqual(
            ranking["lowest_revenue_segment"], min(revenues, key=revenues.get)
        )

    def test_real_data_revenue_counts_match_segment_insights(self):
        rev_counts = {
            r["segment"]: r["customer_count"]
            for r in self.insights["revenue_insights"]["segments"]
        }
        seg_counts = {
            r["segment"]: r["customer_count"]
            for r in self.insights["segment_insights"]["segments"]
        }
        self.assertEqual(rev_counts, seg_counts)
        self.assertEqual(sum(rev_counts.values()), 4338)

    def test_real_data_deterministic(self):
        first = build_phase11_insights()["revenue_insights"]
        second = build_phase11_insights()["revenue_insights"]
        self.assertEqual(first, second)

    def test_real_data_report_has_revenue_section(self):
        markdown = render_phase11_insights_markdown(self.insights)
        self.assertIn("Revenue Insights", markdown)
        self.assertIn("Measured Revenue Facts", markdown)


class TestFinalFindings(unittest.TestCase):
    """Phase 11.4 — Final Findings structure & synthesis validation."""

    def setUp(self):
        self.insights = build_phase11_insights()
        self.final = self.insights["final_findings"]

    def test_final_findings_present(self):
        self.assertIn("final_findings", self.final)
        self.assertIn("synthesis_source", self.final)

    def test_final_findings_structure(self):
        findings = self.final["final_findings"]
        self.assertEqual(len(findings), 7)
        for finding in findings:
            self.assertIn("section", finding)
            self.assertIn("measured", finding)
            self.assertIn("interpretation", finding)
            self.assertTrue(finding["section"])
            self.assertTrue(finding["measured"])
            self.assertTrue(finding["interpretation"])

    def test_required_findings_sections(self):
        sections = [f["section"] for f in self.final["final_findings"]]
        self.assertEqual(sections, [
            "1. Overall customer behaviour findings",
            "2. Most important segment findings",
            "3. Most important revenue findings",
            "4. Important RFM patterns",
            "5. Important statistical evidence",
            "6. Most important business / customer observations",
            "7. Overall conclusion",
        ])

    def test_synthesis_source(self):
        self.assertEqual(self.final["synthesis_source"], "11.1 + 11.2 + 11.3")

    def test_consistent_with_customer_insights(self):
        # Final finding #1 must reference the real measured total customer count
        # (Total customers comes from segment_insights, not statistical_insights).
        measured = self.final["final_findings"][0]["measured"]
        self.assertIn("4338", measured)
        self.assertIn("10,642,110.80", measured)

    def test_consistent_with_segment_insights(self):
        seg = self.insights["segment_insights"]
        self.assertEqual(seg["total_customers"], 4338)

    def test_consistent_with_revenue_insights(self):
        rev = self.insights["revenue_insights"]
        measured = self.final["final_findings"][2]["measured"]
        self.assertIn(f"{rev['total_revenue']:,.2f}", measured)

    def test_no_fabricated_values(self):
        for finding in self.final["final_findings"]:
            self.assertNotIn("0.0000", finding["measured"])

class TestFinalFindingsDeterminism(unittest.TestCase):
    """Phase 11.4 determinism & report checks."""

    def test_deterministic(self):
        first = build_phase11_insights()["final_findings"]
        second = build_phase11_insights()["final_findings"]
        self.assertEqual(first, second)

    def test_report_has_final_findings_section(self):
        insights = build_phase11_insights()
        markdown = render_phase11_insights_markdown(insights)
        self.assertIn("## Final Findings (11.4)", markdown)
        self.assertIn("### 7. Overall conclusion", markdown)

    def test_report_measures_and_interpretation(self):
        insights = build_phase11_insights()
        markdown = render_phase11_insights_markdown(insights)
        self.assertIn("**Measured facts:**", markdown)
        self.assertIn("**Final interpretation / findings:**", markdown)


class TestFinalFindingsInputHandling(unittest.TestCase):
    """Phase 11.4 — invalid / empty input handling & non-mutation."""

    def test_none_input_raises(self):
        with self.assertRaises(ValueError):
            summarize_final_findings(None)

    def test_non_dict_input_raises(self):
        with self.assertRaises(ValueError):
            summarize_final_findings("not-a-dict")

    def test_missing_subresult_raises(self):
        with self.assertRaises(ValueError):
            summarize_final_findings({"segment_insights": {}})

    def test_empty_dict_input_raises(self):
        with self.assertRaises(ValueError):
            summarize_final_findings({})

    def test_empty_segments_handled(self):
        base = build_phase11_insights()
        insights = {
            "customer_insights": base["statistical_insights"],
            "segment_insights": {"segments": [], "total_customers": 0},
            "segment_characteristics": {"segments": [], "total_customers": 0},
            "revenue_insights": {"total_revenue": 0.0, "segments": [], "revenue_ranking": {}},
            "statistical_insights": base["statistical_insights"],
        }
        result = summarize_final_findings(insights)
        self.assertIn("final_findings", result)


class TestRealDataFinalFindings(unittest.TestCase):
    """Phase 11.4 — real-data verification of final findings."""

    def setUp(self):
        self.insights = build_phase11_insights()
        self.final = self.insights["final_findings"]["final_findings"]
        self.rev = self.insights["revenue_insights"]
        self.seg = self.insights["segment_insights"]

    def test_real_data_customer_count_referenced(self):
        self.assertIn(str(self.seg["total_customers"]), self.final[0]["measured"])

    def test_real_data_total_revenue_referenced(self):
        self.assertIn(f"{self.rev['total_revenue']:,.2f}", self.final[2]["measured"])

    def test_real_data_top_revenue_segment(self):
        top_seg = self.rev["revenue_ranking"]["highest_revenue_segment"]
        self.assertIn(top_seg, self.final[2]["measured"])

    def test_real_data_largest_segment(self):
        rows = self.seg["segments"]
        largest = max(rows, key=lambda r: r["customer_count"])["segment"]
        self.assertIn(largest, self.final[1]["measured"])

    def test_real_data_smallest_segment(self):
        rows = self.seg["segments"]
        smallest = min(rows, key=lambda r: r["customer_count"])["segment"]
        self.assertIn(smallest, self.final[1]["measured"])

    def test_real_data_fm_correlation(self):
        corrs = self.insights["statistical_insights"]["correlations"]
        fm = corrs.get(("Frequency", "Monetary"))
        if fm:
            self.assertIn(f"{fm['pearson_r']:.3f}", self.final[3]["measured"])

    def test_real_data_deterministic(self):
        first = build_phase11_insights()["final_findings"]
        second = build_phase11_insights()["final_findings"]
        self.assertEqual(first, second)


class TestReportCompatibility(unittest.TestCase):
    """Phase 11.4 — report compatibility across 11.1/11.2/11.3/11.4."""

    def test_report_contains_all_phases(self):
        insights = build_phase11_insights()
        markdown = render_phase11_insights_markdown(insights)
        self.assertIn("## 1. Measured Segment Findings", markdown)
        self.assertIn("## 1.1 Segment RFM-Score & Recency Characteristics", markdown)
        self.assertIn("## 1.2 Revenue Insights (11.3)", markdown)
        self.assertIn("## Final Findings (11.4)", markdown)

    def test_report_final_findings_measures(self):
        insights = build_phase11_insights()
        markdown = render_phase11_insights_markdown(insights)
        self.assertIn("**Measured facts:**", markdown)
        self.assertIn("**Final interpretation / findings:**", markdown)

    def test_report_synthesis_source(self):
        insights = build_phase11_insights()
        markdown = render_phase11_insights_markdown(insights)
        self.assertIn("*Synthesis source: 11.1 + 11.2 + 11.3*", markdown)


if __name__ == "__main__":
    unittest.main()
