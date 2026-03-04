#!/usr/bin/env python3

# Copyright (C) 2022 TomTom NV. All rights reserved.
#
# This software is the proprietary copyright of TomTom NV and its subsidiaries and may be
# used for internal evaluation purposes or commercial use strictly subject to separate
# license agreement between you and TomTom NV. If you are the licensee, you are only permitted
# to use this software in accordance with the terms of your license agreement. If you are
# not the licensee, you are not authorized to use this software in any manner and should
# immediately return or destroy it.

import argparse
from generic_functions_for_converters import *
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--gpx_file', required=True, type=argparse.FileType('r'), help='gpx file will be converted to ttp format')
parser.add_argument('--ttp', required=False, help='Output filename to write ttp file')
parser.add_argument('--speed', required=False, help='Speed in m/s of generated ttp file, if not provided, 20 is used.')

args = parser.parse_args()
speed_mps = float(args.speed) if args.speed else 20
gpx_file = args.gpx_file
if not args.ttp:
    output_ttp = str(gpx_file).split("'")[1].replace("gpx","ttp")
else:
    output_ttp = args.ttp


points = []
for line in gpx_file:
    if "<trkpt" in line:
        points.append(find_coordinates(line))

utc_ts = datetime.now().timestamp()

create_ttp_file(points, output_ttp, utc_ts, speed_mps)
