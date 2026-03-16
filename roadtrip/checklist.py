"""Packing checklist operations."""

from roadtrip.models import Trip, ChecklistItem


def add_item(trip: Trip, item: str) -> None:
    """Add an item to the packing checklist."""
    trip.checklist.append(ChecklistItem(item=item))


def remove_item(trip: Trip, index: int) -> None:
    """Remove an item by index."""
    if index < 0 or index >= len(trip.checklist):
        raise IndexError(f"Checklist index {index} out of range (0-{len(trip.checklist) - 1})")
    trip.checklist.pop(index)


def check_item(trip: Trip, index: int) -> None:
    """Mark an item as checked."""
    if index < 0 or index >= len(trip.checklist):
        raise IndexError(f"Checklist index {index} out of range (0-{len(trip.checklist) - 1})")
    trip.checklist[index].checked = True


def uncheck_item(trip: Trip, index: int) -> None:
    """Mark an item as unchecked."""
    if index < 0 or index >= len(trip.checklist):
        raise IndexError(f"Checklist index {index} out of range (0-{len(trip.checklist) - 1})")
    trip.checklist[index].checked = False


def print_checklist(trip: Trip) -> str:
    """Format the checklist for display. Returns the formatted string."""
    if not trip.checklist:
        return "Packing checklist is empty."
    checked = sum(1 for c in trip.checklist if c.checked)
    lines = [f"Packing Checklist ({checked}/{len(trip.checklist)} checked):"]
    for i, item in enumerate(trip.checklist):
        mark = "x" if item.checked else " "
        lines.append(f"  [{mark}] {i}: {item.item}")
    return "\n".join(lines)
