---
name: count-lln-sessions
description: Count the number of LLN (Lane Level Navigation) sessions that will be triggered during navigation for a given TomTom route JSON file.
---

# How LLN Sessions Are Triggered

An LLN session starts when `LaneLevelGuidanceInternal` transitions from `null` to non-null inside `LaneLevelGuidanceProcessor`. This happens when the native engine generates lane guidance at a **motorway instruction**'s route offset, and lane map data is available there.

**Motorway instruction types** (the only ones that can trigger sessions):

| JSON `maneuver` value | → SDK Instruction class |
|---|---|
| `EXIT_MOTORWAY_LEFT/RIGHT/MIDDLE` | `ExitHighwayInstruction` |
| `SWITCH_MOTORWAY_LEFT/RIGHT/MIDDLE` | `SwitchHighwayInstruction` |
| `KEEP_LEFT`, `KEEP_RIGHT`, `KEEP_CENTER` | `ForkInstruction` |

**`WAYPOINT_REACHED`**, **`MERGE_*_LANE`**, **`TURN_*`**, **`DEPART`**, **`ARRIVE_*`** — these do NOT trigger LLN sessions.

A session fires only when **both** conditions are true:
1. A qualifying motorway instruction is in `InstructionPhase.Main` or `Confirmation`
2. A **LANES section** exists that covers the instruction's `routeOffsetInMeters`

# Task

Given a route JSON file path (user provides it), run the following Python script and report the findings.

```python
import json, math, sys

MOTORWAY_MANEUVERS = {
    "EXIT_MOTORWAY_LEFT", "EXIT_MOTORWAY_RIGHT", "EXIT_MOTORWAY_MIDDLE",
    "SWITCH_MOTORWAY_LEFT", "SWITCH_MOTORWAY_RIGHT", "SWITCH_MOTORWAY_MIDDLE",
    "KEEP_LEFT", "KEEP_RIGHT", "KEEP_CENTER",
}

# Tolerance to account for rounding differences between routing API offsets
# and haversine-computed cumulative distances from polyline decoding.
TOLERANCE_M = 100

def decode_polyline(encoded, precision=7):
    factor = 10 ** precision
    result, index, lat, lng = [], 0, 0, 0
    while index < len(encoded):
        for coord in [0, 1]:
            shift = result_val = 0
            while True:
                b = ord(encoded[index]) - 63; index += 1
                result_val |= (b & 0x1f) << shift; shift += 5
                if b < 0x20: break
            if result_val & 1: result_val = ~result_val
            result_val >>= 1
            if coord == 0: lat += result_val
            else: lng += result_val; result.append((lat / factor, lng / factor))
    return result

def haversine_m(p1, p2):
    R = 6371000
    lat1, lon1, lat2, lon2 = math.radians(p1[0]), math.radians(p1[1]), math.radians(p2[0]), math.radians(p2[1])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def build_cum_dist(points):
    d = [0.0]
    for i in range(1, len(points)): d.append(d[-1] + haversine_m(points[i-1], points[i]))
    return d

def count_lln_sessions(route_json_path):
    with open(route_json_path) as f:
        data = json.load(f)

    route = data["routes"][0]

    # Decode polyline from all legs (concatenating, skip first point of each subsequent leg)
    all_points = []
    for leg in route.get("legs", []):
        pts = decode_polyline(leg["encodedPolyline"], leg.get("encodedPolylinePrecision", 7))
        if all_points: pts = pts[1:]
        all_points.extend(pts)

    cum_dist = build_cum_dist(all_points)

    # Convert LANES section point-index ranges to cumulative distance ranges
    lanes_ranges = []
    def add_lanes(sections_list):
        for s in sections_list:
            if s.get("sectionType") == "LANES":
                si = max(0, s["startPointIndex"])
                ei = min(s["endPointIndex"], len(cum_dist) - 1)
                lanes_ranges.append((cum_dist[si], cum_dist[ei]))

    add_lanes(route.get("sections", []))
    for leg in route.get("legs", []):
        add_lanes(leg.get("sections", []))

    instructions = route.get("guidance", {}).get("instructions", [])
    motorway_instrs = [i for i in instructions if i["maneuver"] in MOTORWAY_MANEUVERS]

    sessions, no_lanes = [], []
    for instr in motorway_instrs:
        offset = instr["routeOffsetInMeters"]
        in_lanes = any(start - TOLERANCE_M <= offset <= end + TOLERANCE_M for start, end in lanes_ranges)
        (sessions if in_lanes else no_lanes).append(instr)

    print(f"\n{'='*60}")
    print(f"Route file: {route_json_path}")
    print(f"Total points  : {len(all_points)}, route length: {cum_dist[-1]:.0f}m")
    print(f"LANES sections: {len(lanes_ranges)}")
    print(f"Motorway instrs: {len(motorway_instrs)}")
    print(f"\n✅ Expected LLN sessions: {len(sessions)}")
    for s in sessions:
        print(f"   {s['maneuver']:35s} @ {s['routeOffsetInMeters']:7.0f}m")
    if no_lanes:
        print(f"\n⚠️  Motorway instructions WITHOUT lane data ({len(no_lanes)}) — no session:")
        for n in no_lanes:
            print(f"   {n['maneuver']:35s} @ {n['routeOffsetInMeters']:7.0f}m")
    print(f"\n{'='*60}")

if __name__ == "__main__":
    count_lln_sessions(sys.argv[1])
```

Write the script to `/tmp/count_lln_sessions.py`, then run it with:
```bash
python3 /tmp/count_lln_sessions.py <path_to_route.json>
```

Then report:
- Total LANES sections in the file
- Motorway instructions found (type + offset)
- How many will likely trigger LLN sessions (covered by a LANES section)
- Which motorway instructions have no LANES coverage (won't trigger)
