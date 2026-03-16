"""Save and load trips as JSON files."""

import json
from pathlib import Path

from roadtrip.models import Trip

DEFAULT_DIR = Path.home() / ".roadtrip"


def _ensure_dir() -> None:
    DEFAULT_DIR.mkdir(parents=True, exist_ok=True)


def resolve_trip_path(name: str) -> Path:
    """Resolve a trip name or path to a file path."""
    if "/" in name or name.endswith(".json"):
        return Path(name)
    return DEFAULT_DIR / f"{name}.json"


def save_trip(trip: Trip, filepath: Path | None = None) -> Path:
    """Save a trip to a JSON file."""
    if filepath is None:
        filepath = resolve_trip_path(trip.name)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(trip.to_dict(), indent=2) + "\n")
    return filepath


def load_trip(filepath: Path) -> Trip:
    """Load a trip from a JSON file."""
    data = json.loads(filepath.read_text())
    return Trip.from_dict(data)


def list_trips() -> list[Path]:
    """List all saved trip files in the default directory."""
    _ensure_dir()
    return sorted(DEFAULT_DIR.glob("*.json"))
