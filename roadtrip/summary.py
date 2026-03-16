"""Trip summary and daily itinerary formatting."""

from roadtrip.models import Trip
from roadtrip.distance import (
    leg_distances,
    total_distance,
    estimate_drive_time_hours,
    format_duration,
    haversine,
)
from roadtrip.fuel import fuel_cost


def print_trip_summary(trip: Trip) -> str:
    """Format a full trip summary. Returns the formatted string."""
    lines = [f"Trip: {trip.name}", f"Stops: {len(trip.stops)}"]

    if len(trip.stops) < 2:
        if trip.stops:
            lines.append(f"  1. {trip.stops[0].name}")
        lines.append("\nAdd at least 2 stops to see route details.")
        return "\n".join(lines)

    lines.append("")
    legs = leg_distances(trip.stops)
    for i, (from_name, to_name, dist) in enumerate(legs, 1):
        time = estimate_drive_time_hours(dist)
        lines.append(f"  Leg {i}: {from_name} -> {to_name} — {dist:.1f} mi ({format_duration(time)})")

    total_dist = total_distance(trip.stops)
    total_time = estimate_drive_time_hours(total_dist)
    cost = fuel_cost(total_dist, trip.fuel_config.mpg, trip.fuel_config.price_per_gallon)
    gallons = total_dist / trip.fuel_config.mpg

    lines.append("")
    lines.append(f"  Total distance: {total_dist:.1f} miles")
    lines.append(f"  Total drive time: {format_duration(total_time)}")
    lines.append(f"  Fuel needed: {gallons:.1f} gallons")
    lines.append(f"  Estimated fuel cost: ${cost:.2f}")
    lines.append("")
    lines.append("  Note: Distances are straight-line estimates.")

    return "\n".join(lines)


def print_daily_itinerary(trip: Trip) -> str:
    """Format a day-by-day itinerary. Returns the formatted string."""
    if not trip.days:
        return "No daily itinerary set. Use 'roadtrip day add' to assign stops to days."

    lines = ["Daily Itinerary:", ""]
    trip_total_dist = 0.0
    trip_total_time = 0.0
    trip_total_cost = 0.0

    for day_plan in sorted(trip.days, key=lambda d: d.day):
        lines.append(f"  Day {day_plan.day}:")
        if len(day_plan.stop_indices) < 2:
            if day_plan.stop_indices:
                lines.append(f"    {trip.stops[day_plan.stop_indices[0]].name}")
            lines.append("")
            continue

        day_dist = 0.0
        route_parts = []
        for i in range(len(day_plan.stop_indices) - 1):
            s1 = trip.stops[day_plan.stop_indices[i]]
            s2 = trip.stops[day_plan.stop_indices[i + 1]]
            day_dist += haversine(s1.lat, s1.lon, s2.lat, s2.lon)
            if not route_parts:
                route_parts.append(s1.name)
            route_parts.append(s2.name)

        day_time = estimate_drive_time_hours(day_dist)
        day_cost = fuel_cost(day_dist, trip.fuel_config.mpg, trip.fuel_config.price_per_gallon)

        lines.append(f"    {' -> '.join(route_parts)}")
        lines.append(f"    Distance: {day_dist:.1f} mi | Drive time: {format_duration(day_time)} | Fuel: ${day_cost:.2f}")
        lines.append("")

        trip_total_dist += day_dist
        trip_total_time += day_time
        trip_total_cost += day_cost

    lines.append(f"  Trip total: {trip_total_dist:.1f} mi | {format_duration(trip_total_time)} | ${trip_total_cost:.2f}")
    return "\n".join(lines)
