"""Data models for the roadtrip planner."""

from dataclasses import dataclass, field, asdict


@dataclass
class Stop:
    name: str
    lat: float
    lon: float
    notes: str = ""


@dataclass
class ChecklistItem:
    item: str
    checked: bool = False


@dataclass
class DayPlan:
    day: int
    stop_indices: list[int] = field(default_factory=list)


@dataclass
class FuelConfig:
    mpg: float = 25.0
    price_per_gallon: float = 3.50


@dataclass
class Trip:
    name: str
    stops: list[Stop] = field(default_factory=list)
    checklist: list[ChecklistItem] = field(default_factory=list)
    days: list[DayPlan] = field(default_factory=list)
    fuel_config: FuelConfig = field(default_factory=FuelConfig)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Trip":
        stops = [Stop(**s) for s in data.get("stops", [])]
        checklist = [ChecklistItem(**c) for c in data.get("checklist", [])]
        days = [DayPlan(**d) for d in data.get("days", [])]
        fuel_config = FuelConfig(**data.get("fuel_config", {}))
        return cls(
            name=data["name"],
            stops=stops,
            checklist=checklist,
            days=days,
            fuel_config=fuel_config,
        )
