"""
tests/test_data_loading.py — Data Loading, Data Type, File Handling & Exception Testing (Phase 4.1 – 4.4)

Purpose:
    Verify that the approved raw CSV dataset (data/raw/OnlineRetail.csv) can be
    loaded into a pandas DataFrame by src.data_loading with the expected
    structure, that the observed pandas dtypes are as expected (including
    InvoiceDate parsed to datetime64), that the approved file path is handled
    reliably, that loading failures raise clear, useful errors, and that the
    raw file remains unchanged.

Scope:
    This suite tests the Phase 4.1 CSV-loading, Phase 4.2 data-type
    inspection, Phase 4.3 file-handling, and Phase 4.4 exception-handling
    functionality:
      1. The approved raw CSV file path resolves correctly and the file exists.
      2. The approved raw CSV file can be loaded.
      3. The loaded DataFrame has the expected shape (541,909 rows, 8 columns).
      4. The expected 8 columns are present.
      5. The observed pandas dtypes match the expected raw-load dtypes.
      6. Observed types are compared with the Phase 3 data dictionary; after
         the 4.2 correction, InvoiceDate is parsed to datetime64 during CSV
         loading, so observed types now match the dictionary.
      7. At least one valid InvoiceDate value is confirmed to be a real
         datetime.
      8. Real-customer read-only verification (a CustomerID other than 17850).
      9. Loading failures are handled clearly: a missing file raises
         FileNotFoundError; an empty or unreadable CSV raises a clear,
         useful ValueError. (Failure tests use temporary/mocked paths —
         the approved raw dataset is never modified.)
      10. The raw CSV file remains unchanged (size + SHA-256 against the
         approved Phase 3 baseline).

    This does NOT test cleaning, deduplication, negative-value handling, EDA,
    RFM, segmentation, or visualization — those belong to later phases and are
    intentionally out of scope here.

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
from unittest import mock

import pandas as pd

# ---------------------------------------------------------------------------
# Project root - added to sys.path so config and src are importable
# regardless of how the test is invoked.
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.data_loading import (
    DATASET_FILENAME,
    get_raw_csv_path,
    inspect_data_types,
    load_raw_dataset,
)

# ---------------------------------------------------------------------------
# Approved dataset baseline (Source: README.md — Phase 3 approval / 3.5)
# ---------------------------------------------------------------------------
RAW_CSV_PATH = pathlib.Path(config.RAW_DATA_DIR) / DATASET_FILENAME

# Size and SHA-256 recorded at Phase 3 approval (final review).
APPROVED_FILE_SIZE = 47_901_468
APPROVED_SHA256 = "BFA47136118BC854A31E69D5C9E9689A2D07B73909F253679F2CC85EC4EB84EB"

# Expected schema of the approved dataset (Phase 3.2 / 3.3).
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

# ---------------------------------------------------------------------------
# Expected data types (Phase 4.2)
# ---------------------------------------------------------------------------
# Observed pandas dtypes of the DataFrame returned by load_raw_dataset()
# (pandas 3.0.5): text columns use the dedicated 'str' dtype; InvoiceDate is
# parsed to datetime64 during CSV loading (4.2 correction). pandas 3.0.5
# represents parsed dates as 'datetime64[us]' (microsecond resolution).
EXPECTED_RAW_DTYPES = {
    "InvoiceNo": "str",
    "StockCode": "str",
    "Description": "str",
    "Quantity": "int64",
    "InvoiceDate": "datetime64[us]",  # parsed from CSV text during loading
    "UnitPrice": "float64",
    "CustomerID": "int64",
    "Country": "str",
}

# Approved Phase 3.2 / 3.3 data dictionary recorded dtypes
# (Source: README.md Section 3.3.2 Data Dictionary).
DOCUMENTED_DTYPES = {
    "InvoiceNo": "object (str)",
    "StockCode": "object (str)",
    "Description": "object (str)",
    "Quantity": "int64",
    "InvoiceDate": "datetime64",  # now realized by parsing during loading
    "UnitPrice": "float64",
    "CustomerID": "int64",
    "Country": "object (str)",
}


def _dtype_category(dtype_name):
    """Normalize dtype names to a single category for comparison.

    pandas 3.0 reads text columns with the dedicated 'str' dtype
    (StringDtype), which is the string type and is equivalent to the
    documented 'object (str)'. Parsed dates appear as 'datetime64[us]' (or any
    'datetime64[...]' resolution), equivalent to the documented 'datetime64'.
    """
    if dtype_name in ("str", "object", "object (str)", "string"):
        return "string"
    if dtype_name.startswith("datetime64"):
        return "datetime64"
    return dtype_name


# ---------------------------------------------------------------------------
# Real-customer verification (Phase 4.2 correction)
# ---------------------------------------------------------------------------
# A real CustomerID (other than 17850, which was used in Phase 3.3.4) that has
# multiple transaction records in the approved dataset.
VERIFICATION_CUSTOMER_ID = 12_347




class TestRawCsvUnchanged(unittest.TestCase):
    """Verify the approved raw CSV file exists and remains unchanged."""

    def test_raw_csv_exists(self):
        """The approved raw CSV must exist on disk."""
        self.assertTrue(
            RAW_CSV_PATH.is_file(),
            f"Approved raw CSV is missing: {RAW_CSV_PATH}",
        )

    def test_raw_csv_size_unchanged(self):
        """The raw CSV byte size must match the Phase 3 approval record."""
        actual_size = RAW_CSV_PATH.stat().st_size
        self.assertEqual(
            actual_size,
            APPROVED_FILE_SIZE,
            f"Raw CSV size changed: {actual_size} != {APPROVED_FILE_SIZE}",
        )

    def test_raw_csv_sha256_unchanged(self):
        """The raw CSV SHA-256 digest must match the Phase 3 approval record."""
        digest = hashlib.sha256()
        with open(RAW_CSV_PATH, "rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(chunk)
        actual_sha256 = digest.hexdigest().upper()
        self.assertEqual(
            actual_sha256,
            APPROVED_SHA256,
            f"Raw CSV SHA-256 changed: {actual_sha256} != {APPROVED_SHA256}",
        )


class TestFileHandling(unittest.TestCase):
    """Verify the raw CSV path resolves correctly and the file exists (Phase 4.3)."""

    def test_raw_csv_path_resolves_correctly(self):
        """get_raw_csv_path() must resolve to RAW_DATA_DIR / OnlineRetail.csv."""
        expected = (pathlib.Path(config.RAW_DATA_DIR) / DATASET_FILENAME).resolve()
        self.assertEqual(get_raw_csv_path(), expected)
        self.assertTrue(get_raw_csv_path().is_absolute())

    def test_raw_csv_path_is_under_approved_directory(self):
        """The resolved path must sit directly in the approved data/raw dir."""
        csv_path = get_raw_csv_path()
        self.assertEqual(csv_path.parent, pathlib.Path(config.RAW_DATA_DIR).resolve())

    def test_approved_file_exists_at_resolved_path(self):
        """The approved raw CSV file must exist at the resolved path."""
        self.assertTrue(get_raw_csv_path().is_file())

    def test_load_raw_dataset_via_existing_loader(self):
        """The approved file must load through the existing loader."""
        dataframe = load_raw_dataset()
        self.assertIsInstance(dataframe, pd.DataFrame)


class TestCsvLoading(unittest.TestCase):
    """Verify the approved CSV can be loaded into a DataFrame."""

    @classmethod
    def setUpClass(cls):
        """Load the approved CSV once for all loading tests."""
        cls.df = load_raw_dataset()

    def test_loads_dataframe(self):
        """The loader must return a pandas DataFrame."""
        self.assertIsInstance(self.df, pd.DataFrame)

    def test_has_expected_shape(self):
        """The DataFrame must have 541,909 rows and 8 columns."""
        self.assertEqual(
            self.df.shape,
            (EXPECTED_ROW_COUNT, EXPECTED_COLUMN_COUNT),
            f"Unexpected DataFrame shape: {self.df.shape}",
        )

    def test_expected_columns_present(self):
        """All 8 expected columns must exist in the DataFrame."""
        for column in EXPECTED_COLUMNS:
            with self.subTest(column=column):
                self.assertIn(column, self.df.columns)

    def test_has_exactly_eight_columns(self):
        """The DataFrame must contain exactly the 8 expected columns."""
        self.assertEqual(len(self.df.columns), EXPECTED_COLUMN_COUNT)


class TestDataTypeInspection(unittest.TestCase):
    """Verify the pandas dtypes of the DataFrame returned by load_raw_dataset()."""

    @classmethod
    def setUpClass(cls):
        """Load the approved CSV and inspect its dtypes once for all tests."""
        cls.df = load_raw_dataset()
        cls.observed = inspect_data_types(cls.df)

    def test_inspection_covers_eight_columns(self):
        """The dtype inspection must cover all 8 expected columns."""
        self.assertEqual(len(self.observed), EXPECTED_COLUMN_COUNT)
        self.assertEqual(set(self.observed), set(EXPECTED_COLUMNS))

    def test_observed_dtypes_match_expected_raw_dtypes(self):
        """Each observed dtype must match the expected raw-load dtype."""
        for column, expected in EXPECTED_RAW_DTYPES.items():
            with self.subTest(column=column):
                self.assertEqual(
                    self.observed[column],
                    expected,
                    f"Unexpected dtype for {column}: {self.observed[column]}",
                )

    def test_invoice_date_is_datetime64(self):
        """InvoiceDate must be parsed to datetime64 (not text) by the loader.

        Per the 4.2 correction decision, InvoiceDate is parsed to pandas
        datetime64 during CSV loading. The raw CSV file itself is unchanged.
        """
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(self.df["InvoiceDate"]),
            f"InvoiceDate is not datetime64: {self.observed['InvoiceDate']!r}",
        )
        self.assertEqual(self.observed["InvoiceDate"], "datetime64[us]")

    def test_at_least_one_valid_invoice_date_is_datetime(self):
        """At least one real InvoiceDate value must be an actual datetime."""
        first_value = self.df["InvoiceDate"].dropna().iloc[0]
        self.assertIsInstance(first_value, pd.Timestamp)
        self.assertNotIsInstance(first_value, str)

    def test_observed_dtypes_consistent_with_dictionary(self):
        """Observed types must match the Phase 3 data dictionary.

        After the 4.2 correction, InvoiceDate is parsed to datetime64 during
        loading, so all observed dtypes now match the dictionary. String
        columns are equivalent ('str' == 'object (str)').
        """
        for column in EXPECTED_COLUMNS:
            with self.subTest(column=column):
                observed = _dtype_category(self.observed[column])
                documented = _dtype_category(DOCUMENTED_DTYPES[column])
                self.assertEqual(
                    observed,
                    documented,
                    f"Dtype for {column} does not match the data dictionary: "
                    f"observed={self.observed[column]!r}, "
                    f"documented={DOCUMENTED_DTYPES[column]!r}",
                )


class TestRealCustomerVerification(unittest.TestCase):
    """Read-only verification using a real customer other than CustomerID 17850.

    Verifies (without any RFM calculation) that the chosen customer exists,
    has at least one transaction, and that their InvoiceDate values are parsed
    as real datetimes in the loaded DataFrame.
    """

    @classmethod
    def setUpClass(cls):
        """Load the dataset and select the verification customer's rows."""
        cls.df = load_raw_dataset()
        cls.customer_rows = cls.df[
            cls.df["CustomerID"] == VERIFICATION_CUSTOMER_ID
        ]

    def test_customer_exists(self):
        """The verification CustomerID must exist in the dataset."""
        self.assertIn(VERIFICATION_CUSTOMER_ID, set(self.df["CustomerID"]))
        self.assertGreater(len(self.customer_rows), 0)

    def test_customer_has_at_least_one_transaction(self):
        """The customer must have at least one transaction record."""
        self.assertGreaterEqual(len(self.customer_rows), 1)

    def test_customer_invoice_dates_are_datetime(self):
        """The customer's InvoiceDate values must parse to real datetimes."""
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(self.customer_rows["InvoiceDate"]),
        )
        self.assertTrue(
            self.customer_rows["InvoiceDate"].notna().all(),
            "Verification customer has missing InvoiceDate values.",
        )

    def test_customer_sample_rows(self):
        """A small factual sample must be available for the record."""
        sample = self.customer_rows[
            ["CustomerID", "InvoiceNo", "InvoiceDate"]
        ].head(3)
        self.assertEqual(len(sample), 3)
        self.assertTrue(sample["InvoiceDate"].notna().all())
        self.assertTrue(
            all(isinstance(value, pd.Timestamp) for value in sample["InvoiceDate"])
        )


class TestExceptionHandling(unittest.TestCase):
    """Verify loading failures raise clear, useful errors (Phase 4.4).

    Failure tests use temporary files and a mocked path so the approved raw
    dataset (data/raw/OnlineRetail.csv) is never modified or corrupted.
    """

    def test_normal_approved_csv_still_loads(self):
        """The approved CSV must still load successfully (4.1-4.3 intact)."""
        dataframe = load_raw_dataset()
        self.assertIsInstance(dataframe, pd.DataFrame)
        self.assertEqual(
            dataframe.shape,
            (EXPECTED_ROW_COUNT, EXPECTED_COLUMN_COUNT),
        )
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(dataframe["InvoiceDate"]),
        )

    def test_missing_file_raises_file_not_found(self):
        """A missing approved CSV must raise a clear FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_path = pathlib.Path(tmp_dir) / "missing.csv"
            with mock.patch(
                "src.data_loading.get_raw_csv_path",
                return_value=missing_path,
            ):
                with self.assertRaises(FileNotFoundError) as ctx:
                    load_raw_dataset()
            self.assertIn("not found", str(ctx.exception).lower())
            self.assertIn(str(missing_path), str(ctx.exception))

    def test_empty_csv_raises_useful_error(self):
        """An empty CSV must raise a clear, useful ValueError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            empty_path = pathlib.Path(tmp_dir) / "empty.csv"
            empty_path.write_bytes(b"")
            with mock.patch(
                "src.data_loading.get_raw_csv_path",
                return_value=empty_path,
            ):
                with self.assertRaises(ValueError) as ctx:
                    load_raw_dataset()
            self.assertIn("empty", str(ctx.exception).lower())
            self.assertEqual(ctx.exception.__cause__.__class__.__name__, "EmptyDataError")

    def test_unreadable_csv_raises_useful_error(self):
        """An unreadable/malformed CSV must raise a clear, useful ValueError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_path = pathlib.Path(tmp_dir) / "bad.csv"
            bad_path.write_bytes(b"\xff\xfe\xfa\x01not-a-valid-csv\xff")
            with mock.patch(
                "src.data_loading.get_raw_csv_path",
                return_value=bad_path,
            ):
                with self.assertRaises(ValueError) as ctx:
                    load_raw_dataset()
            self.assertIn("could not be read or parsed", str(ctx.exception).lower())
            self.assertIn(str(bad_path), str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
