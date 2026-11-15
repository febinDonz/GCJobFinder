"""Build canada-map.js: simplified province outlines plus flag positions.

    python3 tools/build_map.py

Input:  tools/canada-provinces.geojson (Natural Earth admin-1 boundaries, public domain,
        as redistributed by the Click That Hood project).
Output: canada-map.js (window.CANADA_MAP), loaded by the site before app.js.
Pure standard library: Lambert conformal conic projection + Douglas-Peucker simplification.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 640
TOLERANCE = 0.7          # simplification tolerance in output pixels
MIN_AREA = 9.0           # drop islands smaller than this (px^2), except KEEP_ALL provinces
KEEP_ALL = {"PE", "NS", "NB"}

CODES = {"Quebec": "QC", "Newfoundland and Labrador": "NL", "British Columbia": "BC", "Nunavut": "NU",
         "Northwest Territories": "NT", "New Brunswick": "NB", "Nova Scotia": "NS", "Saskatchewan": "SK",
         "Alberta": "AB", "Prince Edward Island": "PE", "Yukon Territory": "YT", "Manitoba": "MB",
         "Ontario": "ON"}
NAMES = {"YT": "Yukon", "NT": "Northwest Territories"}

# Flag centres as (longitude, latitude). Small Atlantic provinces get a flag placed offshore
# plus a leader line to the province itself (target lon/lat).
FLAGS = {
    "YT": (-135.6, 63.6), "NT": (-120.0, 65.2), "NU": (-91.0, 68.0), "BC": (-125.6, 54.8),
    "AB": (-114.6, 55.2), "SK": (-106.2, 54.8), "MB": (-98.4, 55.6), "ON": (-85.5, 50.8),
    "QC": (-72.5, 51.8), "NL": (-61.8, 53.6),
    "NB": (-69.2, 44.0), "PE": (-60.6, 48.9), "NS": (-60.2, 43.6),
}
LEADERS = {"NB": (-66.4, 46.6), "PE": (-63.2, 46.4), "NS": (-63.0, 45.0)}


def lcc(lon, lat, lon0=-95.0, lat0=49.0, p1=49.0, p2=77.0):
    r = math.radians
    n = math.log(math.cos(r(p1)) / math.cos(r(p2))) / math.log(
        math.tan(math.pi / 4 + r(p2) / 2) / math.tan(math.pi / 4 + r(p1) / 2))
    f = math.cos(r(p1)) * math.tan(math.pi / 4 + r(p1) / 2) ** n / n
    rho = f / math.tan(math.pi / 4 + r(lat) / 2) ** n
    rho0 = f / math.tan(math.pi / 4 + r(lat0) / 2) ** n
    theta = n * r(lon - lon0)
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def dp(points, tol):
    if len(points) < 3:
        return points
    (x1, y1), (x2, y2) = points[0], points[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy) or 1e-9
    best, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        d = abs(dy * points[i][0] - dx * points[i][1] + x2 * y1 - y2 * x1) / norm
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [points[0], points[-1]]
    return dp(points[:idx + 1], tol)[:-1] + dp(points[idx:], tol)


def simplify_ring(ring, tol):
    """Simplify a closed ring: split at the point farthest from the start so the
    two halves are open lines (Douglas-Peucker collapses a closed ring otherwise)."""
    pts = ring[:-1] if ring[0] == ring[-1] else ring[:]
    if len(pts) < 4:
        return pts
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
    first = dp(pts[:far + 1], tol)
    second = dp(pts[far:] + [pts[0]], tol)
    return first[:-1] + second[:-1]


def area(ring):
    return abs(sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1]
                   for i in range(len(ring)))) / 2


def main():
    data = json.loads((ROOT / "tools" / "canada-provinces.geojson").read_text(encoding="utf-8"))
    raw = {}
    for feature in data["features"]:
        code = CODES[feature["properties"]["name"]]
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        raw[code] = [[[lcc(lon, lat) for lon, lat in ring] for ring in poly] for poly in polys]
    xs = [x for polys in raw.values() for poly in polys for ring in poly for x, _ in ring]
    ys = [y for polys in raw.values() for poly in polys for ring in poly for _, y in ring]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    scale = WIDTH / (maxx - minx)
    height = round((maxy - miny) * scale)

    def to_px(pt):
        return ((pt[0] - minx) * scale, (maxy - pt[1]) * scale)

    def project(lon, lat):
        return to_px(lcc(lon, lat))

    provinces = []
    for code, polys in raw.items():
        d = []
        for poly in polys:
            ring = [to_px(p) for p in poly[0]]
            if area(ring) < MIN_AREA and code not in KEEP_ALL:
                continue
            ring = simplify_ring(ring, TOLERANCE if code not in KEEP_ALL else 0.35)
            if len(ring) < 3:
                continue
            d.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in ring) + "Z")
        fx, fy = project(*FLAGS[code])
        entry = {"code": code, "d": "".join(d), "fx": round(fx, 1), "fy": round(fy, 1)}
        if code in LEADERS:
            lx, ly = project(*LEADERS[code])
            entry["leader"] = [round(lx, 1), round(ly, 1)]
        provinces.append(entry)
    out = {"w": WIDTH, "h": height, "provinces": sorted(provinces, key=lambda p: p["code"])}
    js = "/* Generated by tools/build_map.py from Natural Earth boundaries. Do not edit. */\nwindow.CANADA_MAP = " \
         + json.dumps(out, separators=(",", ":")) + ";\n"
    (ROOT / "canada-map.js").write_text(js, encoding="utf-8")
    print(f"canada-map.js: {len(js) / 1024:.1f} KB, viewBox {WIDTH}x{height}")


if __name__ == "__main__":
    main()
