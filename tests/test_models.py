"""Tests for data models."""

import unittest

from roadtrip.models import Trip, Stop, ChecklistItem, DayPlan, FuelConfig


class TestTripRoundTrip(unittest.TestCase):
    def test_full_round_trip(self):
        trip = Trip(
            name="test",
            stops=[Stop("Denver", 39.7, -104.9, "start")],
            checklist=[ChecklistItem("Tent", True)],
            days=[DayPlan(1, [0])],
            fuel_config=FuelConfig(30.0, 4.00),
        )
        restored = Trip.from_dict(trip.to_dict())
        self.assertEqual(restored.name, trip.name)
        self.assertEqual(len(restored.stops), 1)
        self.assertEqual(restored.stops[0].name, "Denver")
        self.assertEqual(restored.stops[0].notes, "start")
        self.assertTrue(restored.checklist[0].checked)
        self.assertEqual(restored.days[0].stop_indices, [0])
        self.assertEqual(restored.fuel_config.mpg, 30.0)

    def test_minimal_trip(self):
        data = {"name": "empty"}
        trip = Trip.from_dict(data)
        self.assertEqual(trip.name, "empty")
        self.assertEqual(trip.stops, [])
        self.assertEqual(trip.checklist, [])
        self.assertEqual(trip.days, [])
        self.assertEqual(trip.fuel_config.mpg, 25.0)

    def test_defaults(self):
        trip = Trip(name="x")
        d = trip.to_dict()
        self.assertEqual(d["name"], "x")
        self.assertEqual(d["stops"], [])
        self.assertEqual(d["fuel_config"]["mpg"], 25.0)


if __name__ == "__main__":
    unittest.main()
