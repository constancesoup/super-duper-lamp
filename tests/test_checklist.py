"""Tests for checklist module."""

import unittest

from roadtrip.models import Trip
from roadtrip.checklist import add_item, remove_item, check_item, uncheck_item, print_checklist


class TestChecklist(unittest.TestCase):
    def setUp(self):
        self.trip = Trip(name="test")

    def test_add_item(self):
        add_item(self.trip, "Tent")
        self.assertEqual(len(self.trip.checklist), 1)
        self.assertEqual(self.trip.checklist[0].item, "Tent")
        self.assertFalse(self.trip.checklist[0].checked)

    def test_check_and_uncheck(self):
        add_item(self.trip, "Tent")
        check_item(self.trip, 0)
        self.assertTrue(self.trip.checklist[0].checked)
        uncheck_item(self.trip, 0)
        self.assertFalse(self.trip.checklist[0].checked)

    def test_remove_item(self):
        add_item(self.trip, "Tent")
        add_item(self.trip, "Cooler")
        remove_item(self.trip, 0)
        self.assertEqual(len(self.trip.checklist), 1)
        self.assertEqual(self.trip.checklist[0].item, "Cooler")

    def test_out_of_bounds(self):
        with self.assertRaises(IndexError):
            check_item(self.trip, 0)

    def test_print_empty(self):
        result = print_checklist(self.trip)
        self.assertIn("empty", result.lower())

    def test_print_with_items(self):
        add_item(self.trip, "Tent")
        check_item(self.trip, 0)
        add_item(self.trip, "Map")
        result = print_checklist(self.trip)
        self.assertIn("[x]", result)
        self.assertIn("[ ]", result)
        self.assertIn("1/2", result)


if __name__ == "__main__":
    unittest.main()
