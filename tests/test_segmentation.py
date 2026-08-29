"""
tests/test_segmentation.py - Phase 8: Customer Segmentation tests.

Internal unit-style tests (Python built-in unittest only, consistent with the
project dependency policy - pytest is NOT an approved dependency).

Coverage:
    - Valid scored RFM input
    - Segment column creation
    - Correct segment assignment (documented thresholds)
    - Valid segment labels (subset of the approved segment set)
    - Deterministic repeated execution
    - Identical RFM scores -> identical segment
    - Missing required columns
    - Missing CustomerID
    - Missing RFM score columns
    - Invalid / non-numeric scores
    - Empty input
    - Single customer
    - Multiple customers
    - Segment summary
    - Compatibility with the Phase 7 RFM output
    - Real-data execution (Phase 5 -> Phase 7 -> Phase 8)
"""

import unittest

import pandas as pd

from src.rfm_analysis import build_rfm_analysis
from src.segmentation import (
    SEGMENT_NAMES,
    assign_customer_segments,
    build_segmentation,
    summarize_segments,
)

SCORE_COLUMNS = ["recency_score", "frequency_score", "monetary_score"]


def _scored_fixture():
    """Five customers with distinct RFM score combinations.

    Combined totals:
        c1: 5+5+5 = 15 -> Champions
        c2: 5+4+3 = 12 -> Loyal Customers
        c3: 4+5+5 = 14 -> Champions
        c4: 4+2+1 = 7  -> Average Customers
        c5: 3+1+1 = 5  -> At-Risk Customers
    """
    return pd.DataFrame(
        {
            "CustomerID": ["c1", "c2", "c3", "c4", "c5"],
            "recency_score": [5, 5, 4, 4, 3],
            "frequency_score": [5, 4, 5, 2, 1],
            "monetary_score": [5, 3, 5, 1, 1],
        }
    )


class TestValidInput(unittest.TestCase):
    def test_valid_scored_input_returns_segmented_table(self):
        segmented = assign_customer_segments(_scored_fixture())
        self.assertIsInstance(segmented, pd.DataFrame)
        self.assertEqual(len(segmented), 5)
        self.assertEqual(len(segmented["CustomerID"].unique()), 5)
        self.assertTrue(segmented["segment"].notna().all())

    def test_segment_column_created(self):
        segmented = assign_customer_segments(_scored_fixture())
        self.assertIn("segment", segmented.columns)

    def test_input_table_not_modified(self):
        source = _scored_fixture()
        before = source.copy()
        assign_customer_segments(source)
        pd.testing.assert_frame_equal(source, before)


class TestSegmentAssignment(unittest.TestCase):
    def test_correct_segment_assignment(self):
        segmented = assign_customer_segments(_scored_fixture())
        expected = {
            "c1": "Champions",
            "c2": "Loyal Customers",
            "c3": "Champions",
            "c4": "Average Customers",
            "c5": "At-Risk Customers",
        }
        actual = segmented.set_index("CustomerID")["segment"].to_dict()
        self.assertEqual(actual, expected)

    def test_valid_segment_labels(self):
        segmented = assign_customer_segments(_scored_fixture())
        self.assertTrue(set(segmented["segment"]).issubset(set(SEGMENT_NAMES)))

    def test_every_customer_gets_exactly_one_segment(self):
        segmented = assign_customer_segments(_scored_fixture())
        self.assertEqual(segmented["CustomerID"].is_unique, True)
        self.assertEqual(segmented["segment"].isna().sum(), 0)


class TestDeterminismAndTies(unittest.TestCase):
    def test_repeated_execution_is_identical(self):
        s1 = assign_customer_segments(_scored_fixture())
        s2 = assign_customer_segments(_scored_fixture())
        self.assertTrue(s1.equals(s2))

    def test_identical_scores_get_identical_segment(self):
        df = pd.DataFrame(
            {
                "CustomerID": ["a", "b", "c", "d"],
                "recency_score": [5, 5, 1, 1],
                "frequency_score": [5, 5, 1, 1],
                "monetary_score": [5, 5, 1, 1],
            }
        )
        segmented = assign_customer_segments(df)
        self.assertEqual(
            segmented.loc[segmented["CustomerID"] == "a", "segment"].iloc[0],
            segmented.loc[segmented["CustomerID"] == "b", "segment"].iloc[0],
        )
        self.assertEqual(
            segmented.loc[segmented["CustomerID"] == "c", "segment"].iloc[0],
            segmented.loc[segmented["CustomerID"] == "d", "segment"].iloc[0],
        )
        self.assertEqual(
            segmented.loc[segmented["CustomerID"] == "a", "segment"].iloc[0], "Champions"
        )
        self.assertEqual(
            segmented.loc[segmented["CustomerID"] == "c", "segment"].iloc[0], "Lost Customers"
        )


class TestValidationErrors(unittest.TestCase):
    def test_missing_required_score_column_raises(self):
        df = _scored_fixture().drop(columns=["monetary_score"])
        with self.assertRaises(ValueError):
            assign_customer_segments(df)

    def test_missing_customer_id_raises(self):
        df = _scored_fixture().drop(columns=["CustomerID"])
        with self.assertRaises(ValueError):
            assign_customer_segments(df)

    def test_non_numeric_scores_raise(self):
        df = _scored_fixture().copy()
        df["recency_score"] = df["recency_score"].astype(str)
        with self.assertRaises(ValueError):
            assign_customer_segments(df)

    def test_empty_input_raises(self):
        df = _scored_fixture().iloc[0:0]
        with self.assertRaises(ValueError):
            assign_customer_segments(df)

    def test_none_input_raises(self):
        with self.assertRaises(ValueError):
            assign_customer_segments(None)


class TestEdgeCases(unittest.TestCase):
    def test_single_customer(self):
        df = pd.DataFrame(
            {
                "CustomerID": ["only"],
                "recency_score": [5],
                "frequency_score": [5],
                "monetary_score": [5],
            }
        )
        segmented = assign_customer_segments(df)
        self.assertEqual(len(segmented), 1)
        self.assertEqual(segmented["segment"].iloc[0], "Champions")

    def test_multiple_customers_preserved(self):
        df = _scored_fixture()
        segmented = assign_customer_segments(df)
        self.assertEqual(len(segmented), len(df))

    def test_segment_summary_counts(self):
        segmented = assign_customer_segments(_scored_fixture())
        summary = summarize_segments(segmented)
        self.assertEqual(summary["Champions"], 2)
        self.assertEqual(summary["Loyal Customers"], 1)
        self.assertEqual(summary["Average Customers"], 1)
        self.assertEqual(summary["At-Risk Customers"], 1)
        self.assertEqual(summary["Lost Customers"], 0)
        self.assertEqual(sum(summary.values()), len(segmented))


class TestPhase7Compatibility(unittest.TestCase):
    def test_consumes_real_phase7_output(self):
        rfm_result = build_rfm_analysis()
        scored = rfm_result["rfm_table"]
        for column in SCORE_COLUMNS + ["CustomerID"]:
            self.assertIn(column, scored.columns)
        segmented = assign_customer_segments(scored)
        self.assertEqual(len(segmented), len(scored))
        self.assertIn("segment", segmented.columns)

    def test_build_segmentation_structure(self):
        result = build_segmentation()
        for key in ("dataset", "rfm_table", "segmented_table", "segment_summary"):
            self.assertIn(key, result)
        self.assertEqual(len(result["segmented_table"]), len(result["rfm_table"]))


class TestRealDataExecution(unittest.TestCase):
    def test_real_data_every_customer_one_segment(self):
        result = build_segmentation()
        segmented = result["segmented_table"]
        customer_count = len(segmented)
        self.assertGreater(customer_count, 1000)
        self.assertEqual(segmented["CustomerID"].is_unique, True)
        self.assertEqual(segmented["segment"].isna().sum(), 0)
        self.assertEqual(len(segmented), len(result["rfm_table"]))
        self.assertEqual(sum(result["segment_summary"].values()), customer_count)
        # Every approved segment is represented in the real data (no empty bucket).
        self.assertEqual(
            sum(1 for v in result["segment_summary"].values() if v > 0), len(SEGMENT_NAMES)
        )


if __name__ == "__main__":
    unittest.main()