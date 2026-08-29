import unittest

import pandas as pd

from src.statistics_analysis import (
    build_phase6_eda_summary,
    get_dataset_summary,
    load_phase6_dataset,
    summarize_monthly_trends,
    summarize_numeric_distributions,
    summarize_relationships,
)
from src.segmentation import SEGMENT_NAMES
from src.statistics_analysis import (
    build_phase9_statistical_input,
    build_phase9_statistical_summary,
    summarize_normality_tests,
    summarize_segment_comparison_tests,
    summarize_segment_profiles,
    summarize_statistical_correlations,
)


class TestPhase6EDA(unittest.TestCase):
    def test_dataset_loads_and_has_expected_shape(self):
        df = load_phase6_dataset()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (524878, 8))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]))

    def test_dataset_summary_uses_real_metrics(self):
        summary = get_dataset_summary()
        self.assertEqual(summary["row_count"], 524878)
        self.assertEqual(summary["unique_customers"], 4338)
        self.assertEqual(summary["unique_invoices"], 19960)
        self.assertEqual(summary["unique_countries"], 38)
        self.assertAlmostEqual(summary["total_revenue"], 10642110.80, places=2)
        self.assertAlmostEqual(summary["avg_quantity_per_transaction"], 10.616600429052085, places=6)
        self.assertAlmostEqual(summary["avg_unit_price"], 3.9225725673394582, places=6)

    def test_numeric_distribution_summary_matches_expected_values(self):
        summary = summarize_numeric_distributions()
        self.assertAlmostEqual(summary["quantity"]["mean"], 10.616600429052085, places=6)
        self.assertAlmostEqual(summary["quantity"]["median"], 4.0, places=6)
        self.assertAlmostEqual(summary["unit_price"]["mean"], 3.9225725673394582, places=6)
        self.assertAlmostEqual(summary["unit_price"]["median"], 2.08, places=6)

    def test_monthly_trends_are_computed(self):
        trends = summarize_monthly_trends()
        self.assertIn("2010-12", trends)
        self.assertEqual(trends["2010-12"]["transactions"], 1559)
        self.assertAlmostEqual(trends["2010-12"]["revenue"], 821452.73, places=2)

    def test_relationship_summary_is_derived_from_supplied_data(self):
        dataframe = pd.DataFrame(
            {
                "Quantity": [1, 2, 3],
                "UnitPrice": [2.0, 4.0, 6.0],
            }
        )
        relationships = summarize_relationships(dataframe)
        self.assertEqual(set(relationships), {"Quantity", "UnitPrice", "revenue"})
        self.assertAlmostEqual(
            relationships["Quantity"]["revenue"],
            0.989743318610787,
        )
        self.assertAlmostEqual(
            relationships["UnitPrice"]["revenue"],
            0.989743318610787,
        )

    def test_complete_summary_includes_relationships(self):
        summary = build_phase6_eda_summary()
        self.assertIn("relationship_summary", summary)
        self.assertAlmostEqual(
            summary["relationship_summary"]["Quantity"]["Quantity"],
            1.0,
        )


# ---------------------------------------------------------------------------
# Phase 9 — Statistical Analysis tests
# ---------------------------------------------------------------------------


def _phase9_segmented_fixture():
    """Ten customers across the five segments with known RFM metrics.

    All RFM metrics are strictly monotonic across customers and contain no
    tied values (higher Frequency -> higher Monetary; higher Recency -> lower
    Frequency), so the Spearman correlations are exact (+/- 1.0) and fully
    deterministic.
    """
    return pd.DataFrame(
        {
            "CustomerID": ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"],
            "recency_days": [1, 2, 10, 12, 30, 33, 60, 70, 120, 150],
            "frequency": [20, 19, 18, 17, 16, 15, 14, 13, 12, 11],
            "monetary": [1000.0, 950.0, 900.0, 850.0, 800.0, 750.0, 700.0, 650.0, 600.0, 550.0],
            "segment": (
                ["Champions"] * 2
                + ["Loyal Customers"] * 2
                + ["Average Customers"] * 2
                + ["At-Risk Customers"] * 2
                + ["Lost Customers"] * 2
            ),
        }
    )


class TestPhase9Correlations(unittest.TestCase):
    def test_fixture_spearman_exact(self):
        corr = summarize_statistical_correlations(_phase9_segmented_fixture())
        self.assertAlmostEqual(
            corr["recency_days_vs_frequency"]["spearman_rho"], -1.0, places=6
        )
        self.assertAlmostEqual(
            corr["frequency_vs_monetary"]["spearman_rho"], 1.0, places=6
        )
        self.assertAlmostEqual(
            corr["recency_days_vs_monetary"]["spearman_rho"], -1.0, places=6
        )

    def test_fixture_pearson_signs(self):
        corr = summarize_statistical_correlations(_phase9_segmented_fixture())
        self.assertLess(corr["recency_days_vs_frequency"]["pearson_r"], 0)
        self.assertGreater(corr["frequency_vs_monetary"]["pearson_r"], 0)
        self.assertLess(corr["recency_days_vs_monetary"]["pearson_r"], 0)

    def test_correlation_structure(self):
        corr = summarize_statistical_correlations(_phase9_segmented_fixture())
        self.assertEqual(
            set(corr),
            {
                "recency_days_vs_frequency",
                "recency_days_vs_monetary",
                "frequency_vs_monetary",
            },
        )
        for value in corr.values():
            self.assertEqual(value["n"], 10)
            self.assertIn("pearson_r", value)
            self.assertIn("pearson_p_value", value)
            self.assertIn("spearman_rho", value)
            self.assertIn("spearman_p_value", value)


class TestPhase9Normality(unittest.TestCase):
    def test_structure_and_p_range(self):
        result = summarize_normality_tests(_phase9_segmented_fixture())
        self.assertIn("recency_days", result)
        self.assertIn("frequency", result)
        self.assertIn("monetary", result)
        for value in result.values():
            self.assertEqual(value["n"], 10)
            self.assertTrue(0 <= value["p_value"] <= 1)

    def test_is_normal_flag_boolean(self):
        result = summarize_normality_tests(_phase9_segmented_fixture())
        self.assertIsInstance(result["frequency"]["is_normal_at_0_05"], bool)


class TestPhase9SegmentProfiles(unittest.TestCase):
    def test_profiles_cover_all_segments(self):
        profiles = summarize_segment_profiles(_phase9_segmented_fixture())
        self.assertEqual(set(profiles), set(SEGMENT_NAMES))

    def test_profiles_known_fixture_values(self):
        profiles = summarize_segment_profiles(_phase9_segmented_fixture())
        self.assertEqual(profiles["Champions"]["customer_count"], 2)
        self.assertAlmostEqual(profiles["Champions"]["frequency_mean"], 19.5, places=6)
        self.assertAlmostEqual(profiles["Champions"]["monetary_mean"], 975.0, places=6)
        self.assertAlmostEqual(profiles["Lost Customers"]["monetary_mean"], 575.0, places=6)

    def test_profile_counts_sum_to_total(self):
        profiles = summarize_segment_profiles(_phase9_segmented_fixture())
        self.assertEqual(sum(p["customer_count"] for p in profiles.values()), 10)

class TestPhase9ComparisonTests(unittest.TestCase):
    def test_kruskal_wallis_fixture(self):
        result = summarize_segment_comparison_tests(_phase9_segmented_fixture())
        frequency = result["frequency_kruskal_wallis"]
        monetary = result["monetary_kruskal_wallis"]
        self.assertEqual(frequency["groups"], 5)
        self.assertEqual(frequency["df"], 4)
        self.assertGreater(frequency["statistic"], 0)
        self.assertTrue(0 <= frequency["p_value"] <= 1)
        self.assertEqual(monetary["groups"], 5)
        self.assertEqual(monetary["df"], 4)
        self.assertGreater(monetary["statistic"], 0)
        self.assertTrue(0 <= monetary["p_value"] <= 1)

    def test_mannwhitney_champions_vs_lost_separated(self):
        result = summarize_segment_comparison_tests(_phase9_segmented_fixture())
        mw = result["champions_vs_lost_frequency_mannwhitney"]
        self.assertEqual(mw["n_champions"], 2)
        self.assertEqual(mw["n_lost"], 2)
        # Every champion frequency exceeds every lost frequency -> maximum U.
        self.assertEqual(mw["statistic"], 4.0)
        self.assertTrue(0 <= mw["p_value"] <= 1)


class TestPhase9ValidationErrors(unittest.TestCase):
    def test_empty_input_raises(self):
        empty = _phase9_segmented_fixture().iloc[0:0]
        with self.assertRaises(ValueError):
            summarize_statistical_correlations(empty)
        with self.assertRaises(ValueError):
            summarize_segment_profiles(empty)

    def test_empty_dataframe_raises(self):
        with self.assertRaises(ValueError):
            summarize_statistical_correlations(pd.DataFrame())

    def test_missing_required_column_raises(self):
        df = _phase9_segmented_fixture().drop(columns=["segment"])
        with self.assertRaises(ValueError):
            summarize_segment_profiles(df)

    def test_non_numeric_metric_raises(self):
        df = _phase9_segmented_fixture().copy()
        df["monetary"] = df["monetary"].astype(str)
        with self.assertRaises(ValueError):
            summarize_statistical_correlations(df)

    def test_comparison_requires_two_segments(self):
        df = _phase9_segmented_fixture().iloc[:2]  # only Champions
        with self.assertRaises(ValueError):
            summarize_segment_comparison_tests(df)

    def test_comparison_requires_two_per_segment(self):
        df = pd.concat(
            [
                _phase9_segmented_fixture().iloc[[0]],
                _phase9_segmented_fixture().iloc[2:4],
            ]
        )
        with self.assertRaises(ValueError):
            summarize_segment_comparison_tests(df)


class TestPhase9RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = build_phase9_statistical_summary()

    def test_real_data_analytical_table(self):
        segmented = self.summary["segmented_table"]
        self.assertEqual(len(segmented), 4338)
        self.assertEqual(segmented["CustomerID"].is_unique, True)
        self.assertIn("segment", segmented.columns)

    def test_real_data_correlations_finite_in_range(self):
        corr = self.summary["correlations"]
        self.assertEqual(
            set(corr),
            {
                "recency_days_vs_frequency",
                "recency_days_vs_monetary",
                "frequency_vs_monetary",
            },
        )
        for value in corr.values():
            self.assertEqual(value["n"], 4338)
            self.assertTrue(-1.0 <= value["pearson_r"] <= 1.0)
            self.assertTrue(-1.0 <= value["spearman_rho"] <= 1.0)
            self.assertTrue(0 <= value["pearson_p_value"] <= 1)
            self.assertTrue(0 <= value["spearman_p_value"] <= 1)

    def test_real_data_normality_is_non_normal(self):
        normality = self.summary["normality_tests"]
        for metric in ("recency_days", "frequency", "monetary"):
            self.assertEqual(normality[metric]["n"], 4338)
            self.assertFalse(normality[metric]["is_normal_at_0_05"])

    def test_real_data_profiles_sum_to_customer_count(self):
        profiles = self.summary["segment_profiles"]
        self.assertEqual(set(profiles), set(SEGMENT_NAMES))
        self.assertEqual(sum(p["customer_count"] for p in profiles.values()), 4338)
        self.assertEqual(sum(self.summary["segment_summary"].values()), 4338)

    def test_real_data_comparison_tests(self):
        comparison = self.summary["segment_comparison_tests"]
        self.assertEqual(comparison["frequency_kruskal_wallis"]["df"], 4)
        self.assertGreater(comparison["frequency_kruskal_wallis"]["statistic"], 0)
        self.assertGreater(comparison["monetary_kruskal_wallis"]["statistic"], 0)
        for key in (
            "frequency_kruskal_wallis",
            "monetary_kruskal_wallis",
            "champions_vs_lost_frequency_mannwhitney",
            "champions_vs_lost_monetary_mannwhitney",
        ):
            self.assertIn("p_value", comparison[key])
            self.assertTrue(0 <= comparison[key]["p_value"] <= 1)

    def test_real_data_deterministic(self):
        segmented = self.summary["segmented_table"]
        first = summarize_statistical_correlations(segmented)
        second = summarize_statistical_correlations(segmented)
        self.assertEqual(first, second)

if __name__ == "__main__":
    unittest.main()
