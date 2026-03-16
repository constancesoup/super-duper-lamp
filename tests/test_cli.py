"""Integration tests for the CLI."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from roadtrip.cli import main
from roadtrip.storage import load_trip


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.trip_path = str(Path(self.tmpdir) / "test.json")

    def _run(self, *args: str) -> None:
        main(list(args))

    def test_new_and_load(self):
        self._run("new", self.trip_path)
        trip = load_trip(Path(self.trip_path))
        self.assertEqual(trip.name, self.trip_path)

    def test_stop_add_and_list(self):
        self._run("new", self.trip_path)
        self._run("stop", "add", self.trip_path, "Denver", "39.7", "-104.9")
        trip = load_trip(Path(self.trip_path))
        self.assertEqual(len(trip.stops), 1)
        self.assertEqual(trip.stops[0].name, "Denver")

    def test_checklist_workflow(self):
        self._run("new", self.trip_path)
        self._run("checklist", "add", self.trip_path, "Tent")
        self._run("checklist", "check", self.trip_path, "0")
        trip = load_trip(Path(self.trip_path))
        self.assertTrue(trip.checklist[0].checked)

    def test_day_workflow(self):
        self._run("new", self.trip_path)
        self._run("stop", "add", self.trip_path, "A", "40", "-74")
        self._run("stop", "add", self.trip_path, "B", "41", "-75")
        self._run("day", "add", self.trip_path, "1", "0", "1")
        trip = load_trip(Path(self.trip_path))
        self.assertEqual(len(trip.days), 1)
        self.assertEqual(trip.days[0].stop_indices, [0, 1])

    def test_no_command_exits(self):
        with self.assertRaises(SystemExit):
            self._run()


if __name__ == "__main__":
    unittest.main()
