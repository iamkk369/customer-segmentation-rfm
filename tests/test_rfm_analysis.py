"""
tests/test_rfm_analysis.py - Phase 7: RFM Calculation tests.

Internal unit-style tests (Python built-in unittest only, consistent with the
project dependency policy - pytest is NOT an approved dependency).

Coverage:
    - Real project dataset loading and schema
    - Customer-level aggregation (one row per CustomerID)
    - Recency (last purchase vs reference date)
    - Frequency (DISTINCT InvoiceNo per customer)
    - Monetary = sum(Quantity * UnitPrice)
    - Default and explicit reference dates
    - R / F / M scoring directions (1..5)
    - Score range 1..5
    - Tie rule: identical raw values receive identical scores
    - Deterministic repeated execution
    - Empty / missing-column / missing-InvoiceNo error handling
    - Single customer and multiple-transaction fixtures
    - Real-data count / output sanity

Phase 12.3 dedicated additions:
    - Analysis-date handling across multiple customers (explicit + default)
    - Independent per-customer recomputation of last_purchase / recency /
      frequency / monetary from source transaction rows on real data
    - Input non-mutation
    - RFM table numeric/type integrity and value validity on real data
    - Independent cross-check of the documented Phase 7 scoring rule
      (pure-Python reimplementation of the approved tie-safe rank rule)
    - Score/metric monotonic consistency on real data
    - summarize_rfm_for_reporting agreement with the underlying table
"""

import unittest

import pandas as pd

from src.rfm_analysis import (
    build_rfm_analysis,
    calculate_customer_rfm,
    load_phase7_dataset,
    score_rfm_table,
    summarize_rfm_for_reporting,
)

# Real project working dataset (Phase 5 output used by Phase 7).
REAL_EXPECTED_ROWS = 524878
REAL_EXPECTED_CUSTOMERS = 4338
REAL_EXPECTED_TOTAL_REVENUE = 10642110.80

EXPECTED_RFM_COLUMNS = ["CustomerID", "last_purchase", "recency_days", "frequency", "monetary"]
SCORE_COLUMNS = ["recency_score", "frequency_score", "monetary_score"]


def _scoring_fixture():
    """Five customers with distinct recency / frequency / monetary values.

    - c1: last purchase 2011-12-05, 1 invoice, monetary 10
    - c2: last purchase 2011-11-05, 2 invoices, monetary 40
    - c3: last purchase 2011-10-05, 3 invoices, monetary 90
    - c4: last purchase 2011-09-05, 4 invoices, monetary 160
    - c5: last purchase 2011-08-05, 5 invoices, monetary 250

    Default reference date = max InvoiceDate = 2011-12-05.
    Recency (days): c1=0, c2=30, c3=61, c4=91, c5=122.
    """
    spec = [
        ("c1", ["A1"], "2011-12-05", 10.0),
        ("c2", ["B1", "B2"], "2011-11-05", 20.0),
        ("c3", ["C1", "C2", "C3"], "2011-10-05", 30.0),
        ("c4", ["D1", "D2", "D3", "D4"], "2011-09-05", 40.0),
        ("c5", ["E1", "E2", "E3", "E4", "E5"], "2011-08-05", 50.0),
    ]
    rows = []
    for cid, invoices, date, price in spec:
        for inv in invoices:
            rows.append(
                {
                    "CustomerID": cid,
                    "InvoiceDate": pd.Timestamp(date),
                    "Quantity": 1,
                    "UnitPrice": price,
                    "InvoiceNo": inv,
                }
            )
    return pd.DataFrame(rows)


class TestDatasetLoading(unittest.TestCase):
    def test_real_dataset_loads_with_expected_shape(self):
        df = load_phase7_dataset()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (REAL_EXPECTED_ROWS, 8))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]))

    def test_real_dataset_has_approved_columns(self):
        df = load_phase7_dataset()
        expected = {
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "CustomerID",
            "Country",
        }
        self.assertEqual(set(df.columns), expected)


class TestCustomerAggregation(unittest.TestCase):
    def test_one_row_per_customer_with_expected_columns(self):
        rfm = calculate_customer_rfm()
        self.assertEqual(len(rfm), REAL_EXPECTED_CUSTOMERS)
        self.assertEqual(list(rfm.columns), EXPECTED_RFM_COLUMNS)
        self.assertEqual(int(rfm["CustomerID"].nunique()), REAL_EXPECTED_CUSTOMERS)


class TestFrequencyCalculation(unittest.TestCase):
    def test_repeated_invoice_counts_once(self):
        # 3 rows but only 2 DISTINCT invoices -> frequency = 2.
        df = pd.DataFrame(
            {
                "CustomerID": [10, 10, 10],
                "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-01-01", "2011-01-02"]),
                "Quantity": [1, 2, 3],
                "UnitPrice": [1.0, 1.0, 1.0],
                "InvoiceNo": ["X", "X", "Y"],
            }
        )
        rfm = calculate_customer_rfm(df)
        self.assertEqual(int(rfm.at[0, "frequency"]), 2)

    def test_single_invoice_on_multiple_rows_is_one_order(self):
        df = pd.DataFrame(
            {
                "CustomerID": [20, 20, 20],
                "InvoiceDate": pd.to_datetime(["2011-01-01"] * 3),
                "Quantity": [1, 1, 1],
                "UnitPrice": [1.0, 1.0, 1.0],
                "InvoiceNo": ["X", "X", "X"],
            }
        )
        rfm = calculate_customer_rfm(df)
        self.assertEqual(int(rfm.at[0, "frequency"]), 1)


class TestMonetaryCalculation(unittest.TestCase):
    def test_monetary_is_sum_of_quantity_times_unitprice(self):
        df = pd.DataFrame(
            {
                "CustomerID": [1, 1, 1],
                "InvoiceDate": pd.to_datetime(["2011-01-01"] * 3),
                "Quantity": [2, 3, 5],
                "UnitPrice": [10.0, 20.0, 30.0],
                "InvoiceNo": ["A", "B", "C"],
            }
        )
        rfm = calculate_customer_rfm(df)
        # 2*10 + 3*20 + 5*30 = 230
        self.assertAlmostEqual(rfm.at[0, "monetary"], 230.0, places=6)

    def test_customer_monetary_sums_to_total_revenue(self):
        df = load_phase7_dataset()
        rfm = calculate_customer_rfm(df)
        total_revenue = float((df["Quantity"] * df["UnitPrice"]).sum())
        self.assertAlmostEqual(float(rfm["monetary"].sum()), total_revenue, places=2)


class TestRecencyCalculation(unittest.TestCase):
    def test_default_reference_date_is_max_invoicedate(self):
        df = pd.DataFrame(
            {
                "CustomerID": [1, 1],
                "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-06-15"]),
                "Quantity": [1, 1],
                "UnitPrice": [1.0, 1.0],
                "InvoiceNo": ["A", "B"],
            }
        )
        rfm = calculate_customer_rfm(df)
        # reference = max InvoiceDate = 2011-06-15; last purchase = 2011-06-15
        self.assertEqual(int(rfm.at[0, "recency_days"]), 0)

    def test_explicit_reference_date(self):
        df = pd.DataFrame(
            {
                "CustomerID": [1],
                "InvoiceDate": pd.to_datetime(["2011-06-15"]),
                "Quantity": [1],
                "UnitPrice": [1.0],
                "InvoiceNo": ["A"],
            }
        )
        rfm = calculate_customer_rfm(df, reference_date="2011-12-15")
        self.assertEqual(int(rfm.at[0, "recency_days"]), 183)


class TestScoringSingleton(unittest.TestCase):
    def test_single_customer_scores_valid(self):
        df = pd.DataFrame(
            {
                "CustomerID": [1],
                "InvoiceDate": pd.to_datetime(["2011-06-15"]),
                "Quantity": [2],
                "UnitPrice": [5.0],
                "InvoiceNo": ["A"],
            }
        )
        rfm = calculate_customer_rfm(df)
        scored = score_rfm_table(rfm)
        for col in SCORE_COLUMNS:
            self.assertTrue(1 <= int(scored.at[0, col]) <= 5)


class TestScoringDirections(unittest.TestCase):
    def setUp(self):
        rfm = calculate_customer_rfm(_scoring_fixture())
        self.scored = score_rfm_table(rfm).set_index("CustomerID")

    def test_recency_direction(self):
        # Lower recency_days (more recent) => higher score.
        self.assertEqual(int(self.scored.at["c1", "recency_score"]), 5)
        self.assertEqual(int(self.scored.at["c5", "recency_score"]), 1)
        self.assertGreater(
            self.scored.at["c1", "recency_score"],
            self.scored.at["c5", "recency_score"],
        )

    def test_frequency_direction(self):
        # Higher frequency => higher score.
        self.assertEqual(int(self.scored.at["c5", "frequency_score"]), 5)
        self.assertEqual(int(self.scored.at["c1", "frequency_score"]), 1)

    def test_monetary_direction(self):
        # Higher monetary => higher score.
        self.assertEqual(int(self.scored.at["c5", "monetary_score"]), 5)
        self.assertEqual(int(self.scored.at["c1", "monetary_score"]), 1)

    def test_score_range_is_1_to_5(self):
        for col in SCORE_COLUMNS:
            self.assertGreaterEqual(self.scored[col].min(), 1)
            self.assertLessEqual(self.scored[col].max(), 5)


class TestTieHandling(unittest.TestCase):
    def test_identical_frequency_values_get_identical_scores(self):
        df = pd.DataFrame(
            {
                "CustomerID": [1, 2, 3, 4],
                "InvoiceDate": pd.to_datetime(
                    ["2011-01-01", "2011-01-01", "2011-01-02", "2011-01-02"]
                ),
                "Quantity": [1, 1, 2, 2],
                "UnitPrice": [1.0, 1.0, 1.0, 1.0],
                "InvoiceNo": ["A", "A", "B", "B"],
            }
        )
        rfm = calculate_customer_rfm(df)
        scored = score_rfm_table(rfm)
        # All four customers have frequency == 1.
        self.assertEqual(set(scored["frequency"].astype(int)), {1})
        self.assertEqual(scored["frequency_score"].nunique(), 1)

    def test_all_equal_values_receive_single_score(self):
        df = pd.DataFrame(
            {
                "CustomerID": [1, 2, 3, 4, 5],
                "InvoiceDate": pd.to_datetime(["2011-01-01"] * 5),
                "Quantity": [1] * 5,
                "UnitPrice": [1.0] * 5,
                "InvoiceNo": ["A", "B", "C", "D", "E"],
            }
        )
        scored = score_rfm_table(calculate_customer_rfm(df))
        for col in SCORE_COLUMNS:
            self.assertEqual(scored[col].nunique(), 1)

    def test_real_data_ties_preserved(self):
        scored = score_rfm_table(calculate_customer_rfm())
        for metric, scorecol in [
            ("recency_days", "recency_score"),
            ("frequency", "frequency_score"),
            ("monetary", "monetary_score"),
        ]:
            max_unique = scored.groupby(metric)[scorecol].nunique().max()
            self.assertEqual(max_unique, 1)


class TestDeterminism(unittest.TestCase):
    def test_repeated_execution_is_identical(self):
        df = load_phase7_dataset()
        rfm1 = score_rfm_table(calculate_customer_rfm(df))
        rfm2 = score_rfm_table(calculate_customer_rfm(df))
        self.assertTrue(rfm1.equals(rfm2))

    def test_real_data_scoring_deterministic(self):
        s1 = score_rfm_table(calculate_customer_rfm())
        s2 = score_rfm_table(calculate_customer_rfm())
        self.assertTrue(s1[SCORE_COLUMNS].equals(s2[SCORE_COLUMNS]))


class TestRecencyDefaultReference(unittest.TestCase):
    def test_default_reference_date_is_max_invoicedate(self):
        df = pd.DataFrame(
            {
                "CustomerID": [1, 1],
                "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-06-15"]),
                "Quantity": [1, 1],
                "UnitPrice": [1.0, 1.0],
                "InvoiceNo": ["A", "B"],
            }
        )
        rfm = calculate_customer_rfm(df)
        # reference = max InvoiceDate = 2011-06-15; last purchase = 2011-06-15
        self.assertEqual(int(rfm.at[0, "recency_days"]), 0)

    def test_explicit_reference_date(self):
        df = pd.DataFrame(
            {
                "CustomerID": [1],
                "InvoiceDate": pd.to_datetime(["2011-06-15"]),
                "Quantity": [1],
                "UnitPrice": [1.0],
                "InvoiceNo": ["A"],
            }
        )
        rfm = calculate_customer_rfm(df, reference_date="2011-12-15")
        self.assertEqual(int(rfm.at[0, "recency_days"]), 183)


# ==========================================================================
# PHASE 12.3 — RFM CALCULATION TESTING (dedicated validation)
# ==========================================================================

def _independent_score(values, higher_is_better=True):
    """Pure-Python reimplementation of the DOCUMENTED Phase 7 scoring rule.

    Rule (per src/rfm_analysis.py docstring):
        below     = count of values strictly less than v
        inclusive = count of values up-to-and-including v
        position  = (below + inclusive) / (2 * n)
        score     = int(position * 5) + 1, clipped to [1, 5]
        Recency is reversed (6 - score) because lower days is better.
    Used ONLY as an independent cross-check — no alternative scoring rule.
    """
    vals = [float(v) for v in values]
    n = len(vals)
    scores = []
    for v in vals:
        below = sum(1 for x in vals if x < v)
        inclusive = sum(1 for x in vals if x <= v)
        position = (below + inclusive) / (2.0 * n)
        s = int(position * 5.0) + 1
        s = max(1, min(5, s))
        scores.append(6 - s if not higher_is_better else s)
    return scores


def _multi_customer_recency_fixture():
    """Three customers with different latest purchases; explicit analysis date."""
    rows = [
        # cust A: two invoices, latest 2011-03-10
        {"CustomerID": "A", "InvoiceDate": pd.Timestamp("2011-02-01"), "Quantity": 2,
         "UnitPrice": 5.0, "InvoiceNo": "A1"},
        {"CustomerID": "A", "InvoiceDate": pd.Timestamp("2011-03-10"), "Quantity": 1,
         "UnitPrice": 7.0, "InvoiceNo": "A2"},
        # cust B: single invoice 2011-01-15
        {"CustomerID": "B", "InvoiceDate": pd.Timestamp("2011-01-15"), "Quantity": 4,
         "UnitPrice": 3.0, "InvoiceNo": "B1"},
        # cust C: three rows across two invoices, latest 2011-05-20
        {"CustomerID": "C", "InvoiceDate": pd.Timestamp("2011-04-02"), "Quantity": 1,
         "UnitPrice": 9.0, "InvoiceNo": "C1"},
        {"CustomerID": "C", "InvoiceDate": pd.Timestamp("2011-05-20"), "Quantity": 2,
         "UnitPrice": 6.0, "InvoiceNo": "C2"},
        {"CustomerID": "C", "InvoiceDate": pd.Timestamp("2011-05-20"), "Quantity": 1,
         "UnitPrice": 8.0, "InvoiceNo": "C3"},
    ]
    return pd.DataFrame(rows)


class TestPhase123AnalysisDate(unittest.TestCase):
    """A. Analysis date: correct use, determinism, multi-customer recency."""

    def test_build_rfm_returns_reference_date_equal_to_dataset_max(self):
        df = load_phase7_dataset()
        result = build_rfm_analysis(df)
        self.assertEqual(pd.Timestamp(result["reference_date"]), df["InvoiceDate"].max())

    def test_explicit_analysis_date_drives_every_customers_recency(self):
        df = _multi_customer_recency_fixture()
        reference = pd.Timestamp("2011-06-10")
        rfm = calculate_customer_rfm(df, reference_date=reference).set_index("CustomerID")
        expected_last = {"A": pd.Timestamp("2011-03-10"),
                         "B": pd.Timestamp("2011-01-15"),
                         "C": pd.Timestamp("2011-05-20")}
        for cid, last in expected_last.items():
            self.assertEqual(pd.Timestamp(rfm.at[cid, "last_purchase"]), last)
            self.assertEqual(
                int(rfm.at[cid, "recency_days"]),
                int((reference - last).days),
                f"Recency for {cid} must equal analysis date minus its own last purchase.",
            )

    def test_default_reference_is_latest_transaction_in_dataset(self):
        df = _multi_customer_recency_fixture()
        rfm = calculate_customer_rfm(df).set_index("CustomerID")
        latest = df["InvoiceDate"].max()  # 2011-05-20
        self.assertEqual(
            int(rfm.at["C", "recency_days"]), int((latest - pd.Timestamp("2011-05-20")).days)
        )
        self.assertEqual(
            int(rfm.at["B", "recency_days"]), int((latest - pd.Timestamp("2011-01-15")).days)
        )

    def test_deterministic_with_fixed_reference_date(self):
        df = _multi_customer_recency_fixture()
        r1 = calculate_customer_rfm(df, reference_date="2011-06-10")
        r2 = calculate_customer_rfm(df, reference_date="2011-06-10")
        self.assertTrue(r1.equals(r2))


class TestPhase123IndependentRecalculation(unittest.TestCase):
    """B/C/D: per-customer values independently recomputed from real rows."""

    @classmethod
    def setUpClass(cls):
        cls.df = load_phase7_dataset()
        cls.rfm = calculate_customer_rfm(cls.df).set_index("CustomerID")

    def test_last_purchase_matches_independent_groupby_max(self):
        expected = self.df.groupby("CustomerID")["InvoiceDate"].max().sort_index()
        actual = self.rfm.sort_index()["last_purchase"]
        self.assertTrue(expected.equals(actual))

    def test_recency_matches_independent_computation(self):
        reference = self.df["InvoiceDate"].max()
        last_purchase = self.df.groupby("CustomerID")["InvoiceDate"].max().sort_index()
        expected = (reference - last_purchase).dt.days
        actual = self.rfm.sort_index()["recency_days"]
        self.assertTrue(expected.equals(actual))

    def test_frequency_matches_distinct_invoice_count_per_customer(self):
        expected = (
            self.df.groupby("CustomerID")["InvoiceNo"].nunique().sort_index().astype(float)
        )
        actual = self.rfm.sort_index()["frequency"].astype(float)
        self.assertTrue(expected.equals(actual))

    def test_monetary_matches_independent_row_level_sum_per_customer(self):
        revenue = self.df["Quantity"] * self.df["UnitPrice"]
        expected = revenue.groupby(self.df["CustomerID"]).sum().sort_index()
        actual = self.rfm.sort_index()["monetary"].sort_index()
        pd.testing.assert_series_equal(
            expected.rename("monetary"), actual, check_names=False, rtol=1e-9
        )

    def test_total_monetary_equals_total_transaction_revenue(self):
        total_revenue = float((self.df["Quantity"] * self.df["UnitPrice"]).sum())
        self.assertAlmostEqual(total_revenue, float(self.rfm["monetary"].sum()), places=2)


class TestPhase123TableIntegrity(unittest.TestCase):
    """E. RFM table structure, identity preservation, non-mutation."""

    @classmethod
    def setUpClass(cls):
        cls.df = load_phase7_dataset()
        cls.rfm = calculate_customer_rfm(cls.df)

    def test_customer_identity_preserved_real_data(self):
        self.assertEqual(len(self.rfm), REAL_EXPECTED_CUSTOMERS)
        self.assertEqual(set(self.rfm["CustomerID"]), set(self.df["CustomerID"].unique()))
        self.assertFalse(self.rfm["CustomerID"].duplicated().any())

    def test_required_rfm_columns_have_no_missing_values(self):
        for col in EXPECTED_RFM_COLUMNS:
            self.assertEqual(int(self.rfm[col].isna().sum()), 0, col)

    def test_numeric_columns_and_valid_ranges_real_data(self):
        self.assertTrue(pd.api.types.is_numeric_dtype(self.rfm["recency_days"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(self.rfm["frequency"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(self.rfm["monetary"]))
        self.assertGreaterEqual(int(self.rfm["recency_days"].min()), 0)
        self.assertGreaterEqual(int(self.rfm["frequency"].min()), 1)
        self.assertGreater(float(self.rfm["monetary"].min()), 0.0)

    def test_input_dataframe_is_not_mutated(self):
        fixture = _multi_customer_recency_fixture()
        before_cols = list(fixture.columns)
        before_len = len(fixture)
        snapshot = fixture.copy(deep=True)
        calculate_customer_rfm(fixture)
        self.assertEqual(list(fixture.columns), before_cols)
        self.assertEqual(len(fixture), before_len)
        self.assertTrue(fixture.equals(snapshot))

    def test_scored_table_keeps_base_columns_and_adds_scores(self):
        scored = score_rfm_table(self.rfm.head(50))
        self.assertEqual(list(scored.columns), EXPECTED_RFM_COLUMNS + SCORE_COLUMNS)


class TestPhase123ScoreRuleConsistency(unittest.TestCase):
    """F. Scores consistent with the EXISTING documented Phase 7 rules."""

    def test_fixture_scores_match_independent_rule_implementation(self):
        scored = score_rfm_table(calculate_customer_rfm(_scoring_fixture()))
        rfm = calculate_customer_rfm(_scoring_fixture()).set_index("CustomerID")
        order = ["c1", "c2", "c3", "c4", "c5"]
        expected_r = _independent_score(rfm.loc[order, "recency_days"], higher_is_better=False)
        expected_f = _independent_score(rfm.loc[order, "frequency"])
        expected_m = _independent_score(rfm.loc[order, "monetary"])
        scored = scored.set_index("CustomerID")
        for idx, cid in enumerate(order):
            self.assertEqual(int(scored.at[cid, "recency_score"]), expected_r[idx])
            self.assertEqual(int(scored.at[cid, "frequency_score"]), expected_f[idx])
            self.assertEqual(int(scored.at[cid, "monetary_score"]), expected_m[idx])

    def test_real_data_score_metric_monotonic_non_decreasing(self):
        """Higher raw metric never yields a lower score (Phase 7 direction)."""
        df = load_phase7_dataset()
        scored = score_rfm_table(calculate_customer_rfm(df))
        pairs = [
            ("frequency", "frequency_score", True),
            ("monetary", "monetary_score", True),
            ("recency_days", "recency_score", False),  # reversed: more days -> lower score
        ]
        for metric, score_col, higher_better in pairs:
            grouped = scored.groupby(metric)[score_col].mean().sort_index()
            diffs = grouped.diff().dropna()
            if higher_better:
                self.assertGreaterEqual(float(diffs.min()), -1e-9, metric)
            else:
                self.assertLessEqual(float(diffs.max()), 1e-9, metric)


class TestPhase123ReportingConsistency(unittest.TestCase):
    """G. Reporting summary agrees with the independently built RFM table."""

    @classmethod
    def setUpClass(cls):
        cls.df = load_phase7_dataset()
        cls.rfm = calculate_customer_rfm(cls.df)
        cls.summary = summarize_rfm_for_reporting(cls.rfm)

    def test_summary_counts_match_table(self):
        self.assertEqual(self.summary["customer_count"], REAL_EXPECTED_CUSTOMERS)
        self.assertEqual(int(self.rfm["CustomerID"].nunique()), REAL_EXPECTED_CUSTOMERS)

    def test_summary_statistics_match_underlying_table(self):
        self.assertAlmostEqual(
            self.summary["avg_monetary"], float(self.rfm["monetary"].mean()), places=6
        )
        self.assertAlmostEqual(
            self.summary["median_monetary"], float(self.rfm["monetary"].median()), places=6
        )
        self.assertAlmostEqual(
            self.summary["avg_frequency"], float(self.rfm["frequency"].mean()), places=6
        )
        self.assertAlmostEqual(
            self.summary["avg_recency_days"], float(self.rfm["recency_days"].mean()), places=6
        )
        self.assertEqual(
            self.summary["min_recency_days"], int(self.rfm["recency_days"].min())
        )
        self.assertEqual(
            self.summary["max_recency_days"], int(self.rfm["recency_days"].max())
        )
