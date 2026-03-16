"""Fuel cost calculations."""


def fuel_needed_gallons(distance_miles: float, mpg: float) -> float:
    """Calculate gallons of fuel needed for a given distance."""
    if mpg <= 0:
        raise ValueError("MPG must be positive")
    return distance_miles / mpg


def fuel_cost(distance_miles: float, mpg: float, price_per_gallon: float) -> float:
    """Calculate total fuel cost for a given distance."""
    return fuel_needed_gallons(distance_miles, mpg) * price_per_gallon
