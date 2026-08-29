"""
tests/test_functional.py - Phase 12.1: Functional Testing.

This is a DEDICATED Phase 12.1 validation module. It exercises the implemented
project functionality across the completed phases against the REAL project
dataset (no synthetic data), verifying that each pipeline component actually
executes successfully and produces usable, internally-consistent output.

Functional scope covered (real data):
    Phase 1-3 consistency  - approved dataset decisions & requirements
    Phase 4                - raw dataset loading, data types, file handling
    Phase 5                - cleaning pipeline outputs (missing value,
                             duplicate and invalid-data handling)
    Phase 6                - EDA / descriptive analysis
    Phase 7                - RFM calculation and RFM scoring
    Phase 8                - customer segmentation assignment & summary
    Phase 9                - statistical analysis functionality
    Phase 10               - visualization generation (four approved charts)
    Phase 11               - customer / segment / revenue / final findings
                             insights + Phase 11 report generation

Phase 12.1 does NOT modify source code. It only verifies the existing
functionality. No Phase 13 (main.py orchestration) work is performed.
"""

import hashlib
import pathlib
import unittest

import pandas as pd

import config
from src.data_cleaning import (
    get_cleaned_dataset_path,
    get_deduplicated_dataset_path,
    get_invalid_removed_dataset_path,
)
from src.data_loading import load_raw_dataset
from src.rfm_analysis import build_rfm_analysis, load_phase7_dataset
from src.segmentation import build_segmentation
from src.statistics_analysis import (
    build_phase6_eda_summary,
    build_phase9_statistical_summary,
)

# Real-data facts recorded from the executed pipeline (recomputed, not
# asserted from hard-coded values where possible).
REAL_RAW_ROWS = 541909
REAL_RAW_SIZE = 47901468
REAL_CUSTOMERS = 4338
REAL_WORKING_ROWS = 524878
REAL_TOTAL_REVENUE = 10642110.80
RAW_SHA256 = "BFA47136118BC854A31E69D5C9E9689A2D07B73909F253679F2CC85EC4EB84EB"

RAW_DATA_PATH = config.RAW_DATA_DIR / "OnlineRetail.csv"
REPORT_PATH = config.REPORTS_DIR / "phase11_insights_report.md"


class TestPhase1to3Consistency(unittest.TestCase):
    """Phase 12.1 - consistency of the project definitions / dataset decisions."""

    def test_raw_dataset_path_and_filename(self):
        """The approved Phase 3 dataset decision (OnlineRetail.csv) is intact."""
        self.assertTrue(RAW_DATA_PATH.is_file())
        self.assertEqual(RAW_DATA_PATH.name, "OnlineRetail.csv")

    def test_raw_dataset_hash_matches_approved(self):
        """Raw dataset SHA-256 still equals the approved hash (case-insensitive)."""
        actual = hashlib.sha256(RAW_DATA_PATH.read_bytes()).hexdigest().upper()
        self.assertEqual(actual, RAW_SHA256)

    def test_approved_columns_present_in_raw(self):
        approved = [
            "InvoiceNo", "StockCode", "Description", "Quantity",
            "InvoiceDate", "UnitPrice", "CustomerID", "Country",
        ]
        df = pd.read_csv(RAW_DATA_PATH, nrows=0)
        self.assertTrue(set(approved).issubset(set(df.columns)))


class TestPhase4Functional(unittest.TestCase):
    """Phase 12.1 - Phase 4 data loading functional checks."""

    def test_raw_dataset_loads(self):
        df = load_raw_dataset()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertEqual(len(df), REAL_RAW_ROWS)

    def test_raw_dataset_filesize(self):
        self.assertEqual(RAW_DATA_PATH.stat().st_size, 47901468)

    def test_raw_columns_and_datetime(self):
        df = load_raw_dataset()
        self.assertIn("InvoiceDate", df.columns)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]))


class TestPhase5Functional(unittest.TestCase):
    """Phase 12.1 - Phase 5 cleaning outputs exist and are usable."""

    def test_phase5_working_dataset_loads(self):
        df = load_phase7_dataset()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertEqual(len(df), REAL_WORKING_ROWS)

    def test_phase5_working_dataset_usable_columns(self):
        df = load_phase7_dataset()
        self.assertIn("InvoiceDate", df.columns)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]))


class TestPhase6Functional(unittest.TestCase):
    """Phase 12.1 - Phase 6 EDA functionality."""

    def test_eda_summary_executes(self):
        summary = build_phase6_eda_summary()
        self.assertIn("dataset_summary", summary)
        self.assertIn("distribution_summary", summary)
        self.assertIn("monthly_trends", summary)

    def test_dataset_summary_values(self):
        summary = build_phase6_eda_summary()["dataset_summary"]
        self.assertEqual(summary["unique_customers"], REAL_CUSTOMERS)
        # total_revenue is a float; compare with tolerance due to float
        # precision (10642110.804000001 vs the rounded reference 10642110.80).
        self.assertAlmostEqual(summary["total_revenue"], REAL_TOTAL_REVENUE, places=1)


class TestPhase7Functional(unittest.TestCase):
    """Phase 12.1 - Phase 7 RFM calculation functionality."""

    def test_rfm_table_executes(self):
        result = build_rfm_analysis()
        rfm_table = result["rfm_table"]
        self.assertEqual(len(rfm_table), REAL_CUSTOMERS)

    def test_rfm_score_columns_range(self):
        result = build_rfm_analysis()
        rfm_table = result["rfm_table"]
        for col in ["recency_score", "frequency_score", "monetary_score"]:
            self.assertTrue((rfm_table[col] >= 1).all())
            self.assertTrue((rfm_table[col] <= 5).all())

    def test_rfm_reference_date_present(self):
        result = build_rfm_analysis()
        self.assertIn("reference_date", result)


class TestPhase8Functional(unittest.TestCase):
    """Phase 12.1 - Phase 8 segmentation functionality."""

    def test_segmentation_executes(self):
        result = build_segmentation()
        segmented = result["segmented_table"]
        self.assertEqual(len(segmented), REAL_CUSTOMERS)
        self.assertIn("segment", segmented.columns)

    def test_segment_summary_covers_all_customers(self):
        result = build_segmentation()
        summary = result["segment_summary"]
        self.assertEqual(sum(summary.values()), REAL_CUSTOMERS)
        segmented = result["segmented_table"]
        self.assertEqual(segmented["segment"].nunique(), 5)


class TestPhase9Functional(unittest.TestCase):
    """Phase 12.1 - Phase 9 statistical analysis functionality."""

    def test_statistical_summary_executes(self):
        summary = build_phase9_statistical_summary()
        self.assertIn("correlations", summary)
        self.assertIn("normality_tests", summary)
        self.assertIn("segment_profiles", summary)
        self.assertIn("segment_comparison_tests", summary)


class TestPhase10Functional(unittest.TestCase):
    """Phase 12.1 - Phase 10 visualization generation."""

    def test_charts_generate_four_outputs(self):
        from src.visualization import build_phase10_visualizations

        charts = build_phase10_visualizations()
        expected = {
            "rfm_score_distributions",
            "segment_size_bar",
            "segment_monetary_box",
            "rfm_metric_correlation_scatter",
        }
        self.assertEqual(set(charts.keys()), expected)
        for name, path in charts.items():
            self.assertTrue(pathlib.Path(path).is_file(), name)

    def test_four_chart_files_exist_on_disk(self):
        names = [
            "rfm_score_distributions.png",
            "segment_size_bar.png",
            "segment_monetary_box.png",
            "rfm_metric_correlation_scatter.png",
        ]
        for name in names:
            self.assertTrue((config.CHARTS_DIR / name).is_file(), name)


class TestPhase11Functional(unittest.TestCase):
    """Phase 12.1 - Phase 11 insights / report functional checks."""

    def test_phase11_insights_executes(self):
        from src.insights import build_phase11_insights

        insights = build_phase11_insights()
        for key in [
            "segment_insights",
            "segment_characteristics",
            "revenue_insights",
            "statistical_insights",
            "final_findings",
        ]:
            self.assertIn(key, insights)
        self.assertEqual(
            insights["segment_insights"]["total_customers"], REAL_CUSTOMERS
        )

    def test_revenue_insights_executes(self):
        from src.insights import build_phase11_insights

        revenue = build_phase11_insights()["revenue_insights"]
        self.assertAlmostEqual(revenue["total_revenue"], REAL_TOTAL_REVENUE, places=2)
        self.assertTrue(revenue["revenue_ranking"]["highest_revenue_segment"])

    def test_final_findings_executes(self):
        from src.insights import build_phase11_insights

        final = build_phase11_insights()["final_findings"]
        self.assertGreaterEqual(len(final["final_findings"]), 7)

    def test_phase11_report_generation(self):
        from src.insights import generate_phase11_insights_report

        report = generate_phase11_insights_report(output_path=REPORT_PATH)
        self.assertTrue(pathlib.Path(report).is_file())
        self.assertGreater(pathlib.Path(report).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()