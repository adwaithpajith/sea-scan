
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans

CHOKEPOINT_RISK_SCORES = {
    "Bab el-Mandeb"       : (12.58,  43.32, 9.5),
    "Suez Canal"          : (30.45,  32.35, 7.0),
    "Strait of Hormuz"    : (26.57,  56.25, 7.5),
    "Strait of Malacca"   : ( 1.25, 103.82, 3.0),
    "Luzon Strait"        : (20.00, 121.50, 4.5),
    "Strait of Gibraltar" : (35.96,  -5.48, 1.0),
    "Dover Strait"        : (51.00,   1.50, 1.0),
    "Bosphorus Strait"    : (41.12,  29.08, 3.0),
    "Panama Canal"        : ( 9.08, -79.68, 1.5),
    "Cape of Good Hope"   : (-34.36, 18.47, 1.0),
    "Lombok Strait"       : (-8.75, 115.75, 2.0),
    "Tsugaru Strait"      : (41.62, 140.92, 2.0),
    "Cape Horn"           : (-55.98,-67.27, 1.0),
    "Strait of Magellan"  : (-54.00,-70.80, 1.0),
    "Danish Straits"      : (55.50,  10.50, 2.5),
}

CLUSTER_INFO = {
    0: {"label": "Low Risk",      "color": "#2ecc71"},
    1: {"label": "Moderate Risk", "color": "#f39c12"},
    2: {"label": "Elevated Risk", "color": "#e67e22"},
    3: {"label": "High Risk",     "color": "#e74c3c"},
    4: {"label": "Critical Risk", "color": "#9b59b6"},
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

def nearest_chokepoint_risk(lat, lon):
    best_dist, best_risk = float("inf"), 0.0
    for cp_lat,cp_lon,risk in CHOKEPOINT_RISK_SCORES.values():
        d = haversine_km(lat, lon, cp_lat, cp_lon)
        if d < best_dist:
            best_dist, best_risk = d, risk
    return best_dist, best_risk

def build_cluster_model(df_ports):
    print("Clustering ports (K-Means, k=5)...")
    rows = []
    for _, row in df_ports.iterrows():
        lat     = float(row["Latitude"])
        lon     = float(row["Longitude"])
        harbour = HARBOUR_SIZE_MAP.get(str(row.get("Harbor Size","Small")), 1)
        cp_dist, cp_risk = nearest_chokepoint_risk(lat, lon)
        rows.append([harbour, cp_risk, cp_dist, abs(lat)])
    X        = np.array(rows, dtype=float)
    X_scaled = MinMaxScaler().fit_transform(X)
    kmeans   = KMeans(n_clusters=5, random_state=42, n_init=10)
    labels   = kmeans.fit_predict(X_scaled)
    centres  = kmeans.cluster_centers_.mean(axis=1)
    rank     = np.argsort(centres)
    lmap     = {old:new for new,old in enumerate(rank)}
    mapped   = np.array([lmap[l] for l in labels])
    df_out   = df_ports.copy()
    df_out["cluster_id"]    = mapped
    df_out["cluster_label"] = [CLUSTER_INFO[c]["label"] for c in mapped]
    df_out["cluster_color"] = [CLUSTER_INFO[c]["color"] for c in mapped]
    for cid,info in CLUSTER_INFO.items():
        print(f"  {info['label']}: {(mapped==cid).sum()} ports")
    return df_out
