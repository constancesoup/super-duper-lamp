"""CLI interface for the roadtrip planner."""

import argparse
import sys

from roadtrip.models import Trip, Stop, DayPlan
from roadtrip.storage import resolve_trip_path, save_trip, load_trip, list_trips
from roadtrip.checklist import add_item, remove_item, check_item, uncheck_item, print_checklist
from roadtrip.summary import print_trip_summary, print_daily_itinerary


def _load(name: str) -> Trip:
    path = resolve_trip_path(name)
    if not path.exists():
        print(f"Error: Trip '{name}' not found at {path}", file=sys.stderr)
        sys.exit(1)
    return load_trip(path)


def _save(trip: Trip) -> None:
    path = save_trip(trip)
    return path


def cmd_new(args: argparse.Namespace) -> None:
    path = resolve_trip_path(args.name)
    if path.exists():
        print(f"Error: Trip '{args.name}' already exists at {path}", file=sys.stderr)
        sys.exit(1)
    trip = Trip(name=args.name)
    save_trip(trip, path)
    print(f"Created new trip '{args.name}' at {path}")


def cmd_list(args: argparse.Namespace) -> None:
    trips = list_trips()
    if not trips:
        print("No saved trips found.")
        return
    print("Saved trips:")
    for t in trips:
        print(f"  {t.stem}")


def cmd_summary(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    print(print_trip_summary(trip))


def cmd_fuel(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    changed = False
    if args.mpg is not None:
        trip.fuel_config.mpg = args.mpg
        changed = True
    if args.price is not None:
        trip.fuel_config.price_per_gallon = args.price
        changed = True
    if changed:
        _save(trip)
        print("Fuel config updated.")
    print(f"  MPG: {trip.fuel_config.mpg}")
    print(f"  Price per gallon: ${trip.fuel_config.price_per_gallon:.2f}")
    if len(trip.stops) >= 2:
        from roadtrip.distance import total_distance
        from roadtrip.fuel import fuel_cost
        dist = total_distance(trip.stops)
        cost = fuel_cost(dist, trip.fuel_config.mpg, trip.fuel_config.price_per_gallon)
        print(f"  Total distance: {dist:.1f} miles")
        print(f"  Estimated fuel cost: ${cost:.2f}")


def cmd_stop_add(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    if not (-90 <= args.lat <= 90):
        print("Error: Latitude must be between -90 and 90.", file=sys.stderr)
        sys.exit(1)
    if not (-180 <= args.lon <= 180):
        print("Error: Longitude must be between -180 and 180.", file=sys.stderr)
        sys.exit(1)
    stop = Stop(name=args.name, lat=args.lat, lon=args.lon, notes=args.notes or "")
    trip.stops.append(stop)
    _save(trip)
    print(f"Added stop '{stop.name}' ({len(trip.stops)} total stops)")


def cmd_stop_remove(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    idx = args.index
    if idx < 0 or idx >= len(trip.stops):
        print(f"Error: Stop index {idx} out of range (0-{len(trip.stops) - 1})", file=sys.stderr)
        sys.exit(1)
    removed = trip.stops.pop(idx)
    # Update day plans: remove references to deleted stop, adjust higher indices
    for day in trip.days:
        day.stop_indices = [i - 1 if i > idx else i for i in day.stop_indices if i != idx]
    _save(trip)
    print(f"Removed stop '{removed.name}'")


def cmd_stop_list(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    if not trip.stops:
        print("No stops added yet.")
        return
    print(f"Stops ({len(trip.stops)}):")
    for i, stop in enumerate(trip.stops):
        notes = f" — {stop.notes}" if stop.notes else ""
        print(f"  {i}: {stop.name} ({stop.lat:.4f}, {stop.lon:.4f}){notes}")


def cmd_checklist_add(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    add_item(trip, args.item)
    _save(trip)
    print(f"Added '{args.item}' to checklist")


def cmd_checklist_remove(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    try:
        remove_item(trip, args.index)
    except IndexError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    _save(trip)
    print("Item removed.")


def cmd_checklist_check(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    try:
        check_item(trip, args.index)
    except IndexError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    _save(trip)
    print("Item checked.")


def cmd_checklist_uncheck(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    try:
        uncheck_item(trip, args.index)
    except IndexError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    _save(trip)
    print("Item unchecked.")


def cmd_checklist_show(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    print(print_checklist(trip))


def cmd_day_add(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    for idx in args.stop_indices:
        if idx < 0 or idx >= len(trip.stops):
            print(f"Error: Stop index {idx} out of range (0-{len(trip.stops) - 1})", file=sys.stderr)
            sys.exit(1)
    # Replace existing day plan if same day number
    trip.days = [d for d in trip.days if d.day != args.day_num]
    trip.days.append(DayPlan(day=args.day_num, stop_indices=args.stop_indices))
    trip.days.sort(key=lambda d: d.day)
    _save(trip)
    stop_names = [trip.stops[i].name for i in args.stop_indices]
    print(f"Day {args.day_num}: {' -> '.join(stop_names)}")


def cmd_day_remove(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    before = len(trip.days)
    trip.days = [d for d in trip.days if d.day != args.day_num]
    if len(trip.days) == before:
        print(f"Error: No plan found for day {args.day_num}", file=sys.stderr)
        sys.exit(1)
    _save(trip)
    print(f"Removed day {args.day_num} plan.")


def cmd_day_show(args: argparse.Namespace) -> None:
    trip = _load(args.trip)
    print(print_daily_itinerary(trip))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roadtrip",
        description="Plan road trips from the command line.",
    )
    sub = parser.add_subparsers(dest="command")

    # new
    p = sub.add_parser("new", help="Create a new trip")
    p.add_argument("name", help="Trip name")
    p.set_defaults(func=cmd_new)

    # list
    p = sub.add_parser("list", help="List saved trips")
    p.set_defaults(func=cmd_list)

    # summary
    p = sub.add_parser("summary", help="Show trip summary")
    p.add_argument("trip", help="Trip name or file path")
    p.set_defaults(func=cmd_summary)

    # fuel
    p = sub.add_parser("fuel", help="Show/set fuel config")
    p.add_argument("trip", help="Trip name or file path")
    p.add_argument("--mpg", type=float, help="Miles per gallon")
    p.add_argument("--price", type=float, help="Price per gallon")
    p.set_defaults(func=cmd_fuel)

    # stop
    stop_parser = sub.add_parser("stop", help="Manage stops")
    stop_sub = stop_parser.add_subparsers(dest="action")

    p = stop_sub.add_parser("add", help="Add a stop")
    p.add_argument("trip", help="Trip name or file path")
    p.add_argument("name", help="Stop name")
    p.add_argument("lat", type=float, help="Latitude")
    p.add_argument("lon", type=float, help="Longitude")
    p.add_argument("--notes", help="Notes about the stop")
    p.set_defaults(func=cmd_stop_add)

    p = stop_sub.add_parser("remove", help="Remove a stop by index")
    p.add_argument("trip", help="Trip name or file path")
    p.add_argument("index", type=int, help="Stop index")
    p.set_defaults(func=cmd_stop_remove)

    p = stop_sub.add_parser("list", help="List all stops")
    p.add_argument("trip", help="Trip name or file path")
    p.set_defaults(func=cmd_stop_list)

    # checklist
    cl_parser = sub.add_parser("checklist", help="Manage packing checklist")
    cl_sub = cl_parser.add_subparsers(dest="action")

    p = cl_sub.add_parser("add", help="Add a checklist item")
    p.add_argument("trip", help="Trip name or file path")
    p.add_argument("item", help="Item to add")
    p.set_defaults(func=cmd_checklist_add)

    p = cl_sub.add_parser("remove", help="Remove a checklist item")
    p.add_argument("trip", help="Trip name or file path")
    p.add_argument("index", type=int, help="Item index")
    p.set_defaults(func=cmd_checklist_remove)

    p = cl_sub.add_parser("check", help="Check off an item")
    p.add_argument("trip", help="Trip name or file path")
    p.add_argument("index", type=int, help="Item index")
    p.set_defaults(func=cmd_checklist_check)

    p = cl_sub.add_parser("uncheck", help="Uncheck an item")
    p.add_argument("trip", help="Trip name or file path")
    p.add_argument("index", type=int, help="Item index")
    p.set_defaults(func=cmd_checklist_uncheck)

    p = cl_sub.add_parser("show", help="Show checklist")
    p.add_argument("trip", help="Trip name or file path")
    p.set_defaults(func=cmd_checklist_show)

    # day
    day_parser = sub.add_parser("day", help="Manage daily itinerary")
    day_sub = day_parser.add_subparsers(dest="action")

    p = day_sub.add_parser("add", help="Assign stops to a day")
    p.add_argument("trip", help="Trip name or file path")
    p.add_argument("day_num", type=int, help="Day number")
    p.add_argument("stop_indices", type=int, nargs="+", help="Stop indices for this day")
    p.set_defaults(func=cmd_day_add)

    p = day_sub.add_parser("remove", help="Remove a day plan")
    p.add_argument("trip", help="Trip name or file path")
    p.add_argument("day_num", type=int, help="Day number")
    p.set_defaults(func=cmd_day_remove)

    p = day_sub.add_parser("show", help="Show daily itinerary")
    p.add_argument("trip", help="Trip name or file path")
    p.set_defaults(func=cmd_day_show)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)
