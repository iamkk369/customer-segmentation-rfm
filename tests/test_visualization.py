"""
tests/test_visualization.py - Phase 10: Data Visualization tests.

Internal unit-style tests (Python built-in unittest only, consistent with the
project dependency policy - pytest is NOT an approved dependency).

Coverage:
    - Chart creation for every approved Phase 10 visualization
    - Charts saved as non-empty PNG files in outputs/charts/
    - Returned paths resolve inside config.CHARTS_DIR
    - Input validation (empty / missing required columns)
    - Input table not mutated by plotting
    - Deterministic repeated rendering (identical PNG bytes)
    - No new output directories introduced
    - Real-data execution via build_phase10_visualizations()
    - Raw dataset remains unchanged after visualization
"""

import hashlib
import pathlib
import unittest

import pandas as pd

import config
from src.visualization import (
    CHARTS_DIR,
    plot_rfm_metric_correlation_scatter,
    plot_rfm_score_distributions,
    plot_segment_monetary_box,
    plot_segment_size_bar,
    build_phase10_visualizations,
)

# Raw dataset integrity (Phase 3 approval record; also enforced by Phase 4 tests).
RAW_CSV_PATH = config.RAW_DATA_DIR / "OnlineRetail.csv"
RAW_CSV_SHA256 = "BFA47136118BC854A31E69D5C9E9689A2D07B73909F253679F2CC85EC4EB84EB"

PHASE10_CHART_FUNCTIONS = (
    plot_rfm_score_distributions,
    plot_segment_size_bar,
    plot_segment_monetary_box,
    plot_rfm_metric_correlation_scatter,
)


def _phase10_fixture():
    """Ten customers across the five segments with complete RFM fields."""
    return pd.DataFrame(
        {
            "CustomerID": ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"],
            "recency_days": [1, 2, 10, 12, 30, 33, 60, 70, 120, 150],
            "frequency": [20, 19, 18, 17, 16, 15, 14, 13, 12, 11],
            "monetary": [1000.0, 950.0, 900.0, 850.0, 800.0, 750.0, 700.0, 650.0, 600.0, 550.0],
            "recency_score": [5, 5, 4, 4, 3, 3, 2, 2, 1, 1],
            "frequency_score": [5, 5, 4, 4, 3, 3, 2, 2, 1, 1],
            "monetary_score": [5, 5, 4, 4, 3, 3, 2, 2, 1, 1],
            "segment": (
                ["Champions"] * 2
                + ["Loyal Customers"] * 2
                + ["Average Customers"] * 2
                + ["At-Risk Customers"] * 2
                + ["Lost Customers"] * 2
            ),
        }
    )


class TestChartOutputCreation(unittest.TestCase):
    """Every approved Phase 10 chart must be produced from valid input."""

    def test_rfm_score_distribution_chart_created(self):
        path = plot_rfm_score_distributions(segmented=_phase10_fixture())
        self.assertIsInstance(path, pathlib.Path)
        self.assertEqual(path.parent.resolve(), CHARTS_DIR.resolve())
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 0)
        self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))

    def test_segment_size_chart_created(self):
        path = plot_segment_size_bar(segmented=_phase10_fixture())
        self.assertIsInstance(path, pathlib.Path)
        self.assertEqual(path.parent.resolve(), CHARTS_DIR.resolve())
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 0)
        self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))

    def test_segment_monetary_box_chart_created(self):
        path = plot_segment_monetary_box(segmented=_phase10_fixture())
        self.assertIsInstance(path, pathlib.Path)
        self.assertEqual(path.parent.resolve(), CHARTS_DIR.resolve())
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 0)
        self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))

    def test_correlation_scatter_chart_created(self):
        path = plot_rfm_metric_correlation_scatter(segmented=_phase10_fixture())
        self.assertIsInstance(path, pathlib.Path)
        self.assertEqual(path.parent.resolve(), CHARTS_DIR.resolve())
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 0)
        self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))


class TestInputValidation(unittest.TestCase):
    """Invalid Phase 10 input must raise clear ValueErrors."""

    def test_empty_input_raises_for_every_chart(self):
        empty = _phase10_fixture().iloc[0:0]
        for chart_function in PHASE10_CHART_FUNCTIONS:
            with self.subTest(chart=chart_function.__name__):
                with self.assertRaises(ValueError):
                    chart_function(segmented=empty)

    def test_missing_required_column_raises(self):
        df = _phase10_fixture().drop(columns=["segment"])
        for chart_function in PHASE10_CHART_FUNCTIONS:
            with self.subTest(chart=chart_function.__name__):
                with self.assertRaises(ValueError):
                    chart_function(segmented=df)

    def test_plotting_does_not_mutate_input(self):
        df = _phase10_fixture()
        before = df.copy()
        plot_segment_monetary_box(segmented=df)
        pd.testing.assert_frame_equal(df, before)


class TestDeterministicRendering(unittest.TestCase):
    """Phase 10 charts must be deterministic for identical input."""

    def test_repeated_rendering_produces_identical_bytes(self):
        df = _phase10_fixture()
        first = plot_segment_size_bar(segmented=df).read_bytes()
        second = plot_segment_size_bar(segmented=df).read_bytes()
        self.assertEqual(first, second)

    def test_score_distribution_rendering_deterministic(self):
        df = _phase10_fixture()
        first = plot_rfm_score_distributions(segmented=df).read_bytes()
        second = plot_rfm_score_distributions(segmented=df).read_bytes()
        self.assertEqual(first, second)


class TestNoNewOutputDirectories(unittest.TestCase):
    """Visualization must stay inside the approved outputs structure."""

    def test_outputs_contains_only_approved_directories(self):
        outputs_dir = pathlib.Path(config.OUTPUTS_DIR)
        present = {item.name for item in outputs_dir.iterdir() if item.is_dir()}
        self.assertEqual(present, {"charts", "tables", "reports"})


class TestRealDataVisualization(unittest.TestCase):
    """End-to-end visualization on the real Phase 5 -> 7 -> 8 pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.paths = build_phase10_visualizations()

    def test_all_four_charts_returned(self):
        expected = {
            "rfm_score_distributions",
            "segment_size_bar",
            "segment_monetary_box",
            "rfm_metric_correlation_scatter",
        }
        self.assertEqual(set(self.paths), expected)

    def test_charts_saved_as_non_empty_png_files(self):
        for name, path in self.paths.items():
            with self.subTest(chart=name):
                self.assertEqual(path.name, f"{name}.png")
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)
                self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))

    def test_charts_saved_inside_config_charts_dir(self):
        expected_parent = pathlib.Path(config.CHARTS_DIR).resolve()
        for path in self.paths.values():
            self.assertEqual(path.parent.resolve(), expected_parent)

    def test_raw_dataset_unchanged_after_visualization(self):
        digest = hashlib.sha256(RAW_CSV_PATH.read_bytes()).hexdigest().upper()
        self.assertEqual(digest, RAW_CSV_SHA256)


if __name__ == "__main__":
    unittest.main()