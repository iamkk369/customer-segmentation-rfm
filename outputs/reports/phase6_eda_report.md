# Phase 6 — Exploratory Data Analysis Report

Source of every number below: verified against the real project data by running
the Phase 6 helpers (`build_phase6_eda_summary()` and related functions in
`src/statistics_analysis.py`) over the approved working dataset
`data/processed/OnlineRetail_invalid_removed.csv`. Nothing is estimated or invented.

## Dataset Overview

| Property | Verified value |
|---|---|
| Raw dataset | `data/raw/OnlineRetail.csv` — 541,909 rows × 8 columns |
| Working dataset analyzed here | `data/processed/OnlineRetail_invalid_removed.csv` — 524,878 rows × 8 columns |
| Columns | InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country |
| Unique customers | 4,338 |
| Unique invoices | 19,960 |
| Countries represented | 38 |
| Observation window | 2010-12-01 08:26 (UTC parse) → 2011-12-09 12:50 |
| Total transaction revenue (Σ Quantity × UnitPrice) | £10,642,110.80 |
| Average quantity per transaction line | 10.62 items |
| Average unit price | £3.92 |

InvoiceDate was parsed to datetime64 during loading (Phase 4.2) and remains
datetime-typed throughout EDA.

## Data Quality Findings

- All eight approved project columns survived every cleaning stage unchanged —
  no column loss or addition anywhere in the chain.
- The only tolerated gap is a free-text field (Description, see below); every
  analytically required field (InvoiceNo, InvoiceDate, Quantity, UnitPrice,
  CustomerID) is fully populated in the working dataset.
- Exact-duplicate rows were eliminated at Phase 5.2, and zero duplicates remain
  in the working dataset (re-verified by `verify_no_additional_filtering()`,
  which also confirms 0 rows required any further filtering).
- Invalid transaction categories (cancellations, non-positive quantities/prices)
  were removed at Phase 5.3; none remain (same verification).
- Phases 5.4–5.6 (filtering, transformation, outlier handling) were verified to
  require **no** additional rules: 0 rows removed, 0 rows changed, no extra
  datasets written — recorded constants
  `NO_ADDITIONAL_FILTERING_REQUIRED`,
  `NO_ADDITIONAL_TRANSFORMATION_REQUIRED`,
  `NO_ADDITIONAL_OUTLIER_HANDLING_REQUIRED` in `src/data_cleaning.py`.

## Missing Values and Invalid Records

Missing-value decision (Phase 5.1, applied to the raw frame):

| Column | Missing count | Share of 541,909 rows | Decision |
|---|---|---|---|
| Description | 1,454 | 0.2683% | Preserved as NaN — imputing product text would fabricate data; rows kept because they carry valid CustomerID/Quantity/UnitPrice needed for RFM |
| All other columns | 0 | 0.0000% | No action |

Invalid-record removal (Phase 5.3, evaluated on the Phase 5.2 deduplicated
frame of 536,641 rows):

| Rule | Definition | Rows flagged |
|---|---|---|
| R1 | Cancellation/return invoices (InvoiceNo starts with "C") | 9,251 |
| R2 | Non-positive Quantity on NON-cancellation invoices | 1,336 |
| R3 | Non-positive UnitPrice | 2,512 |
| Union removed (no double counting) | R1 ∪ R2 ∪ R3 | **11,763** |

Integrity check: 536,641 − 11,763 = **524,878** rows — exactly the size of the
saved working dataset. Per the documented data logic, negative Quantity alone
is never a removal criterion: cancellations leave via R1 (invoice status), and
non-cancellation non-positive quantities additionally carry UnitPrice ≤ 0, so
R2 ⊂ R3's anomaly set and R1 ∩ R3 = ∅.

Full cleaning chain: 541,909 (cleaned, missing handled) → 536,641
(deduplicated) → **524,878** (working).

## Duplicate Records

- Exact duplicate rows (identical across all eight columns): **5,268** removed
  between the 5.1 cleaned stage (541,909 rows) and the 5.2 deduplicated stage
  (536,641 rows).
- Policy: `duplicated(keep="first")` — the first occurrence of each duplicated
  group is kept and original row order is preserved.
- Remaining duplicates in the working dataset: **0** (verified programmatically
  and enforced again during Phases 5.4–5.8 verification checks).

## Descriptive Statistics

Numeric profile of the working dataset (524,878 valid transaction lines):

| Statistic | Quantity | UnitPrice (£) |
|---|---|---|
| Count | 524,878 | 524,878 |
| Mean | 10.62 | 3.92 |
| Std | 156.28 | 36.09 |
| Min | 1 | 0.001 |
| 25th percentile | 1 | 1.25 |
| Median | 4 | 2.08 |
| 75th percentile | 11 | 4.13 |
| Max | 80,995 | 13,541.33 |

Right-skewed distributions: half of all lines sell ≤ 4 items at ≤ £2.08, while
extreme maxima (80,995 items; £13,541.33) reflect genuine bulk/business orders.
Because Phases 5.4–5.6 verified that no additional outlier handling is
required, these extreme-but-valid records remain in the analysis population.

Transaction-level Pearson relationships:

| Pair | r |
|---|---|
| Quantity ↔ UnitPrice | −0.0038 (no linear relationship) |
| Quantity ↔ Revenue | +0.9074 (strong; Quantity drives line revenue) |
| UnitPrice ↔ Revenue | +0.1374 (weak) |

Revenue is derived as Quantity × UnitPrice — the identical definition reused
by RFM Monetary (Phase 7) and by the revenue insights (Phase 11), keeping the
whole project internally consistent.

## EDA Visualizations

No permanent chart deliverable belongs to Phase 6 in this project: the approved
Month-2 submission record states explicitly that Phase 6 produces no permanent
statistical chart output, and the four approved PNG charts in `outputs/charts/`
are Phase 10 visualizations of the RFM/segmentation results — they are not
attributed to EDA here. The quantitative distributions, relationships, country
ranking and monthly trends tabulated in this report constitute the Phase 6 EDA
evidence, and they are recomputed deterministically at any time via
`build_phase6_eda_summary(dataframe=…)` in `src/statistics_analysis.py`.

## Key Findings

1. Market concentration: the United Kingdom generates £9,001,744.09 of the
   £10,642,110.80 total (≈ 84.6%). Top five countries by revenue:
   United Kingdom £9,001,744.09 · Netherlands £285,446.34 · EIRE £283,140.52 ·
   Germany £228,678.40 · France £209,625.37.
2. Monthly unique-invoice counts vary strongly across the 13 observed months:
   the slowest complete month is January 2011 (1,086 unique invoices) and
   activity peaks in November 2011 (2,769 invoices, £1,503,866.78). December
   2011 (819) covers only days up to the 9 December cut-off date and must not
   be read as a decline.

| Month | Unique invoices | Revenue (£) |
|---|---|---|
| 2010-12 | 1,559 | 821,452.73 |
| 2011-01 | 1,086 | 689,811.61 |
| 2011-02 | 1,100 | 522,545.56 |
| 2011-03 | 1,454 | 716,215.26 |
| 2011-04 | 1,246 | 536,968.49 |
| 2011-05 | 1,681 | 769,296.61 |
| 2011-06 | 1,533 | 760,547.01 |
| 2011-07 | 1,475 | 718,076.12 |
| 2011-08 | 1,361 | 757,841.38 |
| 2011-09 | 1,837 | 1,056,435.19 |
| 2011-10 | 2,040 | 1,151,263.73 |
| 2011-11 | 2,769 | 1,503,866.78 |
| 2011-12 (partial) | 819 | 637,790.33 |

3. Data quality supports trustworthy modelling: after cleaning, every retained
   line has a valid invoice, strictly positive quantity and price, and a known
   customer — a clean base for per-customer aggregation.
4. Transaction-level behavior is heavily skewed (bulk orders coexist with tiny
   retail baskets), which later motivates aggregating to customer level before
   scoring instead of treating each line independently.

## Relevance to RFM Analysis

- **Monetary**: removing R1/R2/R3 records guarantees every retained line has
  Quantity > 0 and UnitPrice > 0, so Σ(Quantity × UnitPrice) per customer is a
  true net purchase value with no cancellation noise inflating or deflating it.
- **Frequency**: zero duplicate rows ensure distinct-invoice counting measures
  real repeat purchasing rather than double-booked lines.
- **Recency**: the complete, datetime-parsed InvoiceDate column allows the
  deterministic reference date 2011-12-09 (dataset maximum) and day-accurate
  recency for all 4,338 customers.
- **Grouping validity**: 100%-populated CustomerID makes customer-level
  aggregation lossless; the preserved 1,454 Description gaps never affect it.
- The strong Quantity↔Revenue correlation (+0.91) confirms the Monetary proxy
  behaves coherently at line level before customer aggregation, supporting the
  segment statistics produced in Phase 9.
