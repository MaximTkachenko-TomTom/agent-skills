#!/usr/bin/env python3

# Copyright (C) 2022 TomTom NV. All rights reserved.
#
# This software is the proprietary copyright of TomTom NV and its subsidiaries and may be
# used for internal evaluation purposes or commercial use strictly subject to separate
# license agreement between you and TomTom NV. If you are the licensee, you are only permitted
# to use this software in accordance with the terms of your license agreement. If you are
# not the licensee, you are not authorized to use this software in any manner and should
# immediately return or destroy it.

import json
import math
import re

def degToRad(deg):
    return math.radians(deg)

def radToDeg(rad):
    return math.degrees(rad) % 360.0

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(degToRad, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2.0)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2.0)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km * 1000


def unwrap_heading(heading1, heading2):
    min_heading = -180
    max_heading = 180
    full_rotation = 360

    unwrapped_heading2 = heading2
    while unwrapped_heading2 - heading1 < min_heading:
        unwrapped_heading2 += full_rotation
    while unwrapped_heading2 - heading1 >= max_heading:
        unwrapped_heading2 -= full_rotation
    return unwrapped_heading2


def angle_diff(heading1, heading2):
    return unwrap_heading(heading1, heading2) - heading1

# point in format of [long, lat]
def longitude_scaling_factor(point1, point2):
    average_lat = (point1[1] + point2[1]) * 0.5
    lng_scaling_factor = math.cos(average_lat * 2 * math.pi / 360)
    return lng_scaling_factor

def map_distance2(point1, point2, lng_scaling_factor=None):
    if not lng_scaling_factor:
        lng_scaling_factor = longitude_scaling_factor(point1, point2)

    eps = 1e-10
    delta = [point1[0] - point2[0], point1[1] - point2[1]]
    is_too_close = abs(delta[0]) < eps and abs(delta[1]) < eps
    if is_too_close:
        return 0

    delta[0] *= lng_scaling_factor

    # Earth circumference is about 40000km, (4e7/360)^2
    equator_deg_to_meter2 = 1.234567901234568e+10
    dist2 = (delta[0] * delta[0] + delta[1] * delta[1]) * equator_deg_to_meter2

    return dist2

def map_distance(point1, point2):
    return math.sqrt(map_distance2(point1, point2))

def project(point, segment_tail, segment_head):
    lng_scaling_factor = longitude_scaling_factor(segment_tail, segment_head)

    n_delta = [segment_head[0] - segment_tail[0], segment_head[1] - segment_tail[1]]
    n_delta[0] *= lng_scaling_factor
    p_delta = [point[0] - segment_tail[0], point[1] - segment_tail[1]]
    p_delta[0] *= lng_scaling_factor

    n_norm = n_delta[0] * n_delta[0] + n_delta[1] * n_delta[1]
    if n_norm == 0:
        projection = segment_tail
        fraction = 0
        dist2 = map_distance2(segment_tail, point, lng_scaling_factor)
        return dist2, fraction, projection

    reciprocal_norm2 = 1.0 / n_norm
    if reciprocal_norm2 > 1.0 / 1e-15:
        projection = segment_tail
        fraction = 0
        dist2 = map_distance2(segment_tail, point, lng_scaling_factor)
        return dist2, fraction, projection

    pn_dot_product = n_delta[0] * p_delta[0] + n_delta[1] * p_delta[1]
    fraction = pn_dot_product * reciprocal_norm2
    fraction = min(fraction, 1)
    fraction = max(fraction, 0)

    projection = [segment_tail[0] + fraction * (segment_head[0] - segment_tail[0]),
                  segment_tail[1] + fraction * (segment_head[1] - segment_tail[1])]

    dist2 = map_distance2(projection, point, lng_scaling_factor)

    return dist2, fraction, projection

# Heading in degrees CW from North at point (1) towards point (2) along a great circle
def greatCircleHeading(lon1, lat1, lon2, lat2):
    lat1, lat2, delta_lon = map(degToRad, [lat1, lat2, lon2 - lon1])
    y = math.sin(delta_lon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
    return radToDeg(math.atan2(y, x))

def find_coordinates(line):
    lat	= float(re.findall(r'lat="([^"]+)',line)[0])
    lon = float(re.findall(r'lon="([^"]+)',line)[0])
    return {'latitude': lat, 'longitude': lon}

# Convert a list of coordinates into the expected list of dict
def convert_coordinates(geometry):
    points = []
    for geo in geometry:
        points.append({'latitude': geo[1], 'longitude': geo[0]})
    return points

def get_route(json_filename, leg_index=0):
    with open(json_filename) as f:
        data = json.load(f)

    if "routes" not in data:
        raise "No routes in data"
    route = data["routes"][0]
    if "legs" not in route:
        raise "No legs in route"

    legs = route['legs']
    if leg_index >= 0 and leg_index < len(route["legs"]):
        points = legs[leg_index]['points']
    else:
        points = []
        for leg in route["legs"]:
            for point in leg["points"]:
                points.append(point)
    if len(points) < 2:
        raise "Not enough points in a route"
    return points

def create_ttp_file(points, output_ttp, utc_s, speed_mps, start_ts=None, stop_ts=None):
    step_s = 1.0
    timestamp_s = 1
    current_ind = 0
    prev_lat = points[current_ind]['latitude']
    prev_lon = points[current_ind]['longitude']
    current_lat = prev_lat
    current_lon = prev_lon
    next_lat = points[current_ind + 1]['latitude']
    next_lon = points[current_ind + 1]['longitude']
    current_segment_length_m = haversine(prev_lon, prev_lat, next_lon, next_lat)
    current_segment_covered_m = 0
    current_heading_deg = greatCircleHeading(prev_lon, prev_lat, next_lon, next_lat)
    done = False
    with open(output_ttp, 'w') as f:
        f.write("BEGIN:ApplicationVersion=TomTom Positioning 0.7\n")
        f.write("0.0,245,0,SENSOR=Location\n")
        while True:

# 0.000,245,0,SENSOR=Location,src=3,period=1.000
# 15933.351,245,0,4.957784077,1.281999946,52.27406491,1.281999946,46.579,,338.7088013,,28.51600075
# ,,,,,,1695920465.103,3,3,6,3,,,A,,17,,

            channel = 0
            acc = 5.0
            alt = 0.0
            lane_count = ""
            lane_driven = ""

            skip_before = start_ts != None and timestamp_s < start_ts
            skip_after = stop_ts != None and timestamp_s > stop_ts
            if not skip_before and not skip_after:
                f.write(f"{timestamp_s},{245},{channel},{current_lon},{acc},{current_lat},{acc}")
                f.write(f",{alt},,{current_heading_deg},,{speed_mps}")
                f.write(f",,,,,,{utc_s},3,3,{lane_count},{lane_driven},,,,,,,\n")
            if done:
                break
            timestamp_s += step_s
            utc_s += step_s
            step_distance_m = step_s * speed_mps
            current_segment_covered_m += step_distance_m
            while  current_segment_covered_m >= current_segment_length_m:
                current_ind += 1
                extra_m = current_segment_covered_m - current_segment_length_m
                if current_ind + 2 >= len(points):
                    # Reached end
                    current_lat = points[len(points) - 1]['latitude']
                    current_lon = points[len(points) - 1]['longitude']
                    speed_mps = 0
                    done = True
                    break
                prev_lat = points[current_ind]['latitude']
                prev_lon = points[current_ind]['longitude']
                next_lat = points[current_ind + 1]['latitude']
                next_lon = points[current_ind + 1]['longitude']
                current_segment_length_m = haversine(prev_lon, prev_lat, next_lon, next_lat)
                current_segment_covered_m = extra_m
                current_heading_deg = greatCircleHeading(prev_lon, prev_lat, next_lon, next_lat)
            ratio = current_segment_covered_m / current_segment_length_m
            current_lat = prev_lat + ratio * (next_lat - prev_lat)
            current_lon = prev_lon + ratio * (next_lon - prev_lon)
        f.write("END")
