"""
tests/test_data_validation.py - Phase 12.2: Data Validation.

This is a DEDICATED Phase 12.2 validation module. It validates the integrity
and consistency of the REAL project dataset through the completed pipeline.

It focuses on CROSS-PIPELINE data-integrity consistency (raw -> Phase 5 ->
Phase 7 RFM -> Phase 8 segmentation -> Phase 9 statistics -> Phase 11
insights). Individual unit behaviour is already covered by the per-phase test
modules; this module deliberately does NOT duplicate them.

Rules used are the ones already established in Phase 5 (no new cleaning rules
are invented). The raw dataset is immutable; SHA-256 and size must never change.
"""

import hashlib
import unittest

import pandas as pd

import config
from src.data_cleaning import (
    APPROVED_COLUMNS,
    get_cleaned_dataset_path,
    get_deduplicated_dataset_path,
    get_invalid_removed_dataset_path,
)
from src.data_loading import load_raw_dataset
from src.rfm_analysis import build_rfm_analysis
from src.segmentation import build_segmentation, SEGMENT_NAMES

RAW_ROWS = 541909
RAW_COLUMNS = 8
RAW_SIZE = 47901468
RAW_SHA256 = "BFA47136118BC854A31E69D5C9E9689A2D07B73909F253679F2CC85EC4EB84EB"
WORKING_ROWS = 524878
EXPECTED_CUSTOMERS = 4338
EXPECTED_REVENUE = 10642110.80
SEGMENT_NAME_ORDER = list(SEGMENT_NAMES)

RAW_PATH = config.RAW_DATA_DIR / "OnlineRetail.csv"
WORKING_CSV = config.PROCESSED_DATA_DIR / "OnlineRetail_invalid_removed.csv"
class TestRawDataIntegrity(unittest.TestCase):
    """Phase 12.2 - raw data integrity."""

    def test_file_exists_and_name(self):
        self.assertTrue(RAW_PATH.is_file())
        self.assertEqual(RAW_PATH.name, "OnlineRetail.csv")

    def test_expected_shape(self):
        df = load_raw_dataset()
        self.assertEqual(df.shape, (RAW_ROWS, RAW_COLUMNS))

    def test_expected_columns(self):
        df = load_raw_dataset()
        self.assertEqual(list(df.columns), APPROVED_COLUMNS)

    def test_data_types(self):
        df = load_raw_dataset()
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(df["Quantity"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(df["UnitPrice"]))

    def test_sha256_unchanged(self):
        actual = hashlib.sha256(RAW_PATH.read_bytes()).hexdigest().upper()
        self.assertEqual(actual, RAW_SHA256)

    def test_filesize_unchanged(self):
        self.assertEqual(RAW_PATH.stat().st_size, RAW_SIZE)

    def test_raw_no_modification(self):
        before = hashlib.sha256(RAW_PATH.read_bytes()).hexdigest()
        load_raw_dataset()
        after = hashlib.sha256(RAW_PATH.read_bytes()).hexdigest()
        self.assertEqual(before, after)


class TestPhase5ProcessedData(unittest.TestCase):
    """Phase 12.2 - Phase 5 processed datasets exist and are consistent."""

    def test_final_working_dataset_schema(self):
        df = pd.read_csv(WORKING_CSV, parse_dates=["InvoiceDate"], dtype={'InvoiceNo': str})
        self.assertEqual(list(df.columns), APPROVED_COLUMNS)

    def test_final_working_dataset_rows(self):
        df = pd.read_csv(WORKING_CSV, parse_dates=["InvoiceDate"])
        self.assertEqual(len(df), 524878)

    def test_no_unexpected_column_loss(self):
        df = pd.read_csv(WORKING_CSV, parse_dates=["InvoiceDate"])
        self.assertEqual(set(df.columns), set(APPROVED_COLUMNS))

    def test_required_fields_usable(self):
        df = pd.read_csv(WORKING_CSV, parse_dates=["InvoiceDate"])
        self.assertEqual(int(df["CustomerID"].isna().sum()), 0)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]))


class TestDataQuality(unittest.TestCase):
    """Phase 12.2 - data quality of the final working dataset (Phase 5 rules)."""

    @staticmethod
    def _load():
        return pd.read_csv(WORKING_CSV, parse_dates=["InvoiceDate"])

    def test_required_columns_present(self):
        df = self._load()
        for col in APPROVED_COLUMNS:
            self.assertIn(col, df.columns)

    def test_no_missing_customer_id(self):
        self.assertEqual(int(self._load()["CustomerID"].isna().sum()), 0)

    def test_invalid_quantity_rules(self):
        self.assertEqual(int((self._load()["Quantity"] <= 0).sum()), 0)

    def test_invalid_unitprice_rules(self):
        self.assertEqual(int((self._load()["UnitPrice"] <= 0).sum()), 0)

    def test_no_cancellation_invoices(self):
        df = self._load()
        self.assertEqual(int(df["InvoiceNo"].astype(str).str.startswith("C").sum()), 0)

    def test_no_duplicate_records(self):
        self.assertEqual(int(self._load().duplicated().sum()), 0)

    def test_numeric_columns_numeric(self):
        df = self._load()
        for col in ("Quantity", "UnitPrice"):
            self.assertTrue(pd.api.types.is_numeric_dtype(df[col]), col)

    def test_datetime_column_compatible(self):
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self._load()["InvoiceDate"]))
class TestCustomerConsistency(unittest.TestCase):
    """Phase 12.2 - CustomerID population and consistency across RFM/segmentation."""

    def test_customerid_populated(self):
        raw = load_raw_dataset()
        self.assertEqual(int(raw["CustomerID"].isna().sum()), 0)
        df = pd.read_csv(WORKING_CSV, parse_dates=["InvoiceDate"])
        self.assertEqual(int(df["CustomerID"].isna().sum()), 0)

    def test_unique_customer_count(self):
        df = pd.read_csv(WORKING_CSV, parse_dates=["InvoiceDate"])
        self.assertEqual(df["CustomerID"].nunique(), 4338)

    def test_single_customer_row_in_rfm(self):
        rfm = build_rfm_analysis()["rfm_table"]
        self.assertEqual(int(rfm["CustomerID"].duplicated().sum()), 0)
        self.assertEqual(len(rfm), 4338)

    def test_customer_count_matches_segmentation(self):
        seg = build_segmentation()
        self.assertEqual(len(seg["segmented_table"]), 4338)
        self.assertEqual(seg["segmented_table"]["CustomerID"].nunique(), 4338)


class TestRFMDataConsistency(unittest.TestCase):
    """Phase 12.2 - RFM (Phase 7) data integrity (data only, not 12.3 methodology)."""

    @staticmethod
    def _rfm():
        return build_rfm_analysis()["rfm_table"]

    def test_one_row_per_customer(self):
        rfm = self._rfm()
        self.assertEqual(len(rfm), rfm["CustomerID"].nunique())

    def test_no_missing_rfm_values(self):
        self.assertEqual(int(self._rfm().isna().sum().sum()), 0)

    def test_score_values_in_1_to_5(self):
        rfm = self._rfm()
        for col in ("recency_score", "frequency_score", "monetary_score"):
            self.assertTrue((rfm[col] >= 1).all())
            self.assertTrue((rfm[col] <= 5).all())

    def test_recency_valid(self):
        self.assertTrue((self._rfm()["recency_days"] >= 0).all())

    def test_frequency_valid(self):
        self.assertTrue((self._rfm()["frequency"] > 0).all())

    def test_monetary_valid(self):
        self.assertTrue((self._rfm()["monetary"] > 0).all())

    def test_monetary_consistency(self):
        self.assertAlmostEqual(self._rfm()["monetary"].sum(), EXPECTED_REVENUE, places=1)


class TestSegmentDataConsistency(unittest.TestCase):
    """Phase 12.2 - Segment (Phase 8) data consistency (rules unchanged)."""

    @staticmethod
    def _seg():
        return build_segmentation()

    def test_every_customer_one_segment(self):
        segtable = self._seg()["segmented_table"]
        self.assertEqual(int(segtable["segment"].isna().sum()), 0)
        self.assertEqual(len(segtable), segtable["CustomerID"].nunique())

    def test_only_approved_five_segments(self):
        segtable = self._seg()["segmented_table"]
        self.assertEqual(set(segtable["segment"].unique()), set(SEGMENT_NAMES))

    def test_segment_counts_sum_to_total(self):
        seg = self._seg()
        self.assertEqual(sum(seg["segment_summary"].values()), 4338)

    def test_summary_agrees_with_table(self):
        seg = self._seg()
        segtable = seg["segmented_table"]
        for name in SEGMENT_NAME_ORDER:
            self.assertEqual(int((segtable["segment"] == name).sum()),
                             seg["segment_summary"][name])

    def test_known_counts_match(self):
        segtable = self._seg()["segmented_table"]
        expected = {
            "Champions": 923, "Loyal Customers": 983, "Average Customers": 1040,
            "At-Risk Customers": 1058, "Lost Customers": 334,
        }
        for name, count in expected.items():
            self.assertEqual(int((segtable["segment"] == name).sum()), count)


class TestStatisticalInputConsistency(unittest.TestCase):
    """Phase 12.2 - Data supplied to Phase 9 statistics is consistent."""

    @staticmethod
    def _stats():
        from src.statistics_analysis import build_phase9_statistical_summary
        return build_phase9_statistical_summary()

    def test_required_columns_present(self):
        required = {"CustomerID", "recency_days", "frequency", "monetary", "segment"}
        segmented = self._stats()["segmented_table"]
        self.assertTrue(required.issubset(set(segmented.columns)))

    def test_numeric_values_valid(self):
        segmented = self._stats()["segmented_table"]
        for col in ("recency_days", "frequency", "monetary"):
            self.assertTrue(pd.api.types.is_numeric_dtype(segmented[col]), col)
        self.assertTrue((segmented["monetary"] > 0).all())

    def test_consistent_customer_counts(self):
        self.assertEqual(len(self._stats()["segmented_table"]), 4338)

    def test_no_unexpected_missing(self):
        self.assertEqual(int(self._stats()["segmented_table"].isna().sum().sum()), 0)
class TestVisualizationDataConsistency(unittest.TestCase):
    """Phase 12.2 - Phase 10 receives valid data and charts exist (no new charts)."""

    def test_phase10_input_valid(self):
        from src.visualization import build_phase10_visualization_input
        segmented = build_phase10_visualization_input()
        self.assertEqual(len(segmented), 4338)
        self.assertIn("segment", segmented.columns)

    def test_four_approved_charts_present(self):
        names = [
            "rfm_score_distributions.png",
            "segment_size_bar.png",
            "segment_monetary_box.png",
            "rfm_metric_correlation_scatter.png",
        ]
        for name in names:
            self.assertTrue((config.CHARTS_DIR / name).is_file(), name)


class TestInsightsDataConsistency(unittest.TestCase):
    """Phase 12.2 - Phase 11 insight totals agree with the underlying data."""

    @staticmethod
    def _ins():
        from src.insights import build_phase11_insights
        return build_phase11_insights()

    def test_segment_count_agrees(self):
        ins = self._ins()
        seg = build_segmentation()
        self.assertEqual(ins["segment_insights"]["total_customers"], 4338)
        self.assertEqual(ins["segment_insights"]["total_customers"],
                         sum(seg["segment_summary"].values()))

    def test_revenue_agrees(self):
        ins = self._ins()
        rfm = build_rfm_analysis()["rfm_table"]
        self.assertAlmostEqual(ins["revenue_insights"]["total_revenue"],
                               rfm["monetary"].sum(), places=1)

    def test_segment_insight_counts_agree(self):
        ins = self._ins()
        seg = build_segmentation()
        for row in ins["segment_insights"]["segments"]:
            self.assertEqual(int(row["customer_count"]),
                             seg["segment_summary"][row["segment"]])


if __name__ == "__main__":
    unittest.main()