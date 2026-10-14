
import searoute as sr
from math import radians, sin, cos, sqrt, atan2

CHOKEPOINTS = {
    "Suez Canal"          : (30.45,  32.35),
    "Bab el-Mandeb"       : (12.58,  43.32),
    "Strait of Hormuz"    : (26.57,  56.25),
    "Strait of Malacca"   : ( 1.25, 103.82),
    "Panama Canal"        : ( 9.08, -79.68),
    "Strait of Gibraltar" : (35.96,  -5.48),
    "Dover Strait"        : (51.00,   1.50),
    "Cape of Good Hope"   : (-34.36, 18.47),
    "Lombok Strait"       : (-8.75, 115.75),
    "Luzon Strait"        : (20.00, 121.50),
    "Bosphorus Strait"    : (41.12,  29.08),
    "Danish Straits"      : (55.50,  10.50),
    "Tsugaru Strait"      : (41.62, 140.92),
    "Cape Horn"           : (-55.98, -67.27),
    "Strait of Magellan"  : (-54.00, -70.80),
}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def detect_passages(coords, threshold_km=150):
    passages = []
    for name, (cp_lat, cp_lon) in CHOKEPOINTS.items():
        for lon, lat in coords:
            if haversine_km(lat, lon, cp_lat, cp_lon) < threshold_km:
                if name not in passages:
                    passages.append(name)
                break
    return passages

def get_routes(src_coords, dst_coords, vessel_restrictions=None, speed_knots=24):
    """
    vessel_restrictions: extra searoute restriction keys (e.g. ["panama", "suez"])
    for passages the selected vessel class cannot transit. They are merged into
    every corridor's own restriction set, so all alternatives respect them.
    """
    vessel_restrictions = list(vessel_restrictions or [])
    corridors = [
        ("Optimal Route",           ["northwest"]),
        ("Cape of Good Hope Route", ["northwest", "suez", "panama"]),
        ("Panama Route",            ["northwest", "suez", "babalmandab"]),
        ("Lombok Route",            ["northwest", "malacca"]),
        ("Cape Horn Route",         ["northwest", "suez", "panama", "babalmandab"]),
    ]
    routes = []
    seen   = set()
    for name, restrictions in corridors:
        merged = list(dict.fromkeys(restrictions + vessel_restrictions))
        try:
            r = sr.searoute(src_coords, dst_coords,
                            units="naut", return_passages=True,
                            restrictions=merged)
            dist = round(r["properties"]["length"])
            if dist in seen:
                continue
            seen.add(dist)
            geo = r["geometry"]["coordinates"]
            routes.append({
                "name"    : name,
                "distance": dist,
                "duration": round(dist / speed_knots),
                "geometry": geo,
                "passages": detect_passages(geo),
            })
        except Exception as e:
            print(f"  {name} skipped: {e}")
    return routes
