import csv
import json
import math
import sys
from pathlib import Path

# GMRS UHF Default Mobile Coverage Radii (in miles)
LOCAL_RADIUS_MILES = 18.0
WIDE_AREA_RADIUS_MILES = 30.0

def generate_circle_coords(lat, lon, radius_miles, num_points=48):
    """Calculates [lon, lat] pairs forming a geodesic circle."""
    r_earth = 3958.8  # Earth radius in miles
    lat_r, lon_r = math.radians(lat), math.radians(lon)
    d_r = radius_miles / r_earth

    coords = []
    for i in range(num_points + 1):
        bearing = math.radians((360 / num_points) * i)
        target_lat = math.asin(
            math.sin(lat_r) * math.cos(d_r) +
            math.cos(lat_r) * math.sin(d_r) * math.cos(bearing)
        )
        target_lon = lon_r + math.atan2(
            math.sin(bearing) * math.sin(d_r) * math.cos(lat_r),
            math.cos(d_r) - math.sin(lat_r) * math.sin(target_lat)
        )
        coords.append([round(math.degrees(target_lon), 6), round(math.degrees(target_lat), 6)])
    return coords

def parse_mygmrs_csv(filepath):
    repeaters = []
    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            city = row.get("City", "").strip()
            state = row.get("State", "").strip()
            call = row.get("Callsign", "").strip()
            if not call:
                call = f"GMRS-{city}" if city else "GMRS-Repeater"

            try:
                lat = float(row.get("Latitude", 0))
                lon = float(row.get("Longitude", 0))
                freq = float(row.get("Frequency (MHz)", 0))
            except (ValueError, TypeError):
                continue

            if lat == 0.0 and lon == 0.0:
                continue

            # Offset formatting
            offset_val = row.get("Offset (MHz)", "5.0")
            offset_str = f"+{float(offset_val):.1f} MHz" if offset_val else "+5.0 MHz"

            # Tone handling
            tone = row.get("Tone") or row.get("PL Tone") or "CSQ"
            tsq = row.get("TSQ Tone", "")

            # Coverage radius strictly from Wide Area column
            is_wide_area = str(row.get("Wide Area", "")).strip().lower() == "yes"
            radius = WIDE_AREA_RADIUS_MILES if is_wide_area else LOCAL_RADIUS_MILES

            repeaters.append({
                "callsign": call,
                "frequency": f"{freq:.3f}",
                "offset": offset_str,
                "tone": tone.strip(),
                "tsq": tsq.strip(),
                "city": city,
                "state": state,
                "wide_area": is_wide_area,
                "lat": lat,
                "lon": lon,
                "radius_miles": radius
            })

    return repeaters

def export_kml(repeaters, out_path="gmrs_coverage.kml"):
    kml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        '    <name>myGMRS Repeater Coverage</name>',
        '    <!-- Lighter Purple for 18-mile Standard Local -->',
        '    <Style id="localBubble">',
        '      <LineStyle><color>fffc84c0</color><width>2</width></LineStyle>',
        '      <PolyStyle><color>33fc84c0</color></PolyStyle>',
        '      <IconStyle><scale>0.8</scale></IconStyle>',
        '    </Style>',
        '    <!-- Blue/Teal for 30-mile Wide Area -->',
        '    <Style id="wideBubble">',
        '      <LineStyle><color>ffffaa00</color><width>2</width></LineStyle>',
        '      <PolyStyle><color>33ffaa00</color></PolyStyle>',
        '      <IconStyle><scale>0.8</scale></IconStyle>',
        '    </Style>'
    ]

    for r in repeaters:
        circle_points = generate_circle_coords(r["lat"], r["lon"], r["radius_miles"])
        coord_str = " ".join([f"{pt[0]},{pt[1]},0" for pt in circle_points])
        style_id = "#wideBubble" if r["wide_area"] else "#localBubble"

        desc = (
            f"<b>Location:</b> {r['city']}, {r['state']}<br/>"
            f"<b>Output:</b> {r['frequency']} MHz<br/>"
            f"<b>Offset:</b> {r['offset']}<br/>"
            f"<b>PL Tone:</b> {r['tone']} Hz<br/>"
            f"<b>TSQ Tone:</b> {r['tsq']}<br/>"
            f"<b>Coverage:</b> {'Wide Area (~30 mi)' if r['wide_area'] else 'Standard Local (~18 mi)'}"
        )

        kml.append(f"""
    <Placemark>
      <name>{r['callsign']} ({r['frequency']})</name>
      <description><![CDATA[{desc}]]></description>
      <styleUrl>{style_id}</styleUrl>
      <MultiGeometry>
        <Point>
          <coordinates>{r['lon']},{r['lat']},0</coordinates>
        </Point>
        <Polygon>
          <tessellate>1</tessellate>
          <outerBoundaryIs>
            <LinearRing><coordinates>{coord_str}</coordinates></LinearRing>
          </outerBoundaryIs>
        </Polygon>
      </MultiGeometry>
    </Placemark>""")

    kml.append('  </Document>\n</kml>')
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(kml))
    print(f"Generated KML: {out_path} ({len(repeaters)} features)")

def export_geojson(repeaters, out_path="gmrs_coverage.geojson"):
    features = []
    for r in repeaters:
        # Tower Pin
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "type": "tower",
                "callsign": r["callsign"],
                "frequency": r["frequency"],
                "offset": r["offset"],
                "tone": r["tone"],
                "city": r["city"],
                "state": r["state"],
                "wide_area": r["wide_area"],
                "radius_miles": r["radius_miles"]
            }
        })
        # Bubble Polygon
        circle_coords = generate_circle_coords(r["lat"], r["lon"], r["radius_miles"])
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [circle_coords]},
            "properties": {
                "type": "coverage_bubble",
                "callsign": r["callsign"],
                "frequency": r["frequency"],
                "wide_area": r["wide_area"]
            }
        })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
    print(f"Generated GeoJSON: {out_path}")

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "myGMRS_20261027_data_pull.csv"
    if not Path(csv_file).exists():
        print(f"Cannot find {csv_file}")
        sys.exit(1)

    data = parse_mygmrs_csv(csv_file)
    export_kml(data)
    export_geojson(data)