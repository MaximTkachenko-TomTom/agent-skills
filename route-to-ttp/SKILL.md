---
name: route-to-ttp
description: Convert a JSON route to TTP file.
---

Given a JSON file with a route (most likely from TomTom routing API), convert it into the TTP file with geo points.

Use `parse-ttp-file` skill to learn about TTP file format.

## File Format Requirements

### Header
The first line **must** match this exact pattern:
```
BEGIN:ApplicationVersion=TomTom Positioning <major>.<minor>
```
Example: `BEGIN:ApplicationVersion=TomTom Positioning 0.12`

> ⚠️ Do NOT write `BEGIN:ApplicationVersion = 0.12` (no spaces around `=`, and the full product name is required).

### Timestamps
- The monotonic timestamp field (first column) **must never be `0`**.
- Start the first entry at `0.100` and increment by `1.000` per second thereafter (i.e. `0.100`, `1.100`, `2.100`, …).

## Route Geometry — encodedPolyline vs points

The routing API response may provide leg geometry in one of two forms:

### encodedPolyline (current — Orbis endpoint)
When `legs[].encodedPolyline` is present, decode it using the standard Google Polyline algorithm scaled by `10^encodedPolylinePrecision` (typically `7`):

```python
def decode_polyline(encoded, precision=7):
    coords = []
    index, lat, lng = 0, 0, 0
    while index < len(encoded):
        for is_lng in (False, True):
            result, shift = 0, 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            value = ~(result >> 1) if result & 1 else result >> 1
            if is_lng:
                lng += value
            else:
                lat += value
        coords.append((lat / 10**precision, lng / 10**precision))
    return coords
```

Concatenate decoded coords across all legs (skip the first point of each subsequent leg to avoid duplicates at waypoints).

### points array (legacy)
When `legs[].points[]` is present, use `{"latitude": ..., "longitude": ...}` directly.

## Speed

### If `SPEED_LIMIT` sections are present
Use the `maxSpeedLimitInKmh` field (converted to m/s) as the speed for each geometry point covered by that section (`startPointIndex` to `endPointIndex` inclusive, indexing into the concatenated all-legs point array). Points not covered by any section fall back to the average speed (`lengthInMeters / travelTimeInSeconds`).

```python
default_speed_ms = total_dist / total_time
speed_at = [default_speed_ms] * len(all_coords)
for s in [s for s in route.get('sections', []) if s.get('sectionType') == 'SPEED_LIMIT']:
    spd = s['maxSpeedLimitInKmh'] / 3.6
    for i in range(s['startPointIndex'], min(s['endPointIndex'] + 1, len(all_coords))):
        speed_at[i] = spd
```

With per-point speeds, compute **cumulative time** (not distance) for interpolation:
```python
cum_times = [0.0]
for i in range(len(all_coords) - 1):
    dist = haversine(*all_coords[i], *all_coords[i+1])
    cum_times.append(cum_times[-1] + dist / speed_at[i])
total_sim_time = cum_times[-1]
```
Then generate one entry per second from `t=1` to `t=ceil(total_sim_time)`, interpolating position by time rather than by distance fraction.

### If no speed data is available
Ask the user: *"No speed limit data found in the route. What speed should I use? (e.g. 50 km/h, or 'average' to use route travel time)"*. Convert their answer to m/s, or use `lengthInMeters / travelTimeInSeconds` for average.

## Interpolation

Route points from the API are sparse. Produce **1 Hz GNSS updates** (one entry per second).

Steps:
1. Build cumulative time array using per-point speeds (see **Speed** section above).
2. For each integer second `t` from `1` to `ceil(total_sim_time)` (inclusive), binary-search `cum_times` to find the bracketing segment, then linearly interpolate lat/lon within that segment.
3. Compute per-entry values:
   - **Heading**: bearing from segment start to segment end, converted to degrees [0, 360).
   - **Speed** (m/s): `speed_at[segment_index]`.
   - **UTC time**: base departure UTC + `t` seconds.
4. Write one `245` message line per second.

