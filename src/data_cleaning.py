"""
data_cleaning.py — Data Cleaning Module

Responsibility:
    Validate, clean, and prepare raw data for RFM analysis and produce the
    project working dataset in data/processed/.

Current status:
    PHASE 5.1 — Missing-value handling implemented.
    PHASE 5.2 — Exact-duplicate-record handling implemented.
    PHASE 5.3 — Invalid-data handling implemented.
    PHASE 5.4 — Filtering: owner-approved verification (NO ADDITIONAL
        FILTERING REQUIRED; 0 rows removed; no filtered dataset created).
    PHASE 5.5 — Transformation: owner-approved verification (NO ADDITIONAL
        TRANSFORMATION REQUIRED; 0 rows changed; no transformed dataset
        created; InvoiceDate datetime64 parsing remains Phase 4.2 behavior).
    PHASE 5.6 — Outlier Handling: owner-approved verification (NO ADDITIONAL
        OUTLIER HANDLING REQUIRED; 0 rows removed; no outlier dataset
        created; no statistical outlier method introduced).
    Missing-value, duplicate, invalid-data, filtering, transformation, and
    outlier-handling verification are implemented here; EDA/RFM/segmentation/
    statistics/visualization remain in later subphases.
    The raw CSV is never modified.
"""

import config
import hashlib
import pathlib
import pandas as pd

from src.data_loading import load_raw_dataset

# Name of the cleaned / working dataset produced in data/processed/ (Phase 5.1).
CLEANED_FILENAME = "OnlineRetail_cleaned.csv"
# Name of the deduplicated dataset produced in data/processed/ (Phase 5.2).
DEDUP_FILENAME = "OnlineRetail_deduplicated.csv"

def get_cleaned_dataset_path():
    """Return the resolved path to the working dataset in data/processed/.

    The cleaned/working dataset is always written to ``data/processed/``,
    never to ``data/raw/`` (the raw dataset is the immutable source of truth).

    Returns:
        pathlib.Path: The resolved path to the working dataset CSV.
    """
    return (config.PROCESSED_DATA_DIR / CLEANED_FILENAME).resolve()

def get_deduplicated_dataset_path():
    """Return the resolved path to the deduplicated dataset in data/processed/."""
    return (config.PROCESSED_DATA_DIR / DEDUP_FILENAME).resolve()


def _validate_output_path(output_path):
    """Reject save destinations inside the immutable raw-data directory."""
    resolved_path = pathlib.Path(output_path).resolve()
    raw_data_dir = pathlib.Path(config.RAW_DATA_DIR).resolve()
    try:
        resolved_path.relative_to(raw_data_dir)
    except ValueError:
        return resolved_path
    raise ValueError(
        f"Processed datasets cannot be written to the raw-data directory: "
        f"{resolved_path}"
    )


def save_working_dataset(dataframe=None, output_path=None):
    """Persist the cleaned/working dataset to data/processed/ only if explicitly requested."""
    if dataframe is None:
        dataframe = handle_missing_values(load_raw_dataset())
    if output_path is None:
        # Only write to permanent storage if explicitly called with output_path
        return None  # Do not persist by default
    output_path = _validate_output_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    return output_path


def save_deduplicated_dataset(dataframe=None, output_path=None):
    """Persist the Phase 5.2 deduplicated working dataset only if explicitly requested."""
    if dataframe is None:
        # Generate in-memory if no dataframe is provided
        temp_cleaned = handle_missing_values(load_raw_dataset())
        dataframe = remove_duplicates(temp_cleaned)
    else:
        dataframe = remove_duplicates(dataframe)
    if output_path is None:
        return None  # Do not persist by default
    output_path = _validate_output_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    return output_path


def get_missing_value_counts(dataframe):
    """Return missing-value counts for every column of ``dataframe``.

    Read-only inspection helper for Phase 5.1. The DataFrame is not modified.

    Args:
        dataframe (pandas.DataFrame): A DataFrame to inspect.

    Returns:
        pandas.Series: Missing-value count per column.
    """
    return dataframe.isna().sum()


def handle_missing_values(dataframe):
    """Handle missing values in the Online Retail working dataset (Phase 5.1).

    Documented decision (from the actual dataset and the Phase 2/3 requirements):
    - **Description**: 1,454 missing values (0.2683%). **Not imputed** — there
      is no valid source for the real product text, and inventing a value would
      fabricate data (explicitly disallowed). **Rows not removed** — the
      affected rows carry valid CustomerID, InvoiceDate, Quantity and
      UnitPrice needed for later RFM analysis, and there is no documented
      project reason to drop them. Missing values are therefore **preserved as
      NaN**.
    - **CustomerID**: 0 missing — not applicable; must never be fabricated.
    - **All other columns** (InvoiceNo, StockCode, Quantity, InvoiceDate,
      UnitPrice, Country): 0 missing — no action.

    This function does NOT remove duplicates, remove/cancel rows, correct
    negatives, or otherwise transform the data; it records and applies the
    documented missing-value decision and returns a clean working copy.
    (InvoiceDate is already parsed as datetime64 during Phase 4 loading.)
    The raw CSV is never modified.

    Args:
        dataframe (pandas.DataFrame): The loaded (raw) DataFrame.

    Returns:
        pandas.DataFrame: A working copy with missing values handled per the
            documented decision above (Description NaN preserved).
    """
    missing_counts = get_missing_value_counts(dataframe)

    # Guardrail: CustomerID must never be fabricated, and no required RFM
    # fields may be missing. These assertions encode the project requirements.
    if missing_counts["CustomerID"] != 0:
        raise ValueError(
            "CustomerID must not have missing values; refusal to fabricate "
            f"identifiers (missing: {missing_counts['CustomerID']})."
        )
    for required in ("InvoiceDate", "Quantity", "UnitPrice", "InvoiceNo"):
        if missing_counts[required] != 0:
            raise ValueError(
                f"Required field {required!r} has missing values "
                f"({missing_counts[required]}); refusing to handle silently."
            )

    # Decision: preserve Description NaN (do not impute invented text, do not
    # remove rows). Return a working copy, leaving the raw data untouched.
    working = dataframe.copy()
    return working





# Name of the deduplicated working dataset produced in data/processed/ (Phase 5.2).
DEDUP_FILENAME = "OnlineRetail_deduplicated.csv"


def get_deduplicated_dataset_path():
    """Return the resolved path to the deduplicated working dataset.

    The 5.2 deduplicated dataset is always written to ``data/processed/``,
    never to ``data/raw/`` (the raw dataset is the immutable source of truth).

    Returns:
        pathlib.Path: The resolved path to the deduplicated working dataset.
    """
    return (config.PROCESSED_DATA_DIR / DEDUP_FILENAME).resolve()


def get_duplicate_count(dataframe):
    """Return the number of exact-duplicate rows in ``dataframe``.

    Read-only inspection helper for Phase 5.2. "Exact duplicate" means a fully
    identical row (all columns equal) to an earlier row. The DataFrame is not
    modified.

    Args:
        dataframe (pandas.DataFrame): A DataFrame to inspect.

    Returns:
        int: The count of exact-duplicate rows (``duplicated().sum()``).
    """
    return int(dataframe.duplicated(keep="first").sum())


def remove_duplicates(dataframe):
    """Remove exact-duplicate rows from ``dataframe`` (Phase 5.2).

    Removes **only exact duplicate rows** (rows identical across all columns to
    an earlier row), keeping the first occurrence of each duplicated group and
    preserving the original row order. This is the ONLY change applied: no
    negative-value handling, no cancellation handling, no filtering, no
    transformation, no outlier handling, no aggregation.

    Args:
        dataframe (pandas.DataFrame): The Phase 5.1 (or other) working dataset.

    Returns:
        pandas.DataFrame: A copy with exact-duplicate rows removed and a fresh
            range index. Non-duplicate rows are preserved verbatim.
    """
    keep_mask = ~dataframe.duplicated(keep="first")
    deduplicated = dataframe.loc[keep_mask].copy()
    deduplicated.reset_index(drop=True, inplace=True)
    return deduplicated





# Name of the invalid-data-cleaned working dataset produced in data/processed/
# (Phase 5.3). The 5.2 deduplicated dataset is left untouched for traceability.
INVALID_REMOVED_FILENAME = "OnlineRetail_invalid_removed.csv"


def get_invalid_removed_dataset_path():
    """Return the resolved path to the Phase 5.3 cleaned working dataset.

    The 5.3 working dataset is always written to ``data/processed/``, never to
    ``data/raw/`` (the raw dataset is the immutable source of truth). The 5.2
    deduplicated dataset is left untouched for traceability.

    Returns:
        pathlib.Path: The resolved path to the 5.3 working dataset.
    """
    return (config.PROCESSED_DATA_DIR / INVALID_REMOVED_FILENAME).resolve()


def is_cancellation_invoice(dataframe):
    """Return a boolean mask for cancellation/return invoices (Phase 5.3).

    A cancellation invoice is one whose ``InvoiceNo`` starts with ``"C"``
    (return/cancellation transactions, not completed sales).

    Args:
        dataframe (pandas.DataFrame): The working dataset.

    Returns:
        pandas.Series[bool]: True for cancellation-invoice rows.
    """
    return dataframe["InvoiceNo"].astype(str).str.startswith("C")


def is_invalid_record(dataframe):
    """Return a boolean mask of records considered INVALID for 5.3 removal.

    Removal criteria (union; no double counting — see overlaps below):
    R1 — Cancellation/return invoices (InvoiceNo starts with ``"C"``); returns
         are not completed sales and carry negative Quantity/negative monetary
         as the return mechanism.
    R2 — Non-positive Quantity on NON-cancellation invoices (Quantity <= 0
         with no leading-"C" InvoiceNo): a genuine data anomaly.
    R3 — Non-positive UnitPrice (UnitPrice <= 0): a sale must have a positive
         unit price; zero/negative price is a data error.

    Data-logic (recalculated on the 5.2 input): every cancellation invoice has
    Quantity < 0, so cancellations are removed via R1 (InvoiceNo status), NOT
    via a blind "negative quantity" rule. All non-cancellation Quantity<=0 rows
    also have UnitPrice<=0 (R2 is a subset of R3), and cancellations have
    UnitPrice>0 (R1 is disjoint from R3). Therefore negative Quantity is never
    removed as a standalone criterion, and the criteria never double count.

    Args:
        dataframe (pandas.DataFrame): The working dataset.

    Returns:
        pandas.Series[bool]: True for records to be removed as invalid.
    """
    cancel_mask = is_cancellation_invoice(dataframe)
    nonpositive_quantity = dataframe["Quantity"] <= 0
    nonpositive_price = dataframe["UnitPrice"] <= 0
    return cancel_mask | (nonpositive_quantity & ~cancel_mask) | nonpositive_price


def remove_invalid_records(dataframe):
    """Remove genuinely invalid transaction records (Phase 5.3).

    Applies the Phase 5.3 invalid-data mask (``is_invalid_record``) and returns
    a copy of ``dataframe`` with the invalid rows dropped. Only the three
    approved invalid-data rules are applied (no outlier handling, no
    transformation, no aggregation, no EDA):

    R1 — Cancellation/return invoices (``InvoiceNo`` starts with ``C``).
    R2 — Non-positive ``Quantity`` on NON-cancellation invoices (``Quantity<=0``
         on a non-C invoice): a genuine data anomaly.
    R3 — Non-positive ``UnitPrice`` (``UnitPrice<=0``): a sale must have a
         positive unit price; zero/negative price is a data error.

    The mask is a union with no double counting (cancellations are removed via
    R1 / InvoiceNo status — NOT via a blind negative-quantity rule; R2 is a
    subset of R3; R1 is disjoint from R3). See ``is_invalid_record`` for the
    recalculated data-logic confirmation.

    ``Quantity`` is never removed solely because it is negative: cancellation
    negative quantities are handled by R1 (InvoiceNo status), and non-cancellation
    negative quantities additionally carry ``UnitPrice<=0`` so they are also
    captured by R3. No row is counted twice.

    Args:
        dataframe (pandas.DataFrame): The Phase 5.2 working dataset.

    Returns:
        pandas.DataFrame: A copy with invalid records removed and a fresh
            range index. Valid (non-invalid) rows are preserved verbatim.
    """
    invalid_mask = is_invalid_record(dataframe)
    kept = dataframe.loc[~invalid_mask].copy()
    kept.reset_index(drop=True, inplace=True)
    return kept


def save_invalid_removed_dataset(dataframe=None, output_path=None):
    """Persist the Phase 5.3 invalid-data-cleaned working dataset.

    Writes ``data/processed/OnlineRetail_invalid_removed.csv`` by default (never
    ``data/raw/``). If ``dataframe`` is not supplied, the Phase 5.2 processed
    dataset (``data/processed/OnlineRetail_deduplicated.csv``) is loaded and
    invalid records are removed first. The 5.2 deduplicated dataset is left
    untouched for traceability.

    Args:
        dataframe (pandas.DataFrame | None): The DataFrame to clean/write.
        output_path (pathlib.Path | str | None): Optional explicit output path.

    Returns:
        pathlib.Path: The resolved path the 5.3 working dataset was written to.
    """
    if dataframe is None:
        dataframe = remove_invalid_records(
            pd.read_csv(get_deduplicated_dataset_path(), parse_dates=["InvoiceDate"])
        )
    else:
        dataframe = remove_invalid_records(dataframe)
    if output_path is None:
        output_path = get_invalid_removed_dataset_path()
    output_path = _validate_output_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    return output_path


# ---------------------------------------------------------------------------
# Phase 5.4 — Filtering (owner-approved verification: NO ADDITIONAL FILTERING
# REQUIRED). No operational filtering rule beyond the 5.3 invalid-data handling
# is approved, so 5.4 is a verification-only subphase: it removes 0 rows, never
# writes a filtered copy, and never modifies the 5.3 working dataset.
# ---------------------------------------------------------------------------
NO_ADDITIONAL_FILTERING_REQUIRED = "NO ADDITIONAL FILTERING REQUIRED"

# Approved columns of the project working dataset (Phase 3.3 data dictionary).
APPROVED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


def verify_no_additional_filtering(dataframe=None):
    """Verify the 5.3 working dataset requires NO additional filtering (Phase 5.4).

    Owner-approved Subphase 5.4 decision: no additional operational filtering
    rule exists in the approved requirements / WBS, so 5.4 introduces NO row
    removal and creates NO filtered copy. This read-only verification confirms
    that the Phase 5.3 working dataset is already the complete valid transaction
    population retained for later RFM analysis:

      1. the 5.3 working dataset file exists;
      2. every approved project column is present (none removed / added);
      3. ``CustomerID`` has 0 missing values (identifiers are never fabricated);
      4. there are 0 exact-duplicate rows;
      5. the invalid categories already handled by 5.3 remain absent
         (no cancellation invoices, no non-positive ``Quantity``, no
         non-positive ``UnitPrice``);
      6. no additional project-approved filtering criterion exists.

    The DataFrame is never modified and no filtered copy is ever written here,
    so the rows-removed count for 5.4 is always 0 and the row count is identical
    before and after this verification.

    Args:
        dataframe (pandas.DataFrame | None): Optional DataFrame to verify. If
            None, the Phase 5.3 working dataset
            (``data/processed/OnlineRetail_invalid_removed.csv``) is loaded
            read-only.

    Returns:
        dict: A verification result whose ``decision`` equals
            ``NO_ADDITIONAL_FILTERING_REQUIRED`` and whose ``rows_removed``
            equals 0, along with the observed check values.
    """
    if dataframe is None:
        source_path = get_invalid_removed_dataset_path()
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Phase 5.3 working dataset not found for 5.4 verification: "
                f"{source_path}"
            )
        source = "data/processed/" + source_path.name
        dataframe = pd.read_csv(source_path, parse_dates=["InvoiceDate"])
    else:
        source = "in-memory"

    missing_columns = [
        column for column in APPROVED_COLUMNS if column not in dataframe.columns
    ]
    unexpected_columns = [
        column for column in dataframe.columns if column not in APPROVED_COLUMNS
    ]
    if missing_columns:
        missing_customer_id = None
        duplicate_rows = None
        invalid_rows_remaining = None
    else:
        missing_customer_id = int(dataframe["CustomerID"].isna().sum())
        duplicate_rows = get_duplicate_count(dataframe)
        invalid_rows_remaining = int(is_invalid_record(dataframe).sum())

    verified = (
        (not missing_columns)
        and (not unexpected_columns)
        and missing_customer_id == 0
        and duplicate_rows == 0
        and invalid_rows_remaining == 0
    )

    return {
        "source": source,
        "verified": verified,
        "row_count": int(len(dataframe)),
        "rows_removed": 0,
        "columns": list(dataframe.columns),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "missing_customer_id": missing_customer_id,
        "duplicate_rows": duplicate_rows,
        "invalid_rows_remaining": invalid_rows_remaining,
        "decision": NO_ADDITIONAL_FILTERING_REQUIRED,
    }


# ---------------------------------------------------------------------------
# Phase 5.5 — Transformation (owner-approved verification: NO ADDITIONAL
# TRANSFORMATION REQUIRED). No operational transformation rule beyond the
# already-approved Phase 4.2 InvoiceDate parsing-at-load is defined in the
# approved requirements / WBS, so 5.5 is a verification-only subphase: it
# changes 0 rows, never writes a transformed copy, and never modifies the
# 5.3 working dataset.
# ---------------------------------------------------------------------------
NO_ADDITIONAL_TRANSFORMATION_REQUIRED = "NO ADDITIONAL TRANSFORMATION REQUIRED"

TRANSFORMED_FILENAME = "OnlineRetail_transformed.csv"


def verify_no_additional_transformation(dataframe=None):
    """Verify the 5.3 working dataset requires NO additional transformation.

    Owner-approved Subphase 5.5 decision: no additional transformation rule
    exists in the approved requirements / WBS, so Subphase 5.5 TRANSFORMATION
    is a verification / "NO ADDITIONAL TRANSFORMATION REQUIRED" subphase.
    ``InvoiceDate -> datetime64`` was already implemented and approved as
    Phase 4.2 CSV loading/parsing and must NOT be moved or duplicated here.
    This read-only verification confirms, on the Phase 5.3 working dataset:

      1. the 5.3 working dataset file exists;
      2. every approved project column is present (schema unchanged);
      3. ``InvoiceDate`` is ``datetime64``;
      4. ``Quantity`` is an appropriate numeric/integer dtype;
      5. ``UnitPrice`` is an appropriate numeric/float dtype;
      6. ``CustomerID`` is an appropriate numeric/integer dtype;
      7. no additional project-approved transformation criterion exists.

    The DataFrame is never modified and no transformed copy is ever written
    here, so the rows-changed count for 5.5 is always 0 and the row count is
    identical before and after this verification.

    Args:
        dataframe (pandas.DataFrame | None): Optional DataFrame to verify. If
            None, the Phase 5.3 working dataset
            (``data/processed/OnlineRetail_invalid_removed.csv``) is loaded
            read-only.

    Returns:
        dict: A verification result whose ``decision`` equals
            ``NO_ADDITIONAL_TRANSFORMATION_REQUIRED`` and whose
            ``rows_changed`` equals 0, along with the observed check values.
    """
    expected_dtype_kinds = {
        "InvoiceDate": lambda dtype: pd.api.types.is_datetime64_any_dtype(dtype),
        "Quantity": pd.api.types.is_integer_dtype,
        "UnitPrice": pd.api.types.is_numeric_dtype,
        "CustomerID": pd.api.types.is_integer_dtype,
    }

    if dataframe is None:
        source_path = get_invalid_removed_dataset_path()
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Phase 5.3 working dataset not found for 5.5 verification: "
                f"{source_path}"
            )
        source = "data/processed/" + source_path.name
        dataframe = pd.read_csv(source_path, parse_dates=["InvoiceDate"])
    else:
        source = "in-memory"

    missing_columns = [
        column for column in APPROVED_COLUMNS if column not in dataframe.columns
    ]
    unexpected_columns = [
        column for column in dataframe.columns if column not in APPROVED_COLUMNS
    ]

    observed_dtypes = None
    dtype_issues = None
    if not missing_columns:
        observed_dtypes = {
            column: str(dtype) for column, dtype in dataframe.dtypes.items()
        }
        dtype_issues = [
            column
            for column, checker in expected_dtype_kinds.items()
            if not checker(dataframe[column].dtype)
        ]

    verified = (
        (not missing_columns)
        and (not unexpected_columns)
        and (not dtype_issues)
    )

    return {
        "source": source,
        "verified": verified,
        "row_count": int(len(dataframe)),
        "rows_changed": 0,
        "columns": list(dataframe.columns),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "observed_dtypes": observed_dtypes,
        "dtype_issues": dtype_issues,
        "decision": NO_ADDITIONAL_TRANSFORMATION_REQUIRED,
    }


# ---------------------------------------------------------------------------
# Phase 5.6 — Outlier Handling (owner-approved verification: NO ADDITIONAL
# OUTLIER HANDLING REQUIRED). No statistical outlier rule (IQR, z-score,
# percentile, capping, etc.) exists in the approved requirements / WBS, so
# 5.6 is a verification-only subphase: it removes 0 rows, never writes an
# outlier dataset, and never modifies the 5.3 working dataset or its
# already-approved invalid-category guarantees.
# ---------------------------------------------------------------------------
NO_ADDITIONAL_OUTLIER_HANDLING_REQUIRED = "NO ADDITIONAL OUTLIER HANDLING REQUIRED"

OUTLIER_REMOVED_FILENAME = "OnlineRetail_outlier_removed.csv"
OUTLIERS_FILENAME = "OnlineRetail_outliers.csv"


def verify_no_additional_outlier_handling(dataframe=None):
    """Verify the 5.3 working dataset requires NO additional outlier handling.

    Owner-approved Subphase 5.6 decision: no statistical outlier rule exists
    in the approved requirements / WBS, so Subphase 5.6 OUTLIER HANDLING is a
    verification / "NO ADDITIONAL OUTLIER HANDLING REQUIRED" subphase. This
    read-only verification confirms, on the Phase 5.3 working dataset:

      1. the 5.3 working dataset file exists;
      2. every approved project column is present (schema unchanged) with
         appropriate dtypes;
      3. ``CustomerID`` has 0 missing values (identifiers never fabricated);
      4. there are 0 exact-duplicate rows;
      5. the invalid categories already handled by 5.3 remain absent
         (no cancellation invoices, no ``Quantity <= 0``, no
         ``UnitPrice <= 0``);
      6. row count is identical before and after (no rows removed).

    No statistical outlier method is applied, the DataFrame is never modified,
    and no outlier dataset is ever written here, so ``rows_removed`` is always
    0.

    Args:
        dataframe (pandas.DataFrame | None): Optional DataFrame to verify. If
            None, the Phase 5.3 working dataset
            (``data/processed/OnlineRetail_invalid_removed.csv``) is loaded
            read-only.

    Returns:
        dict: A verification result whose ``decision`` equals
            ``NO_ADDITIONAL_OUTLIER_HANDLING_REQUIRED`` and whose
            ``rows_removed`` equals 0, along with the observed check values.
    """
    expected_dtypes = {
        "InvoiceDate": lambda dtype: pd.api.types.is_datetime64_any_dtype(dtype),
        "Quantity": lambda dtype: (
            pd.api.types.is_integer_dtype(dtype)
            or pd.api.types.is_numeric_dtype(dtype)
        ),
        "UnitPrice": lambda dtype: pd.api.types.is_numeric_dtype(dtype),
        "CustomerID": lambda dtype: (
            pd.api.types.is_integer_dtype(dtype)
            or pd.api.types.is_numeric_dtype(dtype)
        ),
    }
    text_columns = ("InvoiceNo", "StockCode", "Description", "Country")

    def _is_text_compatible(dtype):
        return not (
            pd.api.types.is_numeric_dtype(dtype)
            or pd.api.types.is_datetime64_any_dtype(dtype)
            or pd.api.types.is_bool_dtype(dtype)
        )

    if dataframe is None:
        source_path = get_invalid_removed_dataset_path()
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Phase 5.3 working dataset not found for 5.6 verification: "
                f"{source_path}"
            )
        source = "data/processed/" + source_path.name
        dataframe = pd.read_csv(source_path, parse_dates=["InvoiceDate"])
    else:
        source = "in-memory"

    rows_before = int(len(dataframe))

    missing_columns = [
        column for column in APPROVED_COLUMNS if column not in dataframe.columns
    ]
    unexpected_columns = [
        column for column in dataframe.columns if column not in APPROVED_COLUMNS
    ]

    observed_dtypes = None
    dtype_issues = None
    missing_customer_id = None
    duplicate_rows = None
    invalid_rows_remaining = None
    if not missing_columns:
        observed_dtypes = {
            column: str(dtype) for column, dtype in dataframe.dtypes.items()
        }
        dtype_issues = [
            column
            for column, checker in expected_dtypes.items()
            if not checker(dataframe[column].dtype)
        ] + [
            column
            for column in text_columns
            if not _is_text_compatible(dataframe[column].dtype)
        ]
        missing_customer_id = int(dataframe["CustomerID"].isna().sum())
        duplicate_rows = get_duplicate_count(dataframe)
        invalid_rows_remaining = int(is_invalid_record(dataframe).sum())

    verified = (
        (not missing_columns)
        and (not unexpected_columns)
        and (not dtype_issues)
        and missing_customer_id == 0
        and duplicate_rows == 0
        and invalid_rows_remaining == 0
    )

    return {
        "source": source,
        "verified": verified,
        "rows_before": rows_before,
        "rows_after": int(len(dataframe)),
        "rows_removed": 0,
        "columns": list(dataframe.columns),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "observed_dtypes": observed_dtypes,
        "dtype_issues": dtype_issues,
        "missing_customer_id": missing_customer_id,
        "duplicate_rows": duplicate_rows,
        "invalid_rows_remaining": invalid_rows_remaining,
        "decision": NO_ADDITIONAL_OUTLIER_HANDLING_REQUIRED,
    }


# ---------------------------------------------------------------------------
# Phase 5.7 — Aggregation (owner-approved verification: NO ADDITIONAL
# AGGREGATION REQUIRED). Customer-level aggregation is deferred to Phase 7,
# so 5.7 is a minimal read-only validation: it confirms the 5.3 transaction-
# level dataset remains unchanged and no aggregation output is produced.
# ---------------------------------------------------------------------------
NO_ADDITIONAL_AGGREGATION_REQUIRED = "NO ADDITIONAL AGGREGATION REQUIRED"


def verify_no_additional_aggregation(dataframe=None):
    """Verify the 5.3 working dataset requires NO additional aggregation.

    Owner-approved Subphase 5.7 decision: customer-level aggregation is
    intentionally deferred to Phase 7, where the exact RFM methodology will be
    legally defined. This read-only verification therefore confirms only that
    the current transaction-level working population remains valid and that this
    Phase 5 stage does not create or apply any aggregation.

    The function never mutates the input DataFrame, never writes a file, never
    groups by CustomerID, never creates an aggregated CSV, and never calculates
    RFM metrics. It only validates the approved 8-column schema and the
    transaction-level state of the working dataset.

    Args:
        dataframe (pandas.DataFrame | None): Optional input DataFrame to verify.
            If None, the approved 5.3 working dataset
            (``data/processed/OnlineRetail_invalid_removed.csv``) is loaded.

    Returns:
        dict: A verification result with ``decision`` set to
            ``NO_ADDITIONAL_AGGREGATION_REQUIRED`` and evidence of the row
            count, schema, and transaction-level state.
    """
    if dataframe is None:
        source_path = get_invalid_removed_dataset_path()
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Phase 5.3 working dataset not found for 5.7 verification: "
                f"{source_path}"
            )
        source = "data/processed/" + source_path.name
        dataframe = pd.read_csv(source_path, parse_dates=["InvoiceDate"])
    else:
        source = "in-memory"

    row_count = int(len(dataframe))
    missing_columns = [
        column for column in APPROVED_COLUMNS if column not in dataframe.columns
    ]
    unexpected_columns = [
        column for column in dataframe.columns if column not in APPROVED_COLUMNS
    ]
    missing_customer_id = None
    observed_dtypes = None
    transaction_level = False
    customer_level_aggregation_applied = False

    if not missing_columns:
        missing_customer_id = int(dataframe["CustomerID"].isna().sum())
        observed_dtypes = {
            column: str(dtype) for column, dtype in dataframe.dtypes.items()
        }
        transaction_level = (
            list(dataframe.columns) == APPROVED_COLUMNS
            and row_count == len(dataframe)
            and "Frequency" not in dataframe.columns
            and "Monetary" not in dataframe.columns
            and "Recency" not in dataframe.columns
        )
        customer_level_aggregation_applied = False

    verified = (
        (not missing_columns)
        and (not unexpected_columns)
        and missing_customer_id == 0
        and transaction_level
        and (not customer_level_aggregation_applied)
    )

    return {
        "source": source,
        "verified": verified,
        "row_count": row_count,
        "rows_before": row_count,
        "rows_after": row_count,
        "columns": list(dataframe.columns),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "missing_customer_id": missing_customer_id,
        "observed_dtypes": observed_dtypes,
        "transaction_level": transaction_level,
        "customer_level_aggregation_applied": customer_level_aggregation_applied,
        "decision": NO_ADDITIONAL_AGGREGATION_REQUIRED,
    }


# ---------------------------------------------------------------------------
# Phase 5.8 — Final Validation (owner-approved final validation gate).
# This is a read-only verification that confirms the approved Phase 5 working
# dataset still matches the earlier 5.1–5.7 outcomes and that no new cleaning,
# filtering, transformation, outlier, or aggregation operation has occurred.
# ---------------------------------------------------------------------------
PHASE_5_FINAL_VALIDATION_PASSED = "PHASE 5 FINAL VALIDATION PASSED"


def verify_phase5_final_validation(dataframe=None):
    """Perform the final Phase 5 read-only validation gate.

    This validation is not a new cleaning routine. It confirms that the final
    Phase 5 working dataset remains the approved transaction-level population
    produced by 5.1–5.3 and that no 5.4–5.7 decisions have been violated.

    The function loads the approved 5.3 working dataset when ``dataframe`` is not
    supplied, checks the exact schema and dtypes, confirms missing-value and
    duplicate/invalid conditions remain compliant, verifies the transaction-level
    structure and 524,878 row count, confirms no output is created, and checks
    raw-data integrity without mutating the input DataFrame.

    Args:
        dataframe (pandas.DataFrame | None): Optional DataFrame to validate. If
            None, the final Phase 5 working dataset is loaded from
            ``data/processed/OnlineRetail_invalid_removed.csv``.

    Returns:
        dict: Structured validation evidence and decision.
    """
    source_path = get_invalid_removed_dataset_path()
    if dataframe is None:
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Phase 5 working dataset not found for final validation: "
                f"{source_path}"
            )
        source = "data/processed/" + source_path.name
        dataframe = pd.read_csv(source_path, parse_dates=["InvoiceDate"])
    else:
        source = "in-memory"

    rows_before = int(len(dataframe))
    rows_after = rows_before
    rows_removed = 0
    rows_changed = 0

    missing_columns = [
        column for column in APPROVED_COLUMNS if column not in dataframe.columns
    ]
    unexpected_columns = [
        column for column in dataframe.columns if column not in APPROVED_COLUMNS
    ]

    schema_valid = (not missing_columns) and (not unexpected_columns)
    dtypes_valid = False
    customerid_valid = False
    duplicates_valid = False
    invalid_records_valid = False
    transaction_level_valid = False
    no_new_operation_valid = False
    raw_integrity_valid = False

    if schema_valid:
        dtypes_valid = (
            pd.api.types.is_datetime64_any_dtype(dataframe["InvoiceDate"].dtype)
            and (
                pd.api.types.is_integer_dtype(dataframe["Quantity"])
                or pd.api.types.is_numeric_dtype(dataframe["Quantity"])
            )
            and pd.api.types.is_numeric_dtype(dataframe["UnitPrice"])
            and (
                pd.api.types.is_integer_dtype(dataframe["CustomerID"])
                or pd.api.types.is_numeric_dtype(dataframe["CustomerID"])
            )
        )
        customerid_valid = int(dataframe["CustomerID"].isna().sum()) == 0
        duplicates_valid = int(dataframe.duplicated().sum()) == 0
        invalid_records_valid = (
            int(dataframe["InvoiceNo"].astype(str).str.startswith("C").sum()) == 0
            and int((dataframe["Quantity"] <= 0).sum()) == 0
            and int((dataframe["UnitPrice"] <= 0).sum()) == 0
        )
        row_count_requirement = (
            rows_before == 524_878 if source == "data/processed/OnlineRetail_invalid_removed.csv" else True
        )
        transaction_level_valid = (
            list(dataframe.columns) == APPROVED_COLUMNS
            and row_count_requirement
            and "Frequency" not in dataframe.columns
            and "Monetary" not in dataframe.columns
            and "Recency" not in dataframe.columns
        )
        no_new_operation_valid = (
            rows_removed == 0
            and rows_changed == 0
            and not any(
                filename in {"OnlineRetail_aggregated.csv",
                              "OnlineRetail_customer_aggregated.csv",
                              "OnlineRetail_rfm.csv"}
                for filename in [p.name for p in config.PROCESSED_DATA_DIR.glob("*.csv")]
            )
        )

        raw_path = pathlib.Path(config.RAW_DATA_DIR) / "OnlineRetail.csv"
        raw_integrity_valid = (
            raw_path.is_file()
            and raw_path.stat().st_size == 47_901_468
            and hashlib.sha256(raw_path.read_bytes()).hexdigest().upper()
            == "BFA47136118BC854A31E69D5C9E9689A2D07B73909F253679F2CC85EC4EB84EB"
        )

    verified = (
        schema_valid
        and dtypes_valid
        and customerid_valid
        and duplicates_valid
        and invalid_records_valid
        and transaction_level_valid
        and no_new_operation_valid
        and raw_integrity_valid
    )

    return {
        "source": source,
        "verified": verified,
        "decision": PHASE_5_FINAL_VALIDATION_PASSED if verified else "PHASE 5 FINAL VALIDATION FAILED",
        "input_path": str(source_path),
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_removed,
        "rows_changed": rows_changed,
        "schema_valid": schema_valid,
        "dtypes_valid": dtypes_valid,
        "customerid_valid": customerid_valid,
        "duplicates_valid": duplicates_valid,
        "invalid_records_valid": invalid_records_valid,
        "transaction_level_valid": transaction_level_valid,
        "no_new_operation_valid": no_new_operation_valid,
        "raw_integrity_valid": raw_integrity_valid,
        "row_count": rows_after,
        "columns": list(dataframe.columns),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
    }