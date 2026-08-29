"""
data_loading.py — Data Loading Module

Responsibility:
    Load the approved dataset from data/raw/ into a pandas DataFrame.

    - Expected input: approved dataset in data/raw/
    - Output: loaded DataFrame for downstream processing

Current status:
    PHASE 4.1 — CSV loading implemented for the approved dataset.
    PHASE 4.2 — Data type inspection implemented.
    PHASE 4.2 CORRECTION — InvoiceDate is now parsed to pandas datetime64
    during CSV loading (project decision; see README SUBPHASE 4.2 CORRECTION).
    PHASE 4.3 — File handling implemented (approved path resolution and
    existence verification before loading).
    PHASE 4.4 — Exception handling implemented for loading failures (missing
    file, empty file, read/parse failures) with clear, useful errors.
    Loads data/raw/OnlineRetail.csv into a pandas DataFrame and inspects the
    observed column dtypes. No cleaning, deduplication, negative-value
    handling, or other transformation is performed here (those belong to
    later phases).
"""

import pandas as pd

import config

# Official approved project dataset (Phase 3 approval).
# Dataset selection is deliberately NOT stored in config.py (it holds only
# path constants); the approved filename is therefore defined here.
DATASET_FILENAME = "OnlineRetail.csv"

# Column parsed to pandas datetime64 during CSV loading (4.2 correction).
# The raw CSV file itself is never modified.
DATETIME_COLUMNS = ["InvoiceDate"]


def get_raw_csv_path():
    """Return the resolved path to the approved raw CSV dataset.

    Resolves ``config.RAW_DATA_DIR / DATASET_FILENAME`` (Phase 4.3 file
    handling). Keeps the dataset filename handling consistent with the
    approved ``OnlineRetail.csv``.

    Returns:
        pathlib.Path: The resolved path to the approved raw CSV.
    """
    return (config.RAW_DATA_DIR / DATASET_FILENAME).resolve()


def load_raw_dataset():
    """Load the approved raw CSV dataset into a pandas DataFrame.

    Loads ``data/raw/OnlineRetail.csv`` (using the project's centralized
    ``config.RAW_DATA_DIR``) with pandas and returns the resulting DataFrame.
    The approved file path is resolved and verified to exist before loading
    (Phase 4.3 file handling).

    The raw CSV file is never modified. ``InvoiceDate`` is parsed to pandas
    ``datetime64`` in the returned DataFrame (per the 4.2 correction
    decision). No cleaning, no removal of duplicates, no handling of negative
    values, and no other transformation or analysis is performed.

    Exception handling (Phase 4.4): loading failures are surfaced clearly
    rather than hidden —
      - a missing approved CSV raises ``FileNotFoundError``;
      - an empty approved CSV raises ``ValueError``;
      - unreadable / malformed CSV content raises ``ValueError``;
    every case preserves the original error via exception chaining, and an
    empty DataFrame is never silently returned.

    Returns:
        pandas.DataFrame: The loaded OnlineRetail.csv contents with
            ``InvoiceDate`` as ``datetime64``.
    """
    csv_path = get_raw_csv_path()
    if not csv_path.is_file():
        raise FileNotFoundError(f"Approved raw CSV not found: {csv_path}")
    try:
        return pd.read_csv(csv_path, parse_dates=DATETIME_COLUMNS)
    except pd.errors.EmptyDataError as err:
        raise ValueError(
            f"Approved raw CSV is empty and cannot be loaded: {csv_path}"
        ) from err
    except (OSError, ValueError) as err:
        raise ValueError(
            f"Approved raw CSV could not be read or parsed: {csv_path}"
        ) from err


def inspect_data_types(dataframe):
    """Return the observed pandas dtype of every column in ``dataframe``.

    This is a read-only inspection helper for Phase 4.2. It reads the pandas
    dtype of each column and returns a mapping of column name to its dtype
    name (e.g. ``{"InvoiceNo": "str", "Quantity": "int64"}``).

    The DataFrame is NOT modified, converted, cleaned, or transformed.

    Args:
        dataframe (pandas.DataFrame): A DataFrame to inspect.

    Returns:
        dict: Mapping of ``{column_name: dtype_name}`` for every column.
    """
    return {column: str(dtype) for column, dtype in dataframe.dtypes.items()}
