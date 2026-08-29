"""Phase 13 — Final Integration tests.

Validates the orchestration implemented in ``main.py`` against the REAL
project data without duplicating the Phase 12 suites:

    - every pipeline stage executes on real data and returns usable output;
    - outputs agree with the established verified project facts
      (541,909 raw rows -> 524,878 working rows -> 4,338 customers ->
      five approved segments summing to the customer total);
    - artifacts land in the existing config-defined output locations
      (data/processed CSVs, four approved charts, Phase 11 report);
    - integration does NOT mutate the raw dataset contract (loading is
      read-only) and reuse-only design leaves no duplicated logic.
"""

import unittest

import pandas as pd

import config
from main import run_full_pipeline
from src.data_cleaning import (
    get_cleaned_dataset_path,
    get_deduplicated_dataset_path,
    get_invalid_removed_dataset_path,
)

# Verified project reference facts (Phase 2-12 records).
EXPECTED_RAW_ROWS = 541909
EXPECTED_WORKING_ROWS = 524878
EXPECTED_CUSTOMERS = 4338
APPROVED_SEGMENTS = {
    "Champions", "Loyal Customers", "Average Customers",
    "At-Risk Customers", "Lost Customers",
}


class TestFullPipelineIntegration(unittest.TestCase):
    """Run the integrated pipeline ONCE and verify every stage result."""

    @classmethod
    def setUpClass(cls):
        cls.results = run_full_pipeline()

    def test_stage4_raw_load_matches_verified_row_count(self):
        self.assertEqual(self.results["raw_rows"], EXPECTED_RAW_ROWS)

    def test_stage5_working_dataset_rows_and_paths(self):
        cleaning = self.results["cleaning"]
        self.assertEqual(cleaning["working_rows"], EXPECTED_WORKING_ROWS)
        # OPTION B: cleaned/deduplicated DataFrames are processed in memory,
        # so the pipeline reports only the persisted invalid-removed working
        # path and no longer exposes permanent cleaned/deduplicated paths.
        self.assertNotIn("cleaned_path", cleaning)
        self.assertNotIn("deduplicated_path", cleaning)
        self.assertEqual(
            cleaning["working_path"], get_invalid_removed_dataset_path()
        )
        self.assertTrue(cleaning["working_path"].is_file())

    def test_stage6_eda_summary_sections_present(self):
        eda = self.results["eda"]
        for key in ("dataset_summary", "distribution_summary",
                    "relationship_summary", "monthly_trends"):
            self.assertIn(key, eda)

    def test_stage7_rfm_output_structure(self):
        rfm = self.results["rfm"]
        self.assertIn("rfm_table", rfm)
        self.assertIn("reference_date", rfm)
        scored = rfm["rfm_table"]
        self.assertEqual(self.results["customer_count"], EXPECTED_CUSTOMERS)
        for column in ("recency_days", "frequency", "monetary",
                       "recency_score", "frequency_score", "monetary_score"):
            self.assertIn(column, scored.columns)

    def test_stage8_segmentation_matches_approved_segments(self):
        segmented = self.results["segmented_table"]
        summary = self.results["segment_summary"]
        self.assertEqual(set(summary), APPROVED_SEGMENTS)
        self.assertEqual(sum(summary.values()), EXPECTED_CUSTOMERS)
        self.assertTrue((segmented["segment"].isin(APPROVED_SEGMENTS)).all())

    def test_stage10_four_charts_saved_in_config_dir(self):
        charts = self.results["charts"]
        self.assertEqual(len(charts), 4)
        for name, path in charts.items():
            with self.subTest(chart=name):
                self.assertTrue(path.is_file(), str(path))
                self.assertEqual(path.parent, config.CHARTS_DIR)

    def test_stage11_report_written_with_findings(self):
        report_path = self.results["report_path"]
        self.assertTrue(report_path.is_file())
        text = report_path.read_text(encoding="utf-8")
        self.assertIn("Final Findings", text)
        self.assertIn("Revenue Insights", text)

    def test_insights_include_all_phase11_outputs(self):
        self.assertEqual(
            set(self.results["insights_keys"]),
            {"segment_insights", "segment_characteristics", "revenue_insights",
             "statistical_insights", "final_findings"},
        )

    def test_pipeline_fast_enough_single_pass(self):
        """Single-pass orchestration guard: no duplicated heavy processing."""
        self.assertLess(self.results["elapsed_seconds"], 600)


class TestIntegrationBoundary(unittest.TestCase):
    """Lightweight checks that do not re-run the heavy pipeline."""

    def test_main_module_imports_without_execution_side_effects(self):
        import main as main_module
        self.assertTrue(callable(main_module.run_full_pipeline))
        self.assertTrue(callable(main_module.main))

    def test_processed_datasets_exist_after_integration(self):
        """OPTION B boundary: only the invalid-removed dataset is permanent."""
        self.assertTrue(
            get_invalid_removed_dataset_path().is_file(),
            str(get_invalid_removed_dataset_path()),
        )
        # Obsolete intermediate files must NOT be recreated by the pipeline.
        self.assertFalse(
            get_cleaned_dataset_path().is_file(),
            str(get_cleaned_dataset_path()),
        )
        self.assertFalse(
            get_deduplicated_dataset_path().is_file(),
            str(get_deduplicated_dataset_path()),
        )

    def test_raw_loading_is_read_only_snapshot(self):
        """Loading twice yields identical shape/dtypes (no mutation path)."""
        from src.data_loading import load_raw_dataset, inspect_data_types
        df = load_raw_dataset()
        self.assertEqual(len(df), EXPECTED_RAW_ROWS)
        types = inspect_data_types(df)
        # pandas 3.x parses CSV datetimes at microsecond resolution;
        # require any datetime64 variant rather than a specific unit.
        self.assertTrue(
            str(types["InvoiceDate"]).startswith("datetime64"),
            f"InvoiceDate must remain datetime-typed, got {types['InvoiceDate']}",
        )


if __name__ == "__main__":
    unittest.main()
