
import numpy as np
from math import radians, sin, cos, sqrt, atan2, exp
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from .conflict import CHOKEPOINT_RISK

# Fixed geographic coordinates of each major chokepoint. Risk *scores* are
# read live from backend/conflict.py (the same auto-refreshed table route
# scoring uses), so port clusters stay in sync with the daily conflict-risk
# pipeline instead of drifting from a frozen snapshot.
CHOKEPOINT_COORDS = {
    "Bab el-Mandeb"       : (12.58,  43.32),
    "Suez Canal"          : (30.45,  32.35),
    "Strait of Hormuz"    : (26.57,  56.25),
    "Strait of Malacca"   : ( 1.25, 103.82),
    "Luzon Strait"        : (20.00, 121.50),
    "Strait of Gibraltar" : (35.96,  -5.48),
    "Dover Strait"        : (51.00,   1.50),
    "Bosphorus Strait"    : (41.12,  29.08),
    "Panama Canal"        : ( 9.08, -79.68),
    "Cape of Good Hope"   : (-34.36, 18.47),
    "Lombok Strait"       : (-8.75, 115.75),
    "Tsugaru Strait"      : (41.62, 140.92),
    "Cape Horn"           : (-55.98,-67.27),
    "Strait of Magellan"  : (-54.00,-70.80),
    "Danish Straits"      : (55.50,  10.50),
}

# Only used if a chokepoint name is somehow missing from conflict.py —
# should not happen in normal operation since the name sets match exactly.
_FALLBACK_RISK = 1.0

# A chokepoint's danger doesn't stop sharply at some radius — it fades with
# distance. EXPOSURE_DECAY_KM controls how fast: at this many km away, a
# port "feels" ~37% (1/e) of the chokepoint's own risk score. 500km is
# roughly the scale at which real rerouting/insurance decisions treat a
# chokepoint's disruption as still relevant.
EXPOSURE_DECAY_KM = 500.0

CLUSTER_INFO = {
    0: {"label": "Low Risk",      "color": "#2ecc71"},
    1: {"label": "Moderate Risk", "color": "#f39c12"},
    2: {"label": "Elevated Risk", "color": "#e67e22"},
    3: {"label": "High Risk",     "color": "#e74c3c"},
    4: {"label": "Critical Risk", "color": "#9b59b6"},
}

# Absolute floors an individual port's own exposure value must clear before
# it's *allowed* to carry that label, regardless of where it ranks relative
# to other ports today. Without this, K-Means always produces exactly 5
# non-empty buckets, so a "Critical" label would exist even on a day when
# every chokepoint in the world was calm — the label would just mean
# "relatively worse than other ports today," not "actually dangerous."
# A port that fails a tier's floor is downgraded one tier at a time until
# it either clears the floor or lands at Moderate (Low never needs gating —
# it's already the safe end).
ABSOLUTE_EXPOSURE_FLOORS = {
    2: 2.0,   # Elevated
    3: 4.0,   # High
    4: 6.0,   # Critical
}

HARBOUR_SIZE_MAP = {
    "Very Large":4, "Large":3, "Medium":2, "Small":1, "Very Small":0,
}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    lat1,lon1,lat2,lon2 = map(radians,[lat1,lon1,lat2,lon2])
    dlat,dlon = lat2-lat1, lon2-lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R*2*atan2(sqrt(a),sqrt(1-a))

def nearest_chokepoint_exposure(lat, lon):
    """
    Finds the nearest chokepoint and returns a single 'exposure' value that
    combines its live risk score with how close this port actually is to
    it — risk * exp(-distance / EXPOSURE_DECAY_KM) — instead of treating
    risk and distance as two unrelated axes and leaving K-Means to infer
    the relationship. A port near a moderate chokepoint can now correctly
    outscore a port far from a severe one.
    """
    best_dist, best_name = float("inf"), None
    for name, (cp_lat, cp_lon) in CHOKEPOINT_COORDS.items():
        d = haversine_km(lat, lon, cp_lat, cp_lon)
        if d < best_dist:
            best_dist, best_name = d, name
    risk = CHOKEPOINT_RISK.get(best_name, (_FALLBACK_RISK, ""))[0]
    exposure = risk * exp(-best_dist / EXPOSURE_DECAY_KM)
    return best_dist, risk, exposure

def apply_absolute_floor(cluster_id, exposure):
    while cluster_id in ABSOLUTE_EXPOSURE_FLOORS and exposure < ABSOLUTE_EXPOSURE_FLOORS[cluster_id]:
        cluster_id -= 1
    return cluster_id

def build_cluster_model(df_ports):
    print("Clustering ports (K-Means, k=5)...")
    rows = []
    exposures = []
    for _, row in df_ports.iterrows():
        lat     = float(row["Latitude"])
        lon     = float(row["Longitude"])
        harbour = HARBOUR_SIZE_MAP.get(str(row.get("Harbor Size","Small")), 1)
        _, _, exposure = nearest_chokepoint_exposure(lat, lon)
        rows.append([harbour, exposure, abs(lat)])
        exposures.append(exposure)

    X        = np.array(rows, dtype=float)
    X_scaled = MinMaxScaler().fit_transform(X)
    kmeans   = KMeans(n_clusters=5, random_state=42, n_init=10)
    labels   = kmeans.fit_predict(X_scaled)
    centres  = kmeans.cluster_centers_.mean(axis=1)
    rank     = np.argsort(centres)
    lmap     = {old:new for new,old in enumerate(rank)}
    mapped   = np.array([lmap[l] for l in labels])

    print("  Raw K-Means clusters (before absolute floor):")
    for cid,info in CLUSTER_INFO.items():
        print(f"    {info['label']}: {(mapped==cid).sum()} ports")

    # Apply the absolute floor: a port only keeps an Elevated/High/Critical
    # label if its own exposure value actually clears that tier's floor.
    gated = np.array([
        apply_absolute_floor(cid, exposures[i]) for i, cid in enumerate(mapped)
    ])

    print("  After absolute-floor gating:")
    for cid,info in CLUSTER_INFO.items():
        print(f"    {info['label']}: {(gated==cid).sum()} ports")
    downgraded = int((gated != mapped).sum())
    print(f"  {downgraded} ports downgraded by the absolute floor")

    df_out   = df_ports.copy()
    df_out["cluster_id"]        = gated
    df_out["cluster_label"]     = [CLUSTER_INFO[c]["label"] for c in gated]
    df_out["cluster_color"]     = [CLUSTER_INFO[c]["color"] for c in gated]
    df_out["chokepoint_exposure"] = np.round(exposures, 2)
    return df_out
