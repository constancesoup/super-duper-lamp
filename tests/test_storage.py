"""Tests for storage module."""

import tempfile
import unittest
from pathlib import Path

from roadtrip.models import Trip, Stop
from roadtrip.storage import save_trip, load_trip


class TestStorage(unittest.TestCase):
    def test_save_and_load(self):
        trip = Trip(
            name="test_trip",
            stops=[Stop("Denver", 39.7, -104.9)],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            save_trip(trip, path)
            self.assertTrue(path.exists())
            loaded = load_trip(path)
            self.assertEqual(loaded.name, "test_trip")
            self.assertEqual(len(loaded.stops), 1)
            self.assertEqual(loaded.stops[0].name, "Denver")

    def test_save_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "dir" / "trip.json"
            trip = Trip(name="nested")
            save_trip(trip, path)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
