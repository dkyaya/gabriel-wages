"""Convert a local Census state cartographic-boundary archive to dashboard GeoJSON.

This utility performs no network access. Download the documented Census archive
separately, then pass its local path as the only positional argument.
"""

import argparse
import json
import struct
import zipfile
from pathlib import Path


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = DASHBOARD_ROOT / "src/assets/us-states-2025-20m.geojson"
STATE_SUMMARY = DASHBOARD_ROOT / "data/state_summary.json"


def read_dbf(data):
    record_count = struct.unpack_from("<I", data, 4)[0]
    header_length = struct.unpack_from("<H", data, 8)[0]
    record_length = struct.unpack_from("<H", data, 10)[0]
    fields = []
    offset = 32
    while data[offset] != 0x0D:
        descriptor = data[offset : offset + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("ascii")
        fields.append((name, descriptor[16]))
        offset += 32

    records = []
    for index in range(record_count):
        start = header_length + index * record_length
        record = data[start : start + record_length]
        cursor = 1
        values = {}
        for name, length in fields:
            values[name] = record[cursor : cursor + length].decode("utf-8").strip()
            cursor += length
        records.append(values)
    return records


def ring_area(ring):
    return sum(
        ring[index][0] * ring[index + 1][1] - ring[index + 1][0] * ring[index][1]
        for index in range(len(ring) - 1)
    ) / 2


def read_shapes(data):
    records = []
    offset = 100
    while offset < len(data):
        _, content_words = struct.unpack_from(">2i", data, offset)
        content = data[offset + 8 : offset + 8 + content_words * 2]
        shape_type = struct.unpack_from("<i", content, 0)[0]
        if shape_type != 5:
            raise ValueError(f"Unexpected shapefile record type {shape_type}; expected Polygon (5)")
        part_count, point_count = struct.unpack_from("<2i", content, 36)
        part_starts = list(struct.unpack_from(f"<{part_count}i", content, 44))
        points_offset = 44 + 4 * part_count
        points = [
            [round(x, 5), round(y, 5)]
            for x, y in struct.iter_unpack("<2d", content[points_offset : points_offset + point_count * 16])
        ]
        rings = [
            points[start : part_starts[index + 1] if index + 1 < part_count else point_count]
            for index, start in enumerate(part_starts)
        ]
        polygons = []
        for ring in rings:
            if ring_area(ring) < 0 or not polygons:
                polygons.append([ring])
            else:
                polygons[-1].append(ring)
        records.append({
            "type": "Polygon" if len(polygons) == 1 else "MultiPolygon",
            "coordinates": polygons[0] if len(polygons) == 1 else polygons,
        })
        offset += 8 + content_words * 2
    return records


def archive_member(archive, suffix):
    matches = [name for name in archive.namelist() if name.lower().endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one {suffix} member in archive; found {matches}")
    return matches[0]


def build_geojson(archive_path, output_path):
    allowed_codes = {
        state["state"]
        for state in json.loads(STATE_SUMMARY.read_text())["states"]
    }
    with zipfile.ZipFile(archive_path) as archive:
        dbf = read_dbf(archive.read(archive_member(archive, ".dbf")))
        shapes = read_shapes(archive.read(archive_member(archive, ".shp")))

    features = []
    for properties, geometry in zip(dbf, shapes, strict=True):
        if properties["STUSPS"] not in allowed_codes:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "GEOID": properties["GEOID"],
                "STUSPS": properties["STUSPS"],
                "NAME": properties["NAME"],
            },
            "geometry": geometry,
        })

    features.sort(key=lambda feature: feature["properties"]["STUSPS"])
    actual_codes = {feature["properties"]["STUSPS"] for feature in features}
    if actual_codes != allowed_codes:
        raise ValueError(f"Boundary/dashboard state-code mismatch: missing={allowed_codes - actual_codes}, extra={actual_codes - allowed_codes}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")) + "\n")
    print(f"Wrote {len(features)} state/DC features to {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Local Census state cartographic-boundary ZIP")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_geojson(args.archive, args.output)


if __name__ == "__main__":
    main()
