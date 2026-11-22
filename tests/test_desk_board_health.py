import datetime
import importlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desk" / "board"))
server = importlib.import_module("server")


class LastSweepDueTests(unittest.TestCase):
    def test_monday_morning_still_counts_fridays_sweep_until_the_grace_passes(self) -> None:
        zone = datetime.timezone(datetime.timedelta(hours=1))
        monday = datetime.datetime(2026, 11, 23, 10, 30, tzinfo=zone)
        self.assertEqual(server.last_sweep_due(monday), datetime.datetime(2026, 11, 20, 9, tzinfo=zone))
        self.assertEqual(server.last_sweep_due(monday.replace(hour=11)), datetime.datetime(2026, 11, 23, 9, tzinfo=zone))


if __name__ == "__main__":
    unittest.main()
