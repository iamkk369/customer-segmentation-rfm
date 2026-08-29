"""Phase 12.4 — Edge-Case Testing (dedicated validation).

Verifies that the EXISTING project implementation behaves correctly on
unusual, boundary, minimal, empty, or invalid inputs. Every expected
behavior below is taken from the actual implementation / documented
contracts (verified by direct probing before these tests were written):

- ``calculate_customer_rfm`` raises ``ValueError`` listing the SORTED
  missing required columns, and rejects an empty transaction dataset.
- ``score_rfm_table`` / ``summarize_rfm_for_reporting`` raise
  ``ValueError`` for None / empty RFM tables.
- RFM scoring uses the documented tie-safe rank rule; a single-row table
  yields the midpoint score 3 for every metric (no ordering information),
  and n-row distinct values follow position=(below+inclusive)/(2n).
- ``assign_customer_segments`` accepts the smallest valid scored table
  (one customer) and always returns an APPROVED segment name.
- ``summarize_segments`` counts ONLY the five approved segment names;
  unknown labels are excluded from the approved-name summary.
- Identical R/F/M values across customers receive identical scores
  (tie handling) on minimal tables.

No project methodology, rule, dataset, dependency or source file is
modified by this subphase; fixtures are small in-memory DataFrames.
"""

import unittest

import pandas as pd

from src.rfm_analysis import calculate_customer_rfm, score_rfm_table
from src.rfm_analysis import summarize_rfm_for_reporting
from src.segmentation import SEGMENT_NAMES, assign_customer_segments
from src.segmentation import summarize_segments


def _valid_transaction_frame(rows):
    """Build a minimal valid Phase 7 transaction frame."""
    return pd.DataFrame(
        {
            "CustomerID": [r[0] for r in rows],
            "InvoiceDate": pd.to_datetime([r[1] for r in rows]),
            "Quantity": [r[2] for r in rows],
            "UnitPrice": [r[3] for r in rows],
            "InvoiceNo": [r[4] for r in rows],
        }
    )


class TestPhase124RFMValidation(unittest.TestCase):
    """A/C. Documented Phase 7 raise paths on empty/invalid inputs."""

    def _full_columns(self):
        return ["CustomerID", "InvoiceDate", "Quantity", "UnitPrice", "InvoiceNo"]

    def test_missing_single_required_column_raises_with_name(self):
        df = _valid_transaction_frame([("A", "2011-06-15", 2, 5.0, "X1")])
        df = df.drop(columns=["InvoiceNo"])
        with self.assertRaises(ValueError) as ctx:
            calculate_customer_rfm(df)
        self.assertIn("InvoiceNo", str(ctx.exception))

    def test_missing_multiple_columns_reported_sorted(self):
        df = pd.DataFrame({"CustomerID": ["A"]})
        with self.assertRaises(ValueError) as ctx:
            calculate_customer_rfm(df)
        message = str(ctx.exception)
        self.assertIn("required columns", message)
        # Sorted order, as implemented: InvoiceNo < Quantity < UnitPrice.
        self.assertLess(message.index("InvoiceNo"), message.index("Quantity"))
        self.assertLess(message.index("Quantity"), message.index("UnitPrice"))

    def test_empty_transaction_dataset_raises(self):
        df = pd.DataFrame(columns=self._full_columns())
        with self.assertRaises(ValueError):
            calculate_customer_rfm(df)

    def test_score_rfm_table_rejects_none_and_empty(self):
        for bad in (None, pd.DataFrame()):
            with self.subTest(bad=type(bad).__name__):
                with self.assertRaises(ValueError) as ctx:
                    score_rfm_table(bad)
                self.assertIn("non-empty", str(ctx.exception))

    def test_summarize_rejects_none_and_empty(self):
        for bad in (None, pd.DataFrame()):
            with self.subTest(bad=type(bad).__name__):
                with self.assertRaises(ValueError) as ctx:
                    summarize_rfm_for_reporting(bad)
                self.assertIn("non-empty", str(ctx.exception))


class TestPhase124RFMBoundaries(unittest.TestCase):
    """E/F. Minimal tables, boundary scores and tie behaviour."""

    def test_single_row_scores_are_midpoint_three(self):
        """Smallest valid table: no ranking info -> documented midpoint 3."""
        df = _valid_transaction_frame([("A", "2011-06-15", 2, 5.0, "X1")])
        scored = score_rfm_table(calculate_customer_rfm(df))
        self.assertEqual(len(scored), 1)
        for column in ("recency_score", "frequency_score", "monetary_score"):
            value = int(scored.at[0, column])
            self.assertEqual(value, 3, f"{column} on a one-row table must be 3")
            self.assertTrue(1 <= value <= 5)

    def test_two_distinct_customers_follow_position_rule(self):
        """n=2 boundary: position=(below+inclusive)/(2n) -> no extreme 1/5."""
        df = _valid_transaction_frame(
            [
                ("A", "2011-06-15", 10, 9.0, "X1"),
                ("B", "2011-01-01", 1, 1.0, "Y1"),
            ]
        )
        scored = score_rfm_table(calculate_customer_rfm(df)).set_index("CustomerID")
        # A: newer (recency 0 days) and higher spend than B.
        self.assertEqual(int(scored.at["B", "recency_days"]), 165)
        self.assertEqual(int(scored.at["A", "recency_score"]), 4)
        self.assertEqual(int(scored.at["B", "recency_score"]), 2)
        self.assertEqual(int(scored.at["A", "monetary_score"]), 4)
        self.assertEqual(int(scored.at["B", "monetary_score"]), 2)
        # Frequency ties (one invoice each) -> identical shared score.
        self.assertEqual(int(scored.at["A", "frequency_score"]), 3)
        self.assertEqual(int(scored.at["B", "frequency_score"]), 3)

    def test_identical_values_receive_identical_boundary_scores(self):
        """All-equal metric -> every customer gets the same score."""
        rows = [("C%d" % i, "2011-03-03", 5, 2.0, "I%d" % i) for i in range(6)]
        scored = score_rfm_table(calculate_customer_rfm(_valid_transaction_frame(rows)))
        self.assertEqual(scored["recency_days"].unique().tolist(), [0])
        for column in ("recency_score", "frequency_score", "monetary_score"):
            self.assertEqual(sorted(scored[column].unique().tolist()), [3])

    def test_minimal_scoring_deterministic(self):
        df = _valid_transaction_frame(
            [
                ("A", "2011-06-15", 10, 9.0, "X1"),
                ("B", "2011-01-01", 1, 1.0, "Y1"),
            ]
        )
        s1 = score_rfm_table(calculate_customer_rfm(df))
        s2 = score_rfm_table(calculate_customer_rfm(df))
        self.assertTrue(s1.equals(s2))


class TestPhase124SegmentationMinimalEdges(unittest.TestCase):
    """D/G/H. Smallest valid segmentation input and label boundaries."""

    def test_one_customer_assigns_approved_segment(self):
        scored = pd.DataFrame(
            {
                "CustomerID": ["c1"],
                "recency_score": [5],
                "frequency_score": [5],
                "monetary_score": [5],
            }
        )
        segmented = assign_customer_segments(scored)
        self.assertEqual(len(segmented), 1)
        name = segmented["segment"].iloc[0]
        self.assertIn(name, SEGMENT_NAMES)

    def test_summary_counts_only_approved_names(self):
        scored = pd.DataFrame(
            {
                "CustomerID": ["c1", "zz"],
                "recency_score": [5, 1],
                "frequency_score": [5, 1],
                "monetary_score": [5, 1],
                "segment": ["Champions", "Not-A-Segment"],
            }
        )
        summary = summarize_segments(scored)
        self.assertEqual(sorted(summary.keys()), sorted(SEGMENT_NAMES))
        self.assertEqual(summary["Champions"], 1)
        for other in SEGMENT_NAMES:
            if other != "Champions":
                self.assertEqual(summary[other], 0)

    def test_summary_on_minimal_real_assignment_is_consistent(self):
        scored = pd.DataFrame(
            {
                "CustomerID": ["c1"],
                "recency_score": [5],
                "frequency_score": [5],
                "monetary_score": [5],
            }
        )
        segmented = assign_customer_segments(scored)
        summary = summarize_segments(segmented)
        self.assertEqual(sum(summary.values()), len(segmented))

    def test_all_identical_scores_land_in_one_segment(self):
        scored = pd.DataFrame(
            {
                "CustomerID": ["c%d" % i for i in range(8)],
                "recency_score": [2] * 8,
                "frequency_score": [2] * 8,
                "monetary_score": [2] * 8,
            }
        )
        segmented = assign_customer_segments(scored)
        self.assertEqual(len(segmented["segment"].unique()), 1)
        summary = summarize_segments(segmented)
        self.assertEqual(len([v for v in summary.values() if v > 0]), 1)
        self.assertEqual(sum(summary.values()), 8)


if __name__ == "__main__":
    unittest.main()
