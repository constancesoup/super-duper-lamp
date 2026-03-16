"""Tests for fuel module."""

import unittest

from roadtrip.fuel import fuel_needed_gallons, fuel_cost


class TestFuel(unittest.TestCase):
    def test_gallons_needed(self):
        self.assertAlmostEqual(fuel_needed_gallons(100, 25), 4.0)

    def test_fuel_cost(self):
        self.assertAlmostEqual(fuel_cost(100, 25, 3.50), 14.0)

    def test_zero_distance(self):
        self.assertAlmostEqual(fuel_cost(0, 25, 3.50), 0.0)

    def test_invalid_mpg(self):
        with self.assertRaises(ValueError):
            fuel_needed_gallons(100, 0)


if __name__ == "__main__":
    unittest.main()
