# How to Read TTP Log Files - Summary

## Overview
TTP (TomTom Positioning) is a positioning and sensor data logging format used to capture location, sensor, and system telemetry information. TTP log files have evolved through multiple versions to accommodate improvements in the positioning engine.

## Version History
The format has been updated since version 0.1, with the current version being 0.12. Key updates include:
- **v0.12** (current): Extended Location event with turn light indicator status
- **v0.11**: Added vehicle ignition event
- **v0.10**: Added 6D-IMU and 6D-IMU configuration events
- **v0.8**: Added multi-wheel ticks data and wheel configurations
- **v0.4**: Added Tachometer and Wheel tick data
- **v0.1**: Initial release

## Glossary
| Term | Definition |
|------|-----------|
| TTP | TomTom Positioning |
| GNSS | Global Navigation Satellite System |
| IMU | Inertial Measurement Unit |
| PPS | Pulse Per Second |

## File Format Structure

### Overall Structure
A TTP log file follows this basic structure:
```
BEGIN:ApplicationVersion = <version>
<data lines>
END
```

### Line Format
Most data lines follow this pattern:
- **Timestamp**: Numeric timestamp (seconds, often floating point)
- **Message Type**: Numeric code identifying the sensor/data type
- **Channel**: Integer identifying the sensor channel
- **Data**: Comma-separated values specific to the message type

## Common Message Types

| Message Type | Code | Format Example |
|---|---|---|
| Accelerometer | 163 | `x.x,163,c,x.x,x.x,x.x,...` |
| Barometer | 178 | `x.x,178,x.x,x.x,x.x` |
| Gyroscope | 194 | `x.x,194,x.x,x.x,x.x` |
| PPS (Pulse Per Second) | 208 | `x.x,208` |
| Tacho/Odometer | 209 | `x.x,209,x.x` |
| GNSS Location | 245 | `x.x,245,x.x,x.x,x.x,x.x,x.x,x.x,x.x` |
| 6D-IMU (v0.10+) | 8 | `x.x,8,c,x,...` |
| 6D-IMU Configuration (v0.10+) | 7 | `x.x,7,c,s,x.x,...` |
| Parameters | 17 | `x.x,17,key=value,...` |
| Positioning Configuration | 16 | `x.x,16,string` |
| Map Match Feedback | 62 | `x.x,62,c,x.x,...` |
| Driving Direction | 26 | `x.x,26,c,x` |
| Satellite Data | 246 | `x.x,246,x.x,x.x,x.x,prn,...` |

## Location Message Fields

Format: `x.x,msg,c,x.x,x.x,x.x,x.x,x.x,x.x,x.x,x.x,x.x,x.x,x.x,x.x,x.x,x.x,x.x,q,h...h,x,x,d,m,x,x,d`

| Field No. | Format | Description |
| --- | --- | --- |
| 0 | x.x | Monotonic time of the event (sec) |
| 1 | msg | Location event: 245 (0xF5) - Incoming locations to TomTom Positioning Service; 237 (0xED) - Outgoing locations from TomTom Positioning Service |
| 2 | c | Channel number associated with this event. |
| 3 | x.x | Longitude (deg) |
| 4 | x.x | Longitude Accuracy (m) |
| 5 | x.x | Latitude (deg) |
| 6 | x.x | Latitude Accuracy (m) |
| 7 | x.x | Altitude above sea level (m) |
| 8 | x.x | Altitude Accuracy (m) |
| 9 | x.x | Heading (deg) |
| 10 | x.x | Heading Accuracy (deg) |
| 11 | x.x | Speed (m/s) |
| 12 | x.x | Speed Accuracy (m/s) |
| 13 | x.x | Pitch (deg) |
| 14 | x.x | Pitch Accuracy (deg) |
| 15 | x.x | Traveled distance since last update (m). The distance is negative if vehicle is moving backwards. Otherwise, it is positive. |
| 16 | x.x | Traveled distance accuracy (m) |
| 17 | x.x | UTC time of the fix (seconds since January 1, 1970) |
| 18 | q | Quality of Location Data: 1 - Low accuracy and not suitable for navigation e.g. NETWORK; 3 - Medium accuracy and suitable for navigation e.g. GNSS; 4 - High accuracy and suitable for continuous navigation e.g. Enhanced/DR |
| 19 | h...h | Location Status bitwise hex flags (up to 32 bits): Bit 0 - Medium quality (GNSS) fix valid; Bit 1 - Medium quality (GNSS) fix used (since 16.5); Bit 2-27 - Reserved; Bit 28 - Low quality (NETWORK) fix valid (since 16.5); Bit 29 - Low quality (NETWORK) fix used (since 16.5); Bit 30-31 - Reserved |
| 20 | x | Number of visible lanes |
| 21 | x | ID of used lane assigned from left to right side of the car. The far left passing lane is the number 1. A valid ID must be greater than or equal to one. |
| 22 | x.x | Speedometer readings [m/s] |
| 23 (introduced in v0.6) | d | Intended driving direction at the next intersection: 0 - unknown; 1 - left; 2 - current; 3 - right |
| 24 (introduced in v0.7) | m | Fix mode: 'A' - Autonomous GNSS; 'D' - Differential/SBAS-aided GNSS; 'E' - Estimated (dead reckoning); 'N' - Fix not available; 'M' - Manual Input; 'P' - GNSS PPS; 'F' - RTK float; 'R' - RTK fixed; 'S' - Simulator |
| 25 (introduced in v0.7) | x | Number of satellites in view, or blank if unknown. |
| 26 (introduced in v0.7) | x | Number of satellites used in solution, or blank if unknown. |
| 27 (introduced in v0.7) | x.x | Roll (deg) |
| 28 (introduced in v0.7) | x.x | Roll Accuracy (deg) |
| 29 (introduced in v0.9) | d | Calibration status of the location provider in percentages in the range [0, 100], otherwise invalid. |
| 30 (introduced in v0.12) | d | Turn light indicator status: 0 - off; 1 - Left on; 2 - Right on; 3 - Hazard lights on |

## Key Points

- **Legacy Support**: Old log formats can still be played back, though output is in the newer TTP format
- **Sensor Configuration**: Sensor parameters are defined in configuration lines using message code with "SENSOR = " prefix
- **Timestamps**: Represent time from log start or absolute time depending on context
- **Channels**: Identify which physical sensor provides the data (useful for multi-sensor setups)
- **Parameters**: System and sensor parameters are logged with message code 17, containing key=value pairs
- **Location Messages**: Both GNSS (245) and Positioning Location (237) messages contain similar core fields; Positioning Location includes additional parameters

## Reading TTP Logs

When analyzing TTP logs:
1. Start by examining the header to identify the application version
2. Parse the positioning configuration (message type 16) to understand the logging setup
3. Look for sensor configurations to understand what sensors were active
4. Process sensor data lines in chronological order (by timestamp)
5. Match message codes to the tables above to interpret data
6. Use parameters (message type 17) to understand calibration and configuration details

For map matching specific details, refer to the separate map matching TTP logs documentation.
