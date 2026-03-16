"""Tests for the distance module."""

import unittest

from roadtrip.distance import (
    haversine,
    estimate_drive_time_hours,
    format_duration,
    leg_distances,
    total_distance,
)
from roadtrip.models import Stop


class TestHaversine(unittest.TestCase):
    def test_same_point(self):
        self.assertAlmostEqual(haversine(40.0, -74.0, 40.0, -74.0), 0.0)

    def test_new_york_to_los_angeles(self):
        # NYC (40.7128, -74.0060) to LA (34.0522, -118.2437)
        dist = haversine(40.7128, -74.0060, 34.0522, -118.2437)
        # Great-circle distance is approximately 2451 miles
        self.assertAlmostEqual(dist, 2451, delta=50)

    def test_london_to_paris(self):
        # London (51.5074, -0.1278) to Paris (48.8566, 2.3522)
        dist = haversine(51.5074, -0.1278, 48.8566, 2.3522)
        # Approximately 213 miles
        self.assertAlmostEqual(dist, 213, delta=15)

    def test_symmetry(self):
        d1 = haversine(40.0, -74.0, 34.0, -118.0)
        d2 = haversine(34.0, -118.0, 40.0, -74.0)
        self.assertAlmostEqual(d1, d2, places=6)


class TestDriveTime(unittest.TestCase):
    def test_basic(self):
        self.assertAlmostEqual(estimate_drive_time_hours(60, 60), 1.0)

    def test_zero_distance(self):
        self.assertAlmostEqual(estimate_drive_time_hours(0, 60), 0.0)

    def test_invalid_speed(self):
        with self.assertRaises(ValueError):
            estimate_drive_time_hours(100, 0)


class TestFormatDuration(unittest.TestCase):
    def test_hours_and_minutes(self):
        self.assertEqual(format_duration(2.5), "~2h 30m")

    def test_zero(self):
        self.assertEqual(format_duration(0), "~0m")


class TestLegDistances(unittest.TestCase):
    def test_two_stops(self):
        stops = [
            Stop("A", 40.7128, -74.0060),
            Stop("B", 34.0522, -118.2437),
        ]
        legs = leg_distances(stops)
        self.assertEqual(len(legs), 1)
        self.assertEqual(legs[0][0], "A")
        self.assertEqual(legs[0][1], "B")
        self.assertGreater(legs[0][2], 0)

    def test_empty(self):
        self.assertEqual(leg_distances([]), [])

    def test_single_stop(self):
        self.assertEqual(leg_distances([Stop("A", 0, 0)]), [])


class TestTotalDistance(unittest.TestCase):
    def test_round_trip_consistency(self):
        stops = [
            Stop("A", 40.0, -74.0),
            Stop("B", 41.0, -75.0),
            Stop("C", 42.0, -76.0),
        ]
        legs = leg_distances(stops)
        self.assertAlmostEqual(
            total_distance(stops),
            sum(d for _, _, d in legs),
        )


if __name__ == "__main__":
    unittest.main()
