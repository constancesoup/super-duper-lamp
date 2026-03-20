"""Flask web interface for the roadtrip planner."""

import os
import json
import urllib.request
from pathlib import Path

from flask import Flask, request, jsonify, render_template

from roadtrip.models import Trip, Stop, DayPlan, ChecklistItem
from roadtrip.distance import leg_distances, total_distance, estimate_drive_time_hours, format_duration, haversine
from roadtrip.fuel import fuel_cost, fuel_needed_gallons
from roadtrip.checklist import add_item, remove_item, check_item, uncheck_item

app = Flask(__name__)

# Store trips in a directory (use /tmp for Cloud Run, or configurable)
DATA_DIR = Path(os.environ.get("ROADTRIP_DATA_DIR", Path.home() / ".roadtrip"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _trip_path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def _save(trip: Trip) -> None:
    path = _trip_path(trip.name)
    path.write_text(json.dumps(trip.to_dict(), indent=2) + "\n")


def _load(name: str) -> Trip:
    path = _trip_path(name)
    data = json.loads(path.read_text())
    return Trip.from_dict(data)


def _trip_summary_dict(trip: Trip) -> dict:
    """Build a summary dict for a trip."""
    result = {"name": trip.name, "stops": [], "legs": [], "checklist": [], "days": []}

    for i, stop in enumerate(trip.stops):
        result["stops"].append({
            "index": i, "name": stop.name,
            "lat": stop.lat, "lon": stop.lon, "notes": stop.notes,
        })

    if len(trip.stops) >= 2:
        legs = leg_distances(trip.stops)
        for i, (from_name, to_name, dist) in enumerate(legs, 1):
            time_h = estimate_drive_time_hours(dist)
            result["legs"].append({
                "leg": i, "from": from_name, "to": to_name,
                "distance_miles": round(dist, 1),
                "drive_time": format_duration(time_h),
            })

        total_dist = total_distance(trip.stops)
        total_time = estimate_drive_time_hours(total_dist)
        gallons = fuel_needed_gallons(total_dist, trip.fuel_config.mpg)
        cost = fuel_cost(total_dist, trip.fuel_config.mpg, trip.fuel_config.price_per_gallon)

        result["total_distance_miles"] = round(total_dist, 1)
        result["total_drive_time"] = format_duration(total_time)
        result["fuel_gallons"] = round(gallons, 1)
        result["fuel_cost"] = round(cost, 2)

    result["fuel_config"] = {
        "mpg": trip.fuel_config.mpg,
        "price_per_gallon": trip.fuel_config.price_per_gallon,
    }

    for item in trip.checklist:
        result["checklist"].append({"item": item.item, "checked": item.checked})

    for day in sorted(trip.days, key=lambda d: d.day):
        day_info = {"day": day.day, "stops": []}
        day_dist = 0.0
        for idx in day.stop_indices:
            if idx < len(trip.stops):
                day_info["stops"].append(trip.stops[idx].name)
        if len(day.stop_indices) >= 2:
            for i in range(len(day.stop_indices) - 1):
                s1 = trip.stops[day.stop_indices[i]]
                s2 = trip.stops[day.stop_indices[i + 1]]
                day_dist += haversine(s1.lat, s1.lon, s2.lat, s2.lon)
            day_info["distance_miles"] = round(day_dist, 1)
            day_info["drive_time"] = format_duration(estimate_drive_time_hours(day_dist))
            day_info["fuel_cost"] = round(
                fuel_cost(day_dist, trip.fuel_config.mpg, trip.fuel_config.price_per_gallon), 2
            )
        result["days"].append(day_info)

    return result


# --- HTML UI ---

@app.route("/")
def index():
    return render_template("index.html")


# --- Geocoding Proxy ---

@app.route("/api/geocode/reverse")
def api_reverse_geocode():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "RoadtripPlanner/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        name = data.get("display_name", f"{lat}, {lon}")
        # Use a shorter name: city/town + state if available
        addr = data.get("address", {})
        short = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("hamlet") or ""
        state = addr.get("state", "")
        if short and state:
            name = f"{short}, {state}"
        elif short:
            name = short
        return jsonify({"name": name, "lat": float(lat), "lon": float(lon)})
    except Exception:
        return jsonify({"name": f"{lat}, {lon}", "lat": float(lat), "lon": float(lon)})


# --- API Routes ---

@app.route("/api/trips", methods=["GET"])
def api_list_trips():
    trips = sorted(DATA_DIR.glob("*.json"))
    return jsonify([t.stem for t in trips])


@app.route("/api/trips", methods=["POST"])
def api_create_trip():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Trip name is required"}), 400
    if _trip_path(name).exists():
        return jsonify({"error": f"Trip '{name}' already exists"}), 409
    trip = Trip(name=name)
    _save(trip)
    return jsonify({"message": f"Trip '{name}' created"}), 201


@app.route("/api/trips/<name>", methods=["GET"])
def api_get_trip(name: str):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    trip = _load(name)
    return jsonify(_trip_summary_dict(trip))


@app.route("/api/trips/<name>", methods=["DELETE"])
def api_delete_trip(name: str):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    path.unlink()
    return jsonify({"message": f"Trip '{name}' deleted"})


@app.route("/api/trips/<name>/stops", methods=["POST"])
def api_add_stop(name: str):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    data = request.get_json()
    stop_name = data.get("name", "").strip()
    lat = data.get("lat")
    lon = data.get("lon")
    if not stop_name or lat is None or lon is None:
        return jsonify({"error": "name, lat, and lon are required"}), 400
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lon must be numbers"}), 400
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return jsonify({"error": "Invalid coordinates"}), 400
    trip = _load(name)
    trip.stops.append(Stop(name=stop_name, lat=lat, lon=lon, notes=data.get("notes", "")))
    _save(trip)
    return jsonify({"message": f"Stop '{stop_name}' added", "total_stops": len(trip.stops)}), 201


@app.route("/api/trips/<name>/stops/<int:index>", methods=["DELETE"])
def api_remove_stop(name: str, index: int):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    trip = _load(name)
    if index < 0 or index >= len(trip.stops):
        return jsonify({"error": f"Stop index {index} out of range"}), 400
    removed = trip.stops.pop(index)
    for day in trip.days:
        day.stop_indices = [i - 1 if i > index else i for i in day.stop_indices if i != index]
    _save(trip)
    return jsonify({"message": f"Stop '{removed.name}' removed"})


@app.route("/api/trips/<name>/fuel", methods=["PUT"])
def api_update_fuel(name: str):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    data = request.get_json()
    trip = _load(name)
    if "mpg" in data:
        trip.fuel_config.mpg = float(data["mpg"])
    if "price_per_gallon" in data:
        trip.fuel_config.price_per_gallon = float(data["price_per_gallon"])
    _save(trip)
    return jsonify({"mpg": trip.fuel_config.mpg, "price_per_gallon": trip.fuel_config.price_per_gallon})


@app.route("/api/trips/<name>/checklist", methods=["POST"])
def api_add_checklist_item(name: str):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    data = request.get_json()
    item = data.get("item", "").strip()
    if not item:
        return jsonify({"error": "Item text is required"}), 400
    trip = _load(name)
    add_item(trip, item)
    _save(trip)
    return jsonify({"message": f"'{item}' added to checklist"}), 201


@app.route("/api/trips/<name>/checklist/<int:index>", methods=["DELETE"])
def api_remove_checklist_item(name: str, index: int):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    trip = _load(name)
    try:
        remove_item(trip, index)
    except IndexError as e:
        return jsonify({"error": str(e)}), 400
    _save(trip)
    return jsonify({"message": "Item removed"})


@app.route("/api/trips/<name>/checklist/<int:index>/check", methods=["PUT"])
def api_check_item(name: str, index: int):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    trip = _load(name)
    try:
        check_item(trip, index)
    except IndexError as e:
        return jsonify({"error": str(e)}), 400
    _save(trip)
    return jsonify({"message": "Item checked"})


@app.route("/api/trips/<name>/checklist/<int:index>/uncheck", methods=["PUT"])
def api_uncheck_item(name: str, index: int):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    trip = _load(name)
    try:
        uncheck_item(trip, index)
    except IndexError as e:
        return jsonify({"error": str(e)}), 400
    _save(trip)
    return jsonify({"message": "Item unchecked"})


@app.route("/api/trips/<name>/days", methods=["POST"])
def api_add_day(name: str):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    data = request.get_json()
    day_num = data.get("day")
    stop_indices = data.get("stop_indices", [])
    if day_num is None:
        return jsonify({"error": "day number is required"}), 400
    trip = _load(name)
    for idx in stop_indices:
        if idx < 0 or idx >= len(trip.stops):
            return jsonify({"error": f"Stop index {idx} out of range"}), 400
    trip.days = [d for d in trip.days if d.day != day_num]
    trip.days.append(DayPlan(day=int(day_num), stop_indices=stop_indices))
    trip.days.sort(key=lambda d: d.day)
    _save(trip)
    return jsonify({"message": f"Day {day_num} plan saved"}), 201


@app.route("/api/trips/<name>/days/<int:day_num>", methods=["DELETE"])
def api_remove_day(name: str, day_num: int):
    path = _trip_path(name)
    if not path.exists():
        return jsonify({"error": f"Trip '{name}' not found"}), 404
    trip = _load(name)
    before = len(trip.days)
    trip.days = [d for d in trip.days if d.day != day_num]
    if len(trip.days) == before:
        return jsonify({"error": f"No plan for day {day_num}"}), 404
    _save(trip)
    return jsonify({"message": f"Day {day_num} plan removed"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
