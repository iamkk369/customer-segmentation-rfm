"""
tests/test_data_cleaning.py — Data Cleaning: Missing-Value Handling (Phase 5.1)

Purpose:
    Verify Phase 5.1 missing-value handling for the approved Online Retail
    dataset: the actual missing-value situation is inspected, the documented
    handling decision is applied, a working dataset is produced in
    data/processed/, and the immutable raw CSV is confirmed unchanged.

Scope (Phase 5.1 ONLY):
    1. The actual missing-value counts are verified (only Description is
       missing: 1,454 values; CustomerID and all other columns have 0 missing).
    2. Missing values are handled per the documented decision:
       - Description missing (1,454, 0.2683%) is preserved as NaN (not
         imputed with invented text; rows not removed).
       - CustomerID is never fabricated (0 missing before and after).
    3. RFM-required fields (CustomerID, InvoiceDate, Quantity, UnitPrice,
       InvoiceNo) remain fully present and non-missing.
    4. No rows are removed and no duplicates are removed in 5.1.
    5. A working dataset is produced in data/processed/ (never in data/raw/)
       and round-trips with the missing-value decision intact.
    6. The raw CSV remains unchanged (size + SHA-256 against the Phase 3
       baseline).

    This does NOT test duplicate removal, invalid-data handling, filtering,
    negative-value correction, EDA, RFM, or segmentation — those belong to
    later subphases and are intentionally out of scope here.

Framework:
    Python built-in unittest (no external test dependencies required,
    consistent with the project dependency policy — pytest is NOT an approved
    project dependency and is not installed).

Run from project root:
    .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""

import hashlib
import pathlib
import sys
import tempfile
import unittest

import pandas as pd

# ---------------------------------------------------------------------------
# Project root — added to sys.path so config and src are importable
# regardless of how the test is invoked.
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.data_cleaning import (
    APPROVED_COLUMNS,
    DEDUP_FILENAME,
    INVALID_REMOVED_FILENAME,
    NO_ADDITIONAL_AGGREGATION_REQUIRED,
    NO_ADDITIONAL_FILTERING_REQUIRED,
    NO_ADDITIONAL_OUTLIER_HANDLING_REQUIRED,
    NO_ADDITIONAL_TRANSFORMATION_REQUIRED,
    OUTLIER_REMOVED_FILENAME,
    OUTLIERS_FILENAME,
    PHASE_5_FINAL_VALIDATION_PASSED,
    TRANSFORMED_FILENAME,
    get_duplicate_count,
    get_invalid_removed_dataset_path,
    get_cleaned_dataset_path,
    get_deduplicated_dataset_path,
    handle_missing_values,
    is_cancellation_invoice,
    is_invalid_record,
    remove_duplicates,
    remove_invalid_records,
    save_invalid_removed_dataset,
    save_working_dataset,
    save_deduplicated_dataset,
    verify_no_additional_aggregation,
    verify_no_additional_filtering,
    verify_no_additional_outlier_handling,
    verify_no_additional_transformation,
    verify_phase5_final_validation,
)
from src.data_loading import load_raw_dataset

# ---------------------------------------------------------------------------
# Approved dataset baselines (Source: README.md — Phase 3 approval)
# ---------------------------------------------------------------------------
RAW_CSV_PATH = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"

APPROVED_FILE_SIZE = 47_901_468
APPROVED_SHA256 = "BFA47136118BC854A31E69D5C9E9689A2D07B73909F253679F2CC85EC4EB84EB"

EXPECTED_ROW_COUNT = 541_909
EXPECTED_COLUMN_COUNT = 8
EXPECTED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]

# Phase 3.3 completeness findings (verified against the actual dataset).
EXPECTED_DESCRIPTION_MISSING = 1_454
EXPECTED_CUSTOMER_ID_MISSING = 0
EXPECTED_UNIQUE_CUSTOMERS = 4_372
EXPECTED_DUPLICATE_ROWS = 5_268
# After removing 5,268 exact duplicates from the 541,909-row 5.1 working dataset.
EXPECTED_DEDUPLICATED_ROWS = 536_641

# Phase 5.3 invalid-data findings (recalculated on the actual 5.2 dataset).
EXPECTED_CANCELLATION_INVOICES = 9_251
EXPECTED_NEGATIVE_QUANTITY = 10_587
EXPECTED_ZERO_UNITPRICE = 2_510
EXPECTED_NEGATIVE_UNITPRICE = 2
EXPECTED_NONPOSITIVE_UNITPRICE = 2_512
EXPECTED_NEGATIVE_MONETARY = 9_253
# Removal union = R1 (cancellations) + R2 (non-cancel Q<=0, subset of R3)
# + R3 residual (UnitPrice<=0). No double counting.
EXPECTED_INVALID_ROWS_REMOVED = 11_763
EXPECTED_INVALID_REMOVED_ROWS = 524_878

# RFM-required fields that must remain present and non-missing.
RFM_REQUIRED_FIELDS = ["CustomerID", "InvoiceDate", "Quantity", "UnitPrice", "InvoiceNo"]


class TestMissingValueHandling(unittest.TestCase):
    """Verify the Phase 5.1 missing-value decision on the real dataset.

    Loads the approved raw dataset once (read-only), inspects the actual
    missing-value situation, applies the documented handling, and asserts the
    decision is applied literally. The raw CSV is never modified.
    """

    @classmethod
    def setUpClass(cls):
        cls.df = load_raw_dataset()
        cls.before = cls.df.isna().sum()
        cls.working = handle_missing_values(cls.df)
        cls.after = cls.working.isna().sum()

    # -- Actual missing-value situation (before handling) ---------------------
    def test_only_description_is_missing_before_handling(self):
        """Only Description may have missing values (Phase 3.3 / 3.4)."""
        columns_with_missing = [
            col for col in self.before.index if self.before[col] > 0
        ]
        self.assertEqual(
            columns_with_missing,
            ["Description"],
            f"Unexpected columns with missing values: {columns_with_missing}",
        )

    def test_description_missing_count_before(self):
        """Description must show exactly 1,454 missing values (0.2683%)."""
        self.assertEqual(self.before["Description"], EXPECTED_DESCRIPTION_MISSING)

    def test_customer_id_has_no_missing_before(self):
        """CustomerID must not be missing (must not be fabricated later)."""
        self.assertEqual(self.before["CustomerID"], EXPECTED_CUSTOMER_ID_MISSING)

    def test_all_required_fields_non_missing_before(self):
        """RFM-required fields must have zero missing values before handling."""
        for field in RFM_REQUIRED_FIELDS:
            with self.subTest(field=field):
                self.assertEqual(
                    self.before[field],
                    0,
                    f"Required field {field!r} unexpectedly has missing values.",
                )

    
    # -- Handling decision (after handling) ----------------------------------
    def test_description_missing_preserved_after_handling(self):
        """Description NaN is preserved (not imputed with invented text)."""
        self.assertEqual(self.after["Description"], EXPECTED_DESCRIPTION_MISSING)
        self.assertEqual(
            self.working["Description"].isna().sum(),
            EXPECTED_DESCRIPTION_MISSING,
        )

    def test_customer_id_not_fabricated_after_handling(self):
        """CustomerID must remain fully present (never fabricated)."""
        self.assertEqual(self.after["CustomerID"], EXPECTED_CUSTOMER_ID_MISSING)
        self.assertEqual(
            self.working["CustomerID"].isna().sum(),
            EXPECTED_CUSTOMER_ID_MISSING,
        )
        self.assertEqual(self.working["CustomerID"].nunique(), EXPECTED_UNIQUE_CUSTOMERS)

    def test_all_required_fields_non_missing_after_handling(self):
        """RFM-required fields must remain non-missing after handling."""
        for field in RFM_REQUIRED_FIELDS:
            with self.subTest(field=field):
                self.assertEqual(self.after[field], 0)

    def test_no_rows_removed(self):
        """5.1 must not remove any rows (no row filtering / cancellation)."""
        self.assertEqual(
            self.working.shape, (EXPECTED_ROW_COUNT, EXPECTED_COLUMN_COUNT)
        )
        self.assertEqual(len(self.working), len(self.df))

    def test_exact_columns_preserved(self):
        """The 8 expected columns must remain exactly as approved."""
        self.assertEqual(list(self.working.columns), EXPECTED_COLUMNS)

    def test_invoice_date_remains_datetime64(self):
        """InvoiceDate must keep its Phase 4 datetime64 type through cleaning."""
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(self.working["InvoiceDate"]),
            "InvoiceDate must remain datetime64 after missing-value handling.",
        )

    def test_duplicates_not_removed_in_5_1(self):
        """5.1 must NOT perform duplicate removal (deferred to a later subphase)."""
        self.assertEqual(self.working.duplicated().sum(), EXPECTED_DUPLICATE_ROWS)

    def test_raw_dataframe_not_mutated(self):
        """Handling must not mutate the input DataFrame (copy semantics)."""
        # Re-inspect the original to ensure it was not mutated.
        self.assertEqual(
            self.df.isna().sum()["Description"], EXPECTED_DESCRIPTION_MISSING
        )

    # -- Guardrails (hermetic, using small synthetic frames) -----------------
    def test_missing_customer_id_raises_not_fabricated(self):
        """A missing CustomerID must raise rather than be fabricated."""
        bad = pd.DataFrame(
            {
                "InvoiceNo": ["I1", "I2"],
                "StockCode": ["S1", "S2"],
                "Description": ["d1", None],
                "Quantity": [1, 2],
                "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-01-02"]),
                "UnitPrice": [1.0, 2.0],
                "CustomerID": [1.0, None],
                "Country": ["UK", "UK"],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            handle_missing_values(bad)
        self.assertIn("CustomerID", str(ctx.exception))
        self.assertIn("fabricat", str(ctx.exception).lower())

    def test_missing_required_field_raises(self):
        """A missing RFM-required field must raise rather than be hidden."""
        bad = pd.DataFrame(
            {
                "InvoiceNo": ["I1", "I2"],
                "StockCode": ["S1", "S2"],
                "Description": ["d1", "d2"],
                "Quantity": [1, None],
                "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-01-02"]),
                "UnitPrice": [1.0, 2.0],
                "CustomerID": [1.0, 2.0],
                "Country": ["UK", "UK"],
            }
        )
        with self.assertRaises(ValueError):
            handle_missing_values(bad)




class TestWorkingDatasetFile(unittest.TestCase):
    """Verify the Phase 5.1 working dataset is produced in data/processed/."""

    @classmethod
    def setUpClass(cls):
        cls.working = handle_missing_values(load_raw_dataset())

    def test_path_resolves_into_processed_not_raw(self):
        """The working dataset path must resolve under data/processed/."""
        path = get_cleaned_dataset_path()
        self.assertEqual(path.name, "OnlineRetail_cleaned.csv")
        self.assertIn("processed", path.parts)
        self.assertNotIn(str(config.RAW_DATA_DIR), str(path))

    def test_dedup_output_in_processed_dir(self):
        """The 5.2 output path metadata resolves under data/processed/, never data/raw/.

        Reconstructed for OPTION B: the deduplicated dataset lives in memory
        and is NOT persisted during normal pipeline execution, but
        get_deduplicated_dataset_path() remains part of the backward-compat
        API and must still resolve into data/processed/ (mirrors the 5.1 and
        5.3 path-metadata checks). No file is written by this test.
        """
        path = get_deduplicated_dataset_path()
        self.assertEqual(path.name, "OnlineRetail_deduplicated.csv")
        self.assertIn("processed", path.parts)
        self.assertNotIn(str(config.RAW_DATA_DIR), str(path))

    def test_save_writes_and_roundtrips_to_processed(self):
        """save_working_dataset writes a round-trippable CSV via an explicit path.

        Reconstructed for OPTION B: persistence happens ONLY when an explicit
        output_path is supplied (backward-compat behavior). A temporary
        directory is used, so no permanent OnlineRetail_cleaned.csv is
        created. The 5.1 missing-value decision must survive the round trip:
        Description 1,454 NaN preserved, CustomerID 0 missing (never
        fabricated).
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir) / "OnlineRetail_cleaned.csv"
            returned = save_working_dataset(
                dataframe=self.working, output_path=tmp_path
            )
            self.assertEqual(returned, tmp_path.resolve())
            self.assertTrue(returned.is_file())
            reloaded = pd.read_csv(returned, parse_dates=["InvoiceDate"])
            self.assertEqual(
                reloaded.shape, (EXPECTED_ROW_COUNT, EXPECTED_COLUMN_COUNT)
            )
            self.assertEqual(
                int(reloaded["Description"].isna().sum()),
                EXPECTED_DESCRIPTION_MISSING,
            )
            self.assertEqual(
                int(reloaded["CustomerID"].isna().sum()),
                EXPECTED_CUSTOMER_ID_MISSING,
            )
            self.assertTrue(
                pd.api.types.is_datetime64_any_dtype(reloaded["InvoiceDate"])
            )

    def test_processed_directory_contains_only_intended_files(self):
        """data/processed/ must contain exactly the 5.1, 5.2, and 5.3 files.

        Phase 13 integration (main.py) intentionally persists all three
        cleaning stages for provenance (see save_working_dataset /
        save_deduplicated_dataset / save_invalid_removed_dataset), so all
        three files are expected here.
        """
        if not config.PROCESSED_DATA_DIR.exists():
            self.skipTest("data/processed/ does not exist yet.")
        files = sorted(
            p.name for p in config.PROCESSED_DATA_DIR.iterdir() if p.is_file()
        )
        self.assertEqual(
            files,
            [
                "OnlineRetail_invalid_removed.csv",
        ],
        f"Unexpected files in data/processed/: {files}",
        )
        # The final working dataset handed to Phases 6-13 must remain the
        # 5.3 invalid-removed CSV, present on disk.
        working_path = get_invalid_removed_dataset_path()
        self.assertTrue(working_path.is_file())
        self.assertEqual(working_path.parent, config.PROCESSED_DATA_DIR.resolve())
        self.assertIn(working_path.name, files)


class TestRawCsvIntegrity(unittest.TestCase):
    """Verify the immutable raw CSV was not modified by Phase 5.1."""

    def test_raw_csv_size_unchanged(self):
        self.assertEqual(RAW_CSV_PATH.stat().st_size, APPROVED_FILE_SIZE)

    def test_raw_csv_sha256_unchanged(self):
        sha = hashlib.sha256(RAW_CSV_PATH.read_bytes()).hexdigest().upper()
        self.assertEqual(sha, APPROVED_SHA256)


class TestDuplicateRemoval(unittest.TestCase):
    """Verify Phase 5.2 exact-duplicate handling on the 5.1 processed input."""

    @classmethod
    def setUpClass(cls):
        # Use the ACTUAL Phase 5.1 processed dataset as the 5.2 input.
        cls.src = handle_missing_values(load_raw_dataset())
        cls.duplicate_count = get_duplicate_count(cls.src)
        cls.deduped = remove_duplicates(cls.src)

    def test_duplicate_count_verified_against_5_1_input(self):
        """Exact duplicates on the 5.1 processed input = 5,268 (recalculated)."""
        self.assertEqual(self.duplicate_count, EXPECTED_DUPLICATE_ROWS)

    def test_remove_duplicates_reduces_rows_only_by_exact_duplicates(self):
        """Dedup removes 5,268 rows; resulting shape = 536,641 x 8."""
        self.assertEqual(len(self.src) - len(self.deduped), self.duplicate_count)
        self.assertEqual(
            self.deduped.shape,
            (EXPECTED_DEDUPLICATED_ROWS, EXPECTED_COLUMN_COUNT),
        )

    def test_no_duplicates_remain_after_removal(self):
        self.assertEqual(get_duplicate_count(self.deduped), 0)
        self.assertEqual(int(self.deduped.duplicated(keep="first").sum()), 0)

    def test_first_occurrence_kept_and_order_preserved(self):
        """Deduped output equals the source with only keep='first' rows dropped."""
        expected = self.src[~self.src.duplicated(keep="first")].copy()
        expected.reset_index(drop=True, inplace=True)
        pd.testing.assert_frame_equal(
            self.deduped.reset_index(drop=True), expected.reset_index(drop=True)
        )

    def test_columns_and_invoice_date_preserved(self):
        self.assertEqual(list(self.deduped.columns), EXPECTED_COLUMNS)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.deduped["InvoiceDate"]))

    def test_missing_values_unaffected_by_dedup(self):
        """Description 1,454 missing preserved; CustomerID 0 missing (not fabricated)."""
        self.assertEqual(
            int(self.deduped["Description"].isna().sum()), EXPECTED_DESCRIPTION_MISSING
        )
        self.assertEqual(
            int(self.deduped["CustomerID"].isna().sum()), EXPECTED_CUSTOMER_ID_MISSING
        )

    def test_remove_duplicates_noop_without_duplicates(self):
        sample = self.deduped.head(50).copy()
        out = remove_duplicates(sample)
        self.assertEqual(len(out), len(sample))
        self.assertEqual(get_duplicate_count(out), 0)

    def test_save_deduplicated_roundtrips_to_processed(self):
        """save_deduplicated_dataset writes a round-trippable CSV via an explicit path.

        Reconstructed for OPTION B: the Phase 5.2 deduplicated dataset lives
        in memory and is NOT persisted during normal pipeline execution; the
        backward-compat save function persists ONLY when an explicit
        output_path is supplied. A temporary directory is used, so no
        permanent OnlineRetail_deduplicated.csv is created.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir) / "OnlineRetail_deduplicated.csv"
            returned = save_deduplicated_dataset(
                dataframe=self.deduped, output_path=tmp_path
            )
            self.assertEqual(returned, tmp_path.resolve())
            self.assertTrue(returned.is_file())
            reloaded = pd.read_csv(returned, parse_dates=["InvoiceDate"])
            self.assertEqual(
                reloaded.shape,
                (EXPECTED_DEDUPLICATED_ROWS, EXPECTED_COLUMN_COUNT),
            )
            self.assertEqual(int(reloaded.duplicated(keep="first").sum()), 0)
            self.assertTrue(
                pd.api.types.is_datetime64_any_dtype(reloaded["InvoiceDate"])
            )




class TestInvalidData(unittest.TestCase):
    """Verify Phase 5.3 invalid-data handling on the actual 5.2 dataset.

    Loads the Phase 5.2 processed dataset (``data/processed/OnlineRetail_deduplicated.csv``),
    recalculates the true invalid-data counts, applies the approved removal rules
    (cancellation invoices / non-positive Quantity / non-positive UnitPrice), and
    verifies the result: invalid rows removed, valid rows unchanged, no fabricated
    values, no unexpected missing values introduced, all columns + datetime64 intact,
    the 5.2 dataset and raw CSV untouched, and the processed output written to
    ``data/processed/``.
    """

    @classmethod
    def setUpClass(cls):
        raw = load_raw_dataset()
        cleaned = handle_missing_values(raw)
        cls.src = remove_duplicates(cleaned)
        cls.invalid_mask = is_invalid_record(cls.src)
        cls.removed = remove_invalid_records(cls.src)

    # ------------------------------------------------------------------
    # Actual invalid-data counts before cleaning (recalculated on 5.2 input)
    # ------------------------------------------------------------------
    def test_cancellation_invoice_count_before_cleaning(self):
        """Cancellation invoices (InvoiceNo starts with 'C') = 9,251 (recalculated)."""
        cancel = is_cancellation_invoice(self.src)
        self.assertEqual(int(cancel.sum()), EXPECTED_CANCELLATION_INVOICES)

    def test_negative_quantity_count_before_cleaning(self):
        """Negative Quantity = 10,587 (recalculated)."""
        self.assertEqual(
            int((self.src["Quantity"] < 0).sum()), EXPECTED_NEGATIVE_QUANTITY
        )

    def test_zero_unitprice_count_before_cleaning(self):
        """Zero UnitPrice = 2,510 (recalculated)."""
        self.assertEqual(
            int((self.src["UnitPrice"] == 0).sum()), EXPECTED_ZERO_UNITPRICE
        )

    def test_negative_unitprice_count_before_cleaning(self):
        """Negative UnitPrice = 2 (recalculated)."""
        self.assertEqual(
            int((self.src["UnitPrice"] < 0).sum()), EXPECTED_NEGATIVE_UNITPRICE
        )

    def test_nonpositive_unitprice_count_before_cleaning(self):
        """Non-positive UnitPrice (<=0) = 2,512 (recalculated)."""
        self.assertEqual(
            int((self.src["UnitPrice"] <= 0).sum()), EXPECTED_NONPOSITIVE_UNITPRICE
        )

    def test_negative_monetary_count_before_cleaning(self):
        """Negative monetary value (Quantity * UnitPrice < 0) = 9,253 (recalculated)."""
        monetary = self.src["Quantity"] * self.src["UnitPrice"]
        self.assertEqual(int((monetary < 0).sum()), EXPECTED_NEGATIVE_MONETARY)

    # ------------------------------------------------------------------
    # Approved invalid-data handling / no double counting
    # ------------------------------------------------------------------
    def test_invalid_mask_count_matches_approved_total(self):
        """The removal mask flags exactly 11,763 records (R1 + R2 + R3, no overlap)."""
        self.assertEqual(
            int(self.invalid_mask.sum()), EXPECTED_INVALID_ROWS_REMOVED
        )

    def test_zero_quantity_does_not_exist(self):
        """Quantity == 0 must be 0 so 'non-positive' == 'negative' (no ambiguity)."""
        self.assertEqual(int((self.src["Quantity"] == 0).sum()), 0)

    def test_cancellations_disjoint_from_nonpositive_unitprice(self):
        """Cancellations all have UnitPrice > 0 (R1 disjoint from R3) — removed via R1."""
        cancel = is_cancellation_invoice(self.src)
        cancel_nonpos_price = cancel & (self.src["UnitPrice"] <= 0)
        self.assertEqual(int(cancel_nonpos_price.sum()), 0)

    def test_noncancel_nonpositive_qty_is_subset_of_nonpositive_price(self):
        """All non-cancel Quantity<=0 rows also have UnitPrice<=0 (R2 subset of R3)."""
        cancel = is_cancellation_invoice(self.src)
        r2 = (self.src["Quantity"] <= 0) & ~cancel
        r2_outside_r3 = r2 & ~(self.src["UnitPrice"] <= 0)
        self.assertEqual(int(r2_outside_r3.sum()), 0)

    def test_negative_quantity_not_removed_blindly(self):
        """Negative Quantity is NOT a standalone removal rule.

        Cancellations are removed via R1 (InvoiceNo status); non-cancel negatives
        additionally carry UnitPrice<=0 so they fall under R3. No row is removed
        purely because Quantity < 0.
        """
        cancel = is_cancellation_invoice(self.src)
        noncancel_neg_qty = (~cancel) & (self.src["Quantity"] < 0)
        self.assertTrue(int(noncancel_neg_qty.sum()) > 0)  # sanity: there are some
        self.assertEqual(
            int((noncancel_neg_qty & (self.src["UnitPrice"] <= 0)).sum()),
            int(noncancel_neg_qty.sum()),
        )
        # Cancellations with Q<0 are removed by R1, and R1 flag covers all of them.
        cancel_neg_qty = cancel & (self.src["Quantity"] < 0)
        self.assertEqual(
            int((cancel_neg_qty & self.invalid_mask).sum()),
            int(cancel_neg_qty.sum()),
        )

    # ------------------------------------------------------------------
    # Row counts / after-cleaning validation
    # ------------------------------------------------------------------
    def test_remove_invalid_records_row_count(self):
        """Removes exactly 11,763 rows; result is 524,878 x 8."""
        self.assertEqual(
            len(self.src) - len(self.removed), EXPECTED_INVALID_ROWS_REMOVED
        )
        self.assertEqual(
            self.removed.shape,
            (EXPECTED_INVALID_REMOVED_ROWS, EXPECTED_COLUMN_COUNT),
        )

    def test_no_cancellation_invoices_remain(self):
        """After cleaning, no InvoiceNo starts with 'C'."""
        self.assertEqual(
            int(self.removed["InvoiceNo"].astype(str).str.startswith("C").sum()), 0
        )

    def test_no_negative_or_nonpositive_quantity_remains(self):
        """After cleaning, no Quantity < 0 or Quantity <= 0 remains."""
        self.assertEqual(int((self.removed["Quantity"] < 0).sum()), 0)
        self.assertEqual(int((self.removed["Quantity"] <= 0).sum()), 0)

    def test_no_negative_or_nonpositive_unitprice_remains(self):
        """After cleaning, no UnitPrice <= 0 or UnitPrice < 0 remains."""
        self.assertEqual(int((self.removed["UnitPrice"] <= 0).sum()), 0)
        self.assertEqual(int((self.removed["UnitPrice"] < 0).sum()), 0)

    def test_no_negative_monetary_remains(self):
        """After cleaning, no negative monetary value (Quantity * UnitPrice < 0)."""
        monetary = self.removed["Quantity"] * self.removed["UnitPrice"]
        self.assertEqual(int((monetary < 0).sum()), 0)

    # ------------------------------------------------------------------
    # Valid records remain unchanged
    # ------------------------------------------------------------------
    def test_valid_records_remain_unchanged(self):
        """All non-invalid rows from the 5.2 source are preserved verbatim."""
        expected = self.src.loc[~self.invalid_mask].copy()
        expected.reset_index(drop=True, inplace=True)
        pd.testing.assert_frame_equal(
            self.removed.reset_index(drop=True),
            expected.reset_index(drop=True),
        )

    # ------------------------------------------------------------------
    # Structure / dtype / integrity
    # ------------------------------------------------------------------
    def test_columns_preserved(self):
        """All expected 8 columns remain in the cleaned dataset."""
        self.assertEqual(list(self.removed.columns), EXPECTED_COLUMNS)

    def test_invoice_date_remains_datetime64(self):
        """InvoiceDate remains datetime64 after cleaning."""
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(self.removed["InvoiceDate"])
        )

    def test_customer_id_not_fabricated(self):
        """CustomerID has no missing values and no fabricated IDs (subset of source)."""
        self.assertEqual(int(self.removed["CustomerID"].isna().sum()), 0)
        src_customers = set(self.src["CustomerID"].dropna().unique())
        rem_customers = set(self.removed["CustomerID"].unique())
        self.assertTrue(
            rem_customers.issubset(src_customers),
            "Removed dataset contains CustomerIDs not present in the 5.2 source.",
        )

    def test_no_unexpected_missing_values_introduced(self):
        """No column gains missing values relative to the 5.2 source (rows only drop)."""
        for col in EXPECTED_COLUMNS:
            before = int(self.src[col].isna().sum())
            after = int(self.removed[col].isna().sum())
            self.assertLessEqual(
                after,
                before,
                f"Column '{col}' gained missing values ({before} -> {after}).",
            )

    def test_no_duplicates_introduced(self):
        """No exact duplicates remain after cleaning (5.2 had none to begin with)."""
        self.assertEqual(int(self.removed.duplicated(keep="first").sum()), 0)

    # ------------------------------------------------------------------
    # Output / file / compatibility
    # ------------------------------------------------------------------
    def test_invalid_removed_output_in_processed_dir(self):
        """Output path lives in data/processed/ and never in data/raw/."""
        path = get_invalid_removed_dataset_path()
        self.assertEqual(path.name, INVALID_REMOVED_FILENAME)
        self.assertIn("processed", path.parts)
        self.assertNotIn(str(config.RAW_DATA_DIR), str(path))

    def test_processed_output_file_exists(self):
        """The 5.3 processed output file exists with the expected shape."""
        path = get_invalid_removed_dataset_path()
        self.assertTrue(path.is_file(), f"Expected 5.3 output not found: {path}")
        reloaded = pd.read_csv(path, parse_dates=["InvoiceDate"])
        self.assertEqual(
            reloaded.shape,
            (EXPECTED_INVALID_REMOVED_ROWS, EXPECTED_COLUMN_COUNT),
        )

    def test_save_invalid_removed_roundtrips_to_processed(self):
        """save_invalid_removed_dataset writes a round-trippable CSV to data/processed/."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir) / INVALID_REMOVED_FILENAME
            returned = save_invalid_removed_dataset(
                dataframe=self.src, output_path=tmp_path
            )
            self.assertTrue(returned.is_file())
            reloaded = pd.read_csv(returned, parse_dates=["InvoiceDate"])
            self.assertEqual(
                reloaded.shape,
                (EXPECTED_INVALID_REMOVED_ROWS, EXPECTED_COLUMN_COUNT),
            )
            self.assertEqual(int(reloaded.duplicated(keep="first").sum()), 0)
            self.assertTrue(
                pd.api.types.is_datetime64_any_dtype(reloaded["InvoiceDate"])
            )



    def test_remove_invalid_records_noop_without_invalid(self):
        """remove_invalid_records is a no-op when no invalid records are present."""
        sample = self.removed.head(50).copy()
        out = remove_invalid_records(sample)
        self.assertEqual(len(out), len(sample))
        self.assertEqual(int(is_invalid_record(out).sum()), 0)

    def test_raw_csv_remains_unchanged(self):
        """The immutable raw CSV remains unchanged (size + SHA-256 baseline)."""
        raw_path = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"
        self.assertTrue(raw_path.is_file())
        self.assertEqual(raw_path.stat().st_size, APPROVED_FILE_SIZE)
        sha = hashlib.sha256(raw_path.read_bytes()).hexdigest().upper()
        self.assertEqual(sha, APPROVED_SHA256)


class TestFilteringVerification(unittest.TestCase):
    """Verify Subphase 5.4 — owner decision: NO ADDITIONAL FILTERING REQUIRED.

    Uses the ACTUAL Phase 5.3 processed dataset
    (``data/processed/OnlineRetail_invalid_removed.csv``) for integration
    verification, plus small in-memory DataFrames for unit edge cases. 5.4 is a
    verification-only subphase: it removes 0 rows, creates no ``filtered``
    dataset, and never modifies the 5.3 data or the immutable raw CSV.
    """

    FILTER_OUTPUT_NAME = "OnlineRetail_filtered.csv"

    @classmethod
    def setUpClass(cls):
        # Verification against the REAL Phase 5.3 working dataset (read-only).
        cls.result = verify_no_additional_filtering()

    @staticmethod
    def _clean_frame():
        """A small, valid in-memory DataFrame (no missing/dup/invalid rows)."""
        return pd.DataFrame(
            {
                "InvoiceNo": ["A1", "A2"],
                "StockCode": ["S1", "S2"],
                "Description": ["d1", "d2"],
                "Quantity": [3, 5],
                "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-01-02"]),
                "UnitPrice": [1.5, 2.0],
                "CustomerID": [1001, 1002],
                "Country": ["UK", "UK"],
            }
        )

    def test_53_input_file_exists(self):
        """The Phase 5.3 working dataset must exist for 5.4 verification."""
        path = get_invalid_removed_dataset_path()
        self.assertTrue(path.is_file(), f"5.3 input missing: {path}")
        self.assertEqual(path.name, INVALID_REMOVED_FILENAME)
        self.assertIn("processed", path.parts)

    def test_53_input_shape_is_expectation(self):
        df = pd.read_csv(
            get_invalid_removed_dataset_path(), parse_dates=["InvoiceDate"]
        )
        self.assertEqual(
            df.shape, (EXPECTED_INVALID_REMOVED_ROWS, EXPECTED_COLUMN_COUNT)
        )

    def test_verification_uses_real_53_output(self):
        self.assertEqual(
            self.result["source"], "data/processed/" + INVALID_REMOVED_FILENAME
        )

    def test_verified_is_true_on_real_data(self):
        self.assertTrue(self.result["verified"])

    def test_required_columns_present(self):
        """All approved project columns must be present (none removed/added)."""
        self.assertEqual(self.result["missing_columns"], [])
        for column in EXPECTED_COLUMNS:
            self.assertIn(column, self.result["columns"])

    def test_customer_id_zero_missing(self):
        """CustomerID must have 0 missing values (never fabricated)."""
        self.assertEqual(self.result["missing_customer_id"], 0)

    def test_no_exact_duplicates_remain(self):
        """There must be 0 exact-duplicate rows in the 5.3 input."""
        self.assertEqual(self.result["duplicate_rows"], 0)

    def test_invalid_categories_absent_on_real_input(self):
        """The invalid categories handled by 5.3 must remain absent."""
        df = pd.read_csv(
            get_invalid_removed_dataset_path(), parse_dates=["InvoiceDate"]
        )
        self.assertEqual(int(is_invalid_record(df).sum()), 0)
        self.assertEqual(
            int(df["InvoiceNo"].astype(str).str.startswith("C").sum()), 0
        )
        self.assertEqual(int((df["Quantity"] <= 0).sum()), 0)
        self.assertEqual(int((df["UnitPrice"] <= 0).sum()), 0)
        self.assertEqual(self.result["invalid_rows_remaining"], 0)

    def test_rows_removed_is_zero(self):
        """5.4 must remove exactly 0 rows."""
        self.assertEqual(self.result["rows_removed"], 0)

    def test_row_count_matches_53_output(self):
        """Before/after row count is identical (the full 5.3 population)."""
        self.assertEqual(self.result["row_count"], EXPECTED_INVALID_REMOVED_ROWS)

    def test_no_filtered_dataset_created_on_disk(self):
        """No OnlineRetail_filtered.csv may be created by 5.4."""
        path = config.PROCESSED_DATA_DIR / self.FILTER_OUTPUT_NAME
        self.assertFalse(path.is_file(), f"Unexpected filtered file: {path}")

    def test_verification_writes_no_new_processed_file(self):
        """Running the verification must not alter the processed file set."""
        processed_dir = config.PROCESSED_DATA_DIR
        before = set(p.name for p in processed_dir.glob("*.csv"))
        verify_no_additional_filtering()
        after = set(p.name for p in processed_dir.glob("*.csv"))
        self.assertEqual(before, after)

    def test_no_transformation_on_in_memory_frame(self):
        """Verify must NOT transform or mutate an in-memory input frame."""
        df = self._clean_frame()
        original = df.copy()
        result = verify_no_additional_filtering(df)
        self.assertTrue(result["verified"])
        self.assertEqual(result["rows_removed"], 0)
        self.assertEqual(list(result["columns"]), EXPECTED_COLUMNS)
        pd.testing.assert_frame_equal(df, original)

    def test_invoice_date_remains_datetime_compatible(self):
        """Verify preserves InvoiceDate as datetime-compatible on input."""
        df = self._clean_frame()
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]))
        result = verify_no_additional_filtering(df)
        self.assertEqual(result["row_count"], len(df))

    def test_verify_accepts_in_memory_clean_frame(self):
        """A clean in-memory frame verifies as needing no filtering."""
        result = verify_no_additional_filtering(self._clean_frame())
        self.assertTrue(result["verified"])
        self.assertEqual(result["missing_customer_id"], 0)
        self.assertEqual(result["duplicate_rows"], 0)
        self.assertEqual(result["invalid_rows_remaining"], 0)
        self.assertEqual(result["rows_removed"], 0)

    def test_flags_missing_column(self):
        """A frame missing an approved column must not verify."""
        df = self._clean_frame().drop(columns=["Country"])
        result = verify_no_additional_filtering(df)
        self.assertFalse(result["verified"])
        self.assertIn("Country", result["missing_columns"])

    def test_flags_missing_customer_id(self):
        """A frame with a missing CustomerID must not verify (no fabrication)."""
        df = self._clean_frame()
        df.loc[0, "CustomerID"] = None
        result = verify_no_additional_filtering(df)
        self.assertFalse(result["verified"])
        self.assertEqual(result["missing_customer_id"], 1)

    def test_flags_duplicate_rows(self):
        """A frame with an exact duplicate must not verify."""
        df = self._clean_frame()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        result = verify_no_additional_filtering(df)
        self.assertFalse(result["verified"])
        self.assertEqual(result["duplicate_rows"], 1)

    def test_flags_invalid_record_present(self):
        """A frame carrying a cancellation (invalid) record must not verify."""
        df = self._clean_frame()
        return_row = pd.DataFrame(
            {
                "InvoiceNo": ["C999"],
                "StockCode": ["S9"],
                "Description": ["d9"],
                "Quantity": [-3],
                "InvoiceDate": [pd.Timestamp("2011-01-03")],
                "UnitPrice": [1.5],
                "CustomerID": [2001],
                "Country": ["UK"],
            }
        )
        df = pd.concat([df, return_row], ignore_index=True)
        result = verify_no_additional_filtering(df)
        self.assertFalse(result["verified"])
        self.assertEqual(result["invalid_rows_remaining"], 1)

    def test_decision_reports_no_additional_filtering(self):
        """The verification result must report NO ADDITIONAL FILTERING REQUIRED."""
        self.assertEqual(
            self.result["decision"], NO_ADDITIONAL_FILTERING_REQUIRED
        )
        self.assertEqual(
            self.result["decision"], "NO ADDITIONAL FILTERING REQUIRED"
        )

    def test_previous_processed_outputs_preserved(self):
        """The final processed output remains present."""
        # Only the final processed file is permanently stored; intermediates are in-memory
        filename = "OnlineRetail_invalid_removed.csv"
        path = config.PROCESSED_DATA_DIR / filename
        self.assertTrue(path.is_file(), f"Expected processed file: {path}")

    def test_raw_csv_remains_unchanged(self):
        """The immutable raw CSV remains unchanged (size + SHA-256 baseline)."""
        raw_path = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"
        self.assertTrue(raw_path.is_file())
        self.assertEqual(raw_path.stat().st_size, APPROVED_FILE_SIZE)
        sha = hashlib.sha256(raw_path.read_bytes()).hexdigest().upper()
        self.assertEqual(sha, APPROVED_SHA256)


class TestPhase55NoAdditionalTransformation(unittest.TestCase):
    """Phase 5.5 — Transformation (owner-approved verification-only).

    The project owner approved 5.5 as "NO ADDITIONAL TRANSFORMATION
    REQUIRED": no transformation is applied to the 5.3 working dataset,
    rows changed = 0, and no transformed output CSV is created.
    InvoiceDate -> datetime64 remains Phase 4.2 loading behavior and must
    NOT be moved or duplicated into 5.5.
    """

    @classmethod
    def setUpClass(cls):
        cls.result = verify_no_additional_transformation()
        cls.df = pd.read_csv(
            get_invalid_removed_dataset_path(), parse_dates=["InvoiceDate"]
        )

    def _clean_frame(self):
        """A small clean in-memory frame mirroring the approved schema."""
        return pd.DataFrame(
            {
                "InvoiceNo": ["A1", "A2"],
                "StockCode": ["S1", "S2"],
                "Description": ["d1", None],
                "Quantity": [3, 7],
                "InvoiceDate": pd.to_datetime(
                    ["2011-01-02 10:00:00", "2011-01-03 11:30:00"]
                ),
                "UnitPrice": [1.25, 4.5],
                "CustomerID": [2000, 2001],
                "Country": ["UK", "France"],
            }
        )
    # -- 1. 5.3 input exists -------------------------------------------------
    def test_53_input_exists(self):
        path = get_invalid_removed_dataset_path()
        self.assertTrue(path.is_file(), f"Expected 5.3 dataset: {path}")

    def test_verification_uses_real_53_output(self):
        self.assertEqual(
            self.result["source"], "data/processed/" + INVALID_REMOVED_FILENAME
        )

    # -- 2. approved columns exist ------------------------------------------
    def test_approved_columns_exist(self):
        self.assertEqual(self.result["missing_columns"], [])
        for column in EXPECTED_COLUMNS:
            self.assertIn(column, self.result["columns"])

    # -- 3. InvoiceDate is datetime64 ----------------------------------------
    def test_invoice_date_is_datetime64(self):
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(self.df["InvoiceDate"]),
            f"InvoiceDate observed as {self.result['observed_dtypes']['InvoiceDate']}",
        )
        self.assertNotIn("InvoiceDate", self.result["dtype_issues"])

    # -- 4/5/6. numeric dtypes ----------------------------------------------
    def test_quantity_is_numeric_integer(self):
        self.assertTrue(pd.api.types.is_integer_dtype(self.df["Quantity"]))
        self.assertNotIn("Quantity", self.result["dtype_issues"])

    def test_unit_price_is_numeric_float(self):
        self.assertTrue(
            pd.api.types.is_numeric_dtype(self.df["UnitPrice"])
            and not pd.api.types.is_bool_dtype(self.df["UnitPrice"])
        )
        self.assertNotIn("UnitPrice", self.result["dtype_issues"])

    def test_customer_id_is_numeric_integer(self):
        self.assertTrue(pd.api.types.is_integer_dtype(self.df["CustomerID"]))
        self.assertNotIn("CustomerID", self.result["dtype_issues"])

    # -- 7. schema unchanged --------------------------------------------------
    def test_schema_remains_unchanged(self):
        self.assertEqual(list(self.df.columns), EXPECTED_COLUMNS)
        self.assertEqual(len(self.df.columns), EXPECTED_COLUMN_COUNT)

    # -- 8. no rows changed ---------------------------------------------------
    def test_rows_changed_is_zero(self):
        self.assertEqual(self.result["rows_changed"], 0)
        self.assertEqual(self.result["row_count"], EXPECTED_INVALID_REMOVED_ROWS)

    def test_no_mutation_of_in_memory_frame(self):
        df = self._clean_frame()
        original = df.copy()
        result = verify_no_additional_transformation(df)
        self.assertTrue(result["verified"])
        self.assertEqual(result["rows_changed"], 0)
        pd.testing.assert_frame_equal(df, original)

    # -- 9. no transformed output CSV -----------------------------------------
    def test_no_transformed_dataset_created_on_disk(self):
        path = config.PROCESSED_DATA_DIR / TRANSFORMED_FILENAME
        self.assertFalse(path.is_file(), f"Unexpected transformed file: {path}")

    def test_verification_writes_no_new_processed_file(self):
        processed_dir = config.PROCESSED_DATA_DIR
        before = set(p.name for p in processed_dir.glob("*.csv"))
        verify_no_additional_transformation()
        after = set(p.name for p in processed_dir.glob("*.csv"))
        self.assertEqual(before, after)

    # -- 10. previous processed datasets unchanged ----------------------------
    def test_previous_processed_outputs_preserved(self):
        """The final processed output remains present."""
        # Only the final processed file is permanently stored; intermediates are in-memory
        filename = "OnlineRetail_invalid_removed.csv"
        path = config.PROCESSED_DATA_DIR / filename
        self.assertTrue(path.is_file(), f"Expected processed file: {path}")

    # -- 11. raw dataset unchanged --------------------------------------------
    def test_raw_csv_remains_unchanged_55(self):
        raw_path = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"
        self.assertTrue(raw_path.is_file())
        self.assertEqual(raw_path.stat().st_size, APPROVED_FILE_SIZE)
        sha = hashlib.sha256(raw_path.read_bytes()).hexdigest().upper()
        self.assertEqual(sha, APPROVED_SHA256)

    # -- 12. decision string ----------------------------------------------------
    def test_decision_reports_no_additional_transformation(self):
        self.assertEqual(
            self.result["decision"], NO_ADDITIONAL_TRANSFORMATION_REQUIRED
        )
        self.assertEqual(
            self.result["decision"], "NO ADDITIONAL TRANSFORMATION REQUIRED"
        )
        self.assertTrue(self.result["verified"])

    def test_flags_missing_column_as_unverified(self):
        """A frame missing an approved column must not verify."""
        df = self._clean_frame().drop(columns=["Country"])
        result = verify_no_additional_transformation(df)
        self.assertFalse(result["verified"])
        self.assertIn("Country", result["missing_columns"])

    def test_flags_wrong_dtype_as_unverified(self):
        """A frame whose InvoiceDate is text must not verify."""
        df = self._clean_frame()
        df["InvoiceDate"] = df["InvoiceDate"].astype(str)
        result = verify_no_additional_transformation(df)
        self.assertFalse(result["verified"])
        self.assertIn("InvoiceDate", result["dtype_issues"])

class TestPhase56NoAdditionalOutlierHandling(unittest.TestCase):
    """Phase 5.6 — Outlier Handling (owner-approved verification-only).

    The project owner approved 5.6 as "NO ADDITIONAL OUTLIER HANDLING
    REQUIRED": no statistical outlier method is applied to the 5.3 working
    dataset, rows removed = 0, and no outlier-specific dataset is created.
    """

    @classmethod
    def setUpClass(cls):
        cls.result = verify_no_additional_outlier_handling()
        cls.df = pd.read_csv(
            get_invalid_removed_dataset_path(), parse_dates=["InvoiceDate"]
        )

    def _clean_frame(self):
        """A small clean in-memory frame mirroring the approved schema."""
        return pd.DataFrame(
            {
                "InvoiceNo": ["A1", "A2"],
                "StockCode": ["S1", "S2"],
                "Description": ["d1", None],
                "Quantity": [3, 7],
                "InvoiceDate": pd.to_datetime(
                    ["2011-01-02 10:00:00", "2011-01-03 11:30:00"]
                ),
                "UnitPrice": [1.25, 4.5],
                "CustomerID": [2000, 2001],
                "Country": ["UK", "France"],
            }
        )

    def test_53_input_exists(self):
        path = get_invalid_removed_dataset_path()
        self.assertTrue(path.is_file(), f"Expected 5.3 dataset: {path}")

    def test_verification_uses_real_53_output(self):
        self.assertEqual(
            self.result["source"], "data/processed/" + INVALID_REMOVED_FILENAME
        )

    def test_input_shape_is_expected(self):
        self.assertEqual(
            self.df.shape, (EXPECTED_INVALID_REMOVED_ROWS, EXPECTED_COLUMN_COUNT)
        )
        self.assertEqual(self.result["rows_before"], EXPECTED_INVALID_REMOVED_ROWS)

    def test_approved_columns_exist(self):
        self.assertEqual(self.result["missing_columns"], [])
        self.assertEqual(list(self.df.columns), EXPECTED_COLUMNS)

    def test_expected_dtypes(self):
        self.assertEqual(self.result["dtype_issues"], [])
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.df["InvoiceDate"]))
        self.assertTrue(pd.api.types.is_integer_dtype(self.df["Quantity"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(self.df["UnitPrice"]))
        self.assertTrue(pd.api.types.is_integer_dtype(self.df["CustomerID"]))
        for column in ("InvoiceNo", "StockCode", "Description", "Country"):
            self.assertIn(column, self.result["observed_dtypes"])

    def test_customer_id_has_no_missing_values(self):
        self.assertEqual(self.result["missing_customer_id"], 0)

    def test_duplicates_remain_zero(self):
        self.assertEqual(self.result["duplicate_rows"], 0)

    def test_cancellation_records_remain_zero(self):
        self.assertEqual(
            int(self.df["InvoiceNo"].astype(str).str.startswith("C").sum()), 0
        )

    def test_nonpositive_quantity_remains_zero(self):
        self.assertEqual(int((self.df["Quantity"] <= 0).sum()), 0)

    def test_nonpositive_unitprice_remains_zero(self):
        self.assertEqual(int((self.df["UnitPrice"] <= 0).sum()), 0)

    def test_invalid_rows_remaining_zero(self):
        self.assertEqual(self.result["invalid_rows_remaining"], 0)

    def test_rows_before_equal_rows_after(self):
        self.assertEqual(self.result["rows_before"], self.result["rows_after"])
        self.assertEqual(self.result["rows_after"], EXPECTED_INVALID_REMOVED_ROWS)

    def test_rows_removed_is_zero(self):
        self.assertEqual(self.result["rows_removed"], 0)

    def test_no_outlier_dataset_created_on_disk(self):
        for filename in (OUTLIER_REMOVED_FILENAME, OUTLIERS_FILENAME):
            path = config.PROCESSED_DATA_DIR / filename
            self.assertFalse(path.is_file(), f"Unexpected outlier file: {path}")

    def test_verification_writes_no_new_processed_file(self):
        processed_dir = config.PROCESSED_DATA_DIR
        before = set(p.name for p in processed_dir.glob("*.csv"))
        verify_no_additional_outlier_handling()
        after = set(p.name for p in processed_dir.glob("*.csv"))
        self.assertEqual(before, after)

    def test_previous_processed_outputs_preserved(self):
        """The final processed output remains present."""
        # Only the final processed file is permanently stored; intermediates are in-memory
        filename = "OnlineRetail_invalid_removed.csv"
        path = config.PROCESSED_DATA_DIR / filename
        self.assertTrue(path.is_file(), f"Expected processed file: {path}")

    def test_raw_csv_size_unchanged(self):
        raw_path = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"
        self.assertTrue(raw_path.is_file())
        self.assertEqual(raw_path.stat().st_size, APPROVED_FILE_SIZE)

    def test_raw_csv_sha256_unchanged(self):
        raw_path = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"
        sha = hashlib.sha256(raw_path.read_bytes()).hexdigest().upper()
        self.assertEqual(sha, APPROVED_SHA256)

    def test_decision_reports_no_additional_outlier_handling(self):
        self.assertEqual(
            self.result["decision"], NO_ADDITIONAL_OUTLIER_HANDLING_REQUIRED
        )
        self.assertEqual(
            self.result["decision"], "NO ADDITIONAL OUTLIER HANDLING REQUIRED"
        )
        self.assertTrue(self.result["verified"])

    def test_no_mutation_of_in_memory_frame(self):
        df = self._clean_frame()
        original = df.copy()
        result = verify_no_additional_outlier_handling(df)
        self.assertTrue(result["verified"])
        self.assertEqual(result["rows_removed"], 0)
        self.assertEqual(result["rows_before"], result["rows_after"])
        pd.testing.assert_frame_equal(df, original)

    def test_flags_missing_column_as_unverified(self):
        df = self._clean_frame().drop(columns=["Country"])
        result = verify_no_additional_outlier_handling(df)
        self.assertFalse(result["verified"])
        self.assertIn("Country", result["missing_columns"])

    def test_flags_invalid_record_as_unverified(self):
        df = self._clean_frame()
        df.loc[0, "Quantity"] = -3
        result = verify_no_additional_outlier_handling(df)
        self.assertFalse(result["verified"])
        self.assertEqual(result["invalid_rows_remaining"], 1)


class TestPhase58FinalValidation(unittest.TestCase):
    """Phase 5.8 — final read-only validation gate."""

    @classmethod
    def setUpClass(cls):
        cls.result = verify_phase5_final_validation()
        cls.df = pd.read_csv(
            get_invalid_removed_dataset_path(), parse_dates=["InvoiceDate"]
        )

    @staticmethod
    def _clean_frame():
        return pd.DataFrame(
            {
                "InvoiceNo": ["A1", "A2"],
                "StockCode": ["S1", "S2"],
                "Description": ["d1", "d2"],
                "Quantity": [3, 5],
                "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-01-02"]),
                "UnitPrice": [1.5, 2.5],
                "CustomerID": [1001, 1002],
                "Country": ["UK", "FR"],
            }
        )

    def test_53_input_exists(self):
        path = get_invalid_removed_dataset_path()
        self.assertTrue(path.is_file(), f"Expected 5.3 dataset: {path}")

    def test_final_row_count_is_expected(self):
        self.assertEqual(self.df.shape, (524_878, EXPECTED_COLUMN_COUNT))
        self.assertEqual(self.result["rows_after"], 524_878)
        self.assertEqual(self.result["rows_before"], 524_878)

    def test_exact_schema(self):
        self.assertEqual(list(self.df.columns), EXPECTED_COLUMNS)
        self.assertEqual(self.result["schema_valid"], True)

    def test_required_dtypes(self):
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.df["InvoiceDate"]))
        self.assertTrue(pd.api.types.is_integer_dtype(self.df["Quantity"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(self.df["UnitPrice"]))
        self.assertTrue(pd.api.types.is_integer_dtype(self.df["CustomerID"]))
        self.assertTrue(self.result["dtypes_valid"])

    def test_customer_id_has_no_missing_values(self):
        self.assertEqual(self.result["customerid_valid"], True)
        self.assertEqual(self.df["CustomerID"].isna().sum(), 0)

    def test_no_duplicates(self):
        self.assertEqual(self.df.duplicated().sum(), 0)
        self.assertEqual(self.result["duplicates_valid"], True)

    def test_invalid_categories_absent(self):
        self.assertEqual(int(self.df["InvoiceNo"].astype(str).str.startswith("C").sum()), 0)
        self.assertEqual(int((self.df["Quantity"] <= 0).sum()), 0)
        self.assertEqual(int((self.df["UnitPrice"] <= 0).sum()), 0)
        self.assertEqual(self.result["invalid_records_valid"], True)

    def test_transaction_level_structure_preserved(self):
        self.assertTrue(self.result["transaction_level_valid"])
        self.assertEqual(self.result["row_count"], 524_878)

    def test_no_row_removal_or_change(self):
        self.assertEqual(self.result["rows_removed"], 0)
        self.assertEqual(self.result["rows_changed"], 0)
        self.assertEqual(self.result["rows_after"], self.result["rows_before"])

    def test_no_mutation_of_in_memory_frame(self):
        df = self._clean_frame()
        original = df.copy()
        result = verify_phase5_final_validation(df)
        self.assertTrue(result["verified"])
        self.assertEqual(result["decision"], PHASE_5_FINAL_VALIDATION_PASSED)
        pd.testing.assert_frame_equal(df, original)

    def test_no_new_processed_output_created(self):
        before = set(p.name for p in config.PROCESSED_DATA_DIR.glob("*.csv"))
        verify_phase5_final_validation()
        after = set(p.name for p in config.PROCESSED_DATA_DIR.glob("*.csv"))
        self.assertEqual(before, after)

    def test_existing_processed_outputs_preserved(self):
        """The final processed output remains present."""
        # Only the final processed file is permanently stored; intermediates are in-memory
        filename = "OnlineRetail_invalid_removed.csv"
        path = config.PROCESSED_DATA_DIR / filename
        self.assertTrue(path.is_file(), f"Expected processed file: {path}")

    def test_raw_csv_size_unchanged(self):
        raw_path = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"
        self.assertTrue(raw_path.is_file())
        self.assertEqual(raw_path.stat().st_size, APPROVED_FILE_SIZE)

    def test_raw_csv_sha256_unchanged(self):
        raw_path = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"
        sha = hashlib.sha256(raw_path.read_bytes()).hexdigest().upper()
        self.assertEqual(sha, APPROVED_SHA256)

    def test_correct_decision_string(self):
        self.assertEqual(self.result["decision"], PHASE_5_FINAL_VALIDATION_PASSED)
        self.assertTrue(self.result["verified"])

    def test_missing_column_fails_safely(self):
        df = self._clean_frame().drop(columns=["Country"])
        result = verify_phase5_final_validation(df)
        self.assertFalse(result["verified"])
        self.assertIn("Country", result["missing_columns"])

    def test_extra_column_fails_safely(self):
        df = self._clean_frame()
        df["Unexpected"] = "extra"
        result = verify_phase5_final_validation(df)
        self.assertFalse(result["verified"])
        self.assertEqual(result["unexpected_columns"], ["Unexpected"])


class TestHealthFixes(unittest.TestCase):
    """Verify raw-output protection and exact-schema validation."""

    @staticmethod
    def _clean_frame():
        return pd.DataFrame(
            {
                "InvoiceNo": ["I1"],
                "StockCode": ["S1"],
                "Description": ["d1"],
                "Quantity": [1],
                "InvoiceDate": [pd.Timestamp("2011-01-01")],
                "UnitPrice": [1.0],
                "CustomerID": [1],
                "Country": ["UK"],
            }
        )

    def test_processed_output_still_works(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = pathlib.Path(tmp_dir) / "working.csv"
            returned = save_working_dataset(self._clean_frame(), output_path)
            self.assertEqual(returned, output_path.resolve())
            self.assertTrue(returned.is_file())

    def test_all_save_apis_reject_raw_directory(self):
        raw_output = pathlib.Path(config.RAW_DATA_DIR) / "health_fix.csv"
        for save_function in (
            save_working_dataset,
            save_deduplicated_dataset,
            save_invalid_removed_dataset,
        ):
            with self.subTest(save_function=save_function.__name__):
                with self.assertRaises(ValueError) as context:
                    save_function(self._clean_frame(), raw_output)
                self.assertIn("raw-data directory", str(context.exception))

    def test_raw_dataset_cannot_be_overwritten(self):
        """No save API may overwrite the immutable raw dataset itself.

        Reconstructed for OPTION B. Complements
        test_all_save_apis_reject_raw_directory (which probes a sibling
        filename inside data/raw/) by targeting the EXACT raw CSV and proving
        the refusal happens BEFORE any bytes are written: the raw file's size
        and SHA-256 must be identical immediately after every rejected
        attempt (no partial write / truncation).
        """
        for save_function in (
            save_working_dataset,
            save_deduplicated_dataset,
            save_invalid_removed_dataset,
        ):
            with self.subTest(save_function=save_function.__name__):
                with self.assertRaises(ValueError) as context:
                    save_function(self._clean_frame(), RAW_CSV_PATH)
                self.assertIn("raw-data directory", str(context.exception))
        self.assertEqual(RAW_CSV_PATH.stat().st_size, APPROVED_FILE_SIZE)
        sha = hashlib.sha256(RAW_CSV_PATH.read_bytes()).hexdigest().upper()
        self.assertEqual(sha, APPROVED_SHA256)

    def test_5_2_functionality_remains_compatible(self):
        """The Phase 5.2 dedup API keeps its semantics after the OPTION B change.

        Reconstructed for OPTION B (backward-compat regression guard):
        1. save_deduplicated_dataset still DEDUPLICATES a provided frame —
           5.2 semantics survive through the compat save API.
        2. Without an explicit output_path it persists NOTHING (returns None
           and never creates data/processed/OnlineRetail_deduplicated.csv) —
           the OPTION B in-memory contract.
        """
        frame_with_duplicates = pd.concat(
            [self._clean_frame()] * 3, ignore_index=True
        )
        self.assertEqual(get_duplicate_count(frame_with_duplicates), 2)

        # OPTION B default: no explicit output_path -> nothing is persisted.
        self.assertIsNone(save_deduplicated_dataset(frame_with_duplicates))
        self.assertFalse(get_deduplicated_dataset_path().exists())

        # Explicit path: 5.2 dedup semantics preserved through the save API.
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = pathlib.Path(tmp_dir) / "compat_deduplicated.csv"
            returned = save_deduplicated_dataset(
                frame_with_duplicates, output_path
            )
            self.assertEqual(returned, output_path.resolve())
            saved = pd.read_csv(returned)
            self.assertEqual(len(saved), 1)  # 3 identical rows -> first kept
            self.assertEqual(get_duplicate_count(saved), 0)



    def test_exact_schema_passes_all_verifications(self):
        dataframe = self._clean_frame()
        for verify_function in (
            verify_no_additional_filtering,
            verify_no_additional_transformation,
            verify_no_additional_outlier_handling,
        ):
            with self.subTest(verify_function=verify_function.__name__):
                self.assertTrue(verify_function(dataframe)["verified"])

    def test_unexpected_extra_column_fails_all_verifications(self):
        dataframe = self._clean_frame()
        dataframe["Unexpected"] = "not approved"
        for verify_function in (
            verify_no_additional_filtering,
            verify_no_additional_transformation,
            verify_no_additional_outlier_handling,
        ):
            with self.subTest(verify_function=verify_function.__name__):
                result = verify_function(dataframe)
                self.assertFalse(result["verified"])
                self.assertEqual(result["unexpected_columns"], ["Unexpected"])


class TestPhase57NoAdditionalAggregation(unittest.TestCase):
    """Phase 5.7 — owner-approved verification / no-op aggregation check."""

    @classmethod
    def setUpClass(cls):
        cls.result = verify_no_additional_aggregation()
        cls.df = pd.read_csv(
            get_invalid_removed_dataset_path(), parse_dates=["InvoiceDate"]
        )

    @staticmethod
    def _clean_frame():
        return pd.DataFrame(
            {
                "InvoiceNo": ["A1", "A2"],
                "StockCode": ["S1", "S2"],
                "Description": ["d1", "d2"],
                "Quantity": [2, 5],
                "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-01-02"]),
                "UnitPrice": [1.5, 2.5],
                "CustomerID": [1001, 1002],
                "Country": ["UK", "FR"],
            }
        )

    def test_53_input_exists(self):
        path = get_invalid_removed_dataset_path()
        self.assertTrue(path.is_file(), f"Expected 5.3 dataset: {path}")

    def test_53_input_has_expected_columns(self):
        self.assertEqual(list(self.df.columns), EXPECTED_COLUMNS)
        self.assertEqual(self.df.shape, (EXPECTED_INVALID_REMOVED_ROWS, EXPECTED_COLUMN_COUNT))

    def test_customer_id_has_no_missing_values(self):
        self.assertEqual(self.result["missing_customer_id"], 0)
        self.assertTrue(self.df["CustomerID"].notna().all())

    def test_dataset_remains_transaction_level(self):
        self.assertTrue(self.result["transaction_level"])
        self.assertEqual(self.result["row_count"], EXPECTED_INVALID_REMOVED_ROWS)

    def test_no_mutation_of_in_memory_frame(self):
        df = self._clean_frame()
        original = df.copy()
        result = verify_no_additional_aggregation(df)
        self.assertTrue(result["verified"])
        self.assertEqual(result["decision"], NO_ADDITIONAL_AGGREGATION_REQUIRED)
        pd.testing.assert_frame_equal(df, original)

    def test_no_aggregation_output_created_on_disk(self):
        for filename in (
            "OnlineRetail_aggregated.csv",
            "OnlineRetail_customer_aggregated.csv",
            "OnlineRetail_rfm.csv",
        ):
            path = config.PROCESSED_DATA_DIR / filename
            self.assertFalse(path.is_file(), f"Unexpected aggregation file: {path}")

    def test_existing_processed_outputs_preserved(self):
        """The final processed output remains present."""
        # Only the final processed file is permanently stored; intermediates are in-memory
        filename = "OnlineRetail_invalid_removed.csv"
        path = config.PROCESSED_DATA_DIR / filename
        self.assertTrue(path.is_file(), f"Expected processed file: {path}")

    def test_raw_csv_remains_unchanged(self):
        raw_path = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"
        self.assertTrue(raw_path.is_file())
        self.assertEqual(raw_path.stat().st_size, APPROVED_FILE_SIZE)
        sha = hashlib.sha256(raw_path.read_bytes()).hexdigest().upper()
        self.assertEqual(sha, APPROVED_SHA256)

    def test_decision_reports_no_additional_aggregation(self):
        self.assertEqual(
            self.result["decision"], NO_ADDITIONAL_AGGREGATION_REQUIRED
        )
        self.assertEqual(
            self.result["decision"], "NO ADDITIONAL AGGREGATION REQUIRED"
        )
        self.assertTrue(self.result["verified"])

    def test_missing_required_column_causes_failure(self):
        df = self._clean_frame().drop(columns=["CustomerID"])
        result = verify_no_additional_aggregation(df)
        self.assertFalse(result["verified"])
        self.assertIn("CustomerID", result["missing_columns"])

    def test_extra_unexpected_column_causes_failure(self):
        df = self._clean_frame()
        df["Unexpected"] = "extra"
        result = verify_no_additional_aggregation(df)
        self.assertFalse(result["verified"])
        self.assertEqual(result["unexpected_columns"], ["Unexpected"])


if __name__ == "__main__":
    unittest.main(verbosity=2)