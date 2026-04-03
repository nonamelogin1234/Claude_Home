from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from progress import boss_progress, calculate_level, current_max_gap_days, maybe_float


class ProgressTests(unittest.TestCase):
    def test_calculate_level_for_second_rank(self) -> None:
        level, title, next_title, progress, left = calculate_level(12)
        self.assertEqual(level, 2)
        self.assertEqual(title, "Воин")
        self.assertEqual(next_title, "Ветеран")
        self.assertGreater(progress, 0)
        self.assertEqual(left, 13)

    def test_boss_progress_when_start_equals_target(self) -> None:
        self.assertEqual(boss_progress(100.0, 100.0, 100.0), 0.0)
        self.assertEqual(boss_progress(100.0, 99.0, 100.0), 100.0)

    def test_current_max_gap_days(self) -> None:
        gap = current_max_gap_days([date(2026, 4, 3), date(2026, 4, 1), date(2026, 3, 28)])
        self.assertEqual(gap, 4)

    def test_maybe_float_handles_invalid_value(self) -> None:
        self.assertIsNone(maybe_float("N/A"))
        self.assertIsNone(maybe_float(None))
        self.assertEqual(maybe_float("12.5"), 12.5)


if __name__ == "__main__":
    unittest.main()
