# GMRS Repeater Coverage Map Generator

A Python tool that converts raw myGMRS repeater export data into visual coverage maps (`.kml` and `.geojson`). 

It calculates geographic line-of-sight coverage circles around each repeater site, allowing operators to visually track repeater handoffs on Google My Maps, Google Earth, or custom mobile dashboards.

---

## Features

- **Automated Polygon Generation:** Computes geodesic circle boundaries around each repeater site.
- **Visual Classification:**
  - **Light Purple Circles (~18-mile radius):** Standard local UHF GMRS repeaters.
  - **Blue/Teal Circles (~30-mile radius):** Wide-area, mountain-top, or high-elevation installations.
- **My Maps Compliant (`<MultiGeometry>`):** Binds each pin and its range polygon into a single feature, fitting entire multi-state directories under Google My Maps' strict 2,000-feature import ceiling.
- **Dual Export:** Outputs both `.kml` (for Google My Maps / Google Earth) and `.geojson` (for mobile apps and web maps).

---

## File Structure

```text
├── myGMRS_20261027_data_pull.csv   # Raw input data
├── parse_mygmrs.py                  # Processing script
├── gmrs_coverage.kml                # Generated KML output
├── gmrs_coverage.geojson            # Generated GeoJSON output
└── README.md
```

---

## Requirements
Python 3.8 or higher.

Built strictly with Python standard library modules (csv, json, math, sys, pathlib). No external package installations (pip) are required.

---

## Instructions
Step 1: Run the Script
Place your raw CSV in the project folder and run the script from your terminal:

python parse_mygmrs.py myGMRS_20261027_data_pull.csv

(If executed without arguments, it defaults to looking for myGMRS_20261027_data_pull.csv in the current directory).

The script will output two files:

gmrs_coverage.kml

gmrs_coverage.geojson

Step 2: Import into Google My Maps (Browser)
Open your desktop web browser and navigate to Google My Maps.

Click Create a New Map.

Under the untitled layer on the left card, click Import.

Drag and drop or browse to select gmrs_coverage.kml.

Rename the map title (e.g., GMRS Travel Coverage).

Click any pin or circle boundary to verify the pop-up data card (Output Frequency, Duplex Offset, PL Tone, TSQ Tone, City, and State).

Step 3: View While Driving in Google Maps (Android / iOS)
Once imported into My Maps, the layer is permanently linked to your Google account and accessible inside the standard Google Maps navigation app:

Open the standard Google Maps app on your phone.

Tap the Saved tab at the bottom navigation bar.

Scroll down to the bottom and select Maps.

Tap your imported map name (e.g., GMRS Travel Coverage).

The map overlay will load onto your road navigation view. As you drive, your vehicle's blue location dot will show your real-time position inside and outside the repeater coverage bubbles.

Step 4: Alternative Viewing in Google Earth
Open Google Earth (Web, Desktop, or Mobile App).

Navigate to Projects > Open > Import KML file from computer / device.

Select gmrs_coverage.kml to display full 3D terrain topography and elevation contours under the coverage bubbles.

---

## Expected CSV Data Schema
The script parses standard myGMRS directory exports with the following column headers:

Header			|	Type		|  Description
Callsign		|	String		|  Repeater FCC callsign (defaults to GMRS-[City] if blank)
Frequency (MHz)	|	Float		|  Repeater output / listening frequency
Offset (MHz)	|	Float		|  Duplex split (defaults to +5.0 MHz for standard GMRS repeaters)
Tone or PL Tone	|	String		|  Uplink CTCSS / PL Tone required to open the machine
TSQ Tone		|	String		|  Downlink Tone Squelch (if configured)
Latitude		|	Float		|  Decimal latitude coordinates
Longitude		|	Float		|  Decimal longitude coordinates
Wide Area		|	String		|  If marked Yes, radius increases to 30 miles (Teal). Blank defaults to 18 miles (Purple).

---

## Technical Notes
- **Google My Maps Limits:** My Maps restricts single layer imports to 2,000 features. Standard KML structures generate 1 feature for the point and 1 feature for the polygon ($1,683 \times 2 = 3,366$), causing upload failures. This pipeline wraps both inside <MultiGeometry> per <Placemark>, keeping the count at exactly 1 feature per repeater.
- **Coverage Estimation:** Radii are calculated approximations based on mobile UHF propagation to vehicle-mounted 5/8-wave antennas. Terrain obstructions, hills, and local building density will affect physical line-of-sight.

---

## License & Usage Notice
This utility is provided for amateur and personal radio operators for route planning and travel coordination. Repeater directory coordination records remain the property of their respective sources.