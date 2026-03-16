"""Distance calculations using the Haversine formula."""

import math

EARTH_RADIUS_MILES = 3958.8


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return straight-line distance in miles between two lat/lon points."""
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    dlat = lat2 - lat1
    dlon = math.radians(lon2) - math.radians(lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def estimate_drive_time_hours(distance_miles: float, avg_speed_mph: float = 60.0) -> float:
    """Estimate drive time in hours based on distance and average speed."""
    if avg_speed_mph <= 0:
        raise ValueError("Average speed must be positive")
    return distance_miles / avg_speed_mph


def format_duration(hours: float) -> str:
    """Format hours as '~Xh Ym'."""
    h = int(hours)
    m = int((hours - h) * 60)
    if h == 0:
        return f"~{m}m"
    return f"~{h}h {m}m"


def leg_distances(stops: list) -> list[tuple[str, str, float]]:
    """Return list of (from_name, to_name, miles) for consecutive stops."""
    legs = []
    for i in range(len(stops) - 1):
        dist = haversine(stops[i].lat, stops[i].lon, stops[i + 1].lat, stops[i + 1].lon)
        legs.append((stops[i].name, stops[i + 1].name, dist))
    return legs


def total_distance(stops: list) -> float:
    """Sum of all leg distances."""
    return sum(dist for _, _, dist in leg_distances(stops))
