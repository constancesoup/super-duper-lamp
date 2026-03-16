# Roadtrip Planner

A command-line tool for planning road trips. Manage stops, calculate distances, estimate fuel costs, track packing lists, and organize daily itineraries.

## Install

```bash
pip install -e .
```

## Usage

### Create and manage trips

```bash
roadtrip new summer2026
roadtrip list
```

### Add stops

```bash
roadtrip stop add summer2026 "Denver, CO" 39.7392 -104.9903
roadtrip stop add summer2026 "Moab, UT" 38.5733 -109.5498
roadtrip stop add summer2026 "Las Vegas, NV" 36.1699 -115.1398
roadtrip stop list summer2026
```

### View trip summary

```bash
roadtrip summary summer2026
```

Output:
```
Trip: summer2026
Stops: 3

  Leg 1: Denver, CO -> Moab, UT — 278.4 mi (~4h 38m)
  Leg 2: Moab, UT -> Las Vegas, NV — 327.4 mi (~5h 27m)

  Total distance: 605.8 miles
  Total drive time: ~10h 5m
  Fuel needed: 24.2 gallons
  Estimated fuel cost: $84.81

  Note: Distances are straight-line estimates.
```

### Fuel configuration

```bash
roadtrip fuel summer2026 --mpg 30 --price 3.25
```

### Packing checklist

```bash
roadtrip checklist add summer2026 "Sunscreen"
roadtrip checklist add summer2026 "Cooler"
roadtrip checklist check summer2026 0
roadtrip checklist show summer2026
```

### Daily itinerary

```bash
roadtrip day add summer2026 1 0 1      # Day 1: stops 0 → 1
roadtrip day add summer2026 2 1 2      # Day 2: stops 1 → 2
roadtrip day show summer2026
```

## Data storage

Trips are saved as JSON files in `~/.roadtrip/`. You can also specify a file path directly:

```bash
roadtrip new /path/to/my-trip.json
```

## Running tests

```bash
python -m unittest discover -s tests
```

## Notes

- Distances use the Haversine formula (straight-line). Actual driving distances will be longer.
- Default fuel config: 25 MPG, $3.50/gallon. Adjust with `roadtrip fuel`.
