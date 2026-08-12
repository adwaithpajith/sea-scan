
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import os

from engine import get_routes, CHOKEPOINTS
from weather import get_weather_risk
from conflict import get_conflict_risk, CHOKEPOINT_RISK
from clustering import build_cluster_model, CLUSTER_INFO
from metrics import score_all_routes

app = FastAPI(title="SeaRoute Intelligence API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "data", "UpdatedPub150.csv")

print("Loading port data...")
df_raw = pd.read_csv(CSV_PATH, encoding="latin-1")
df_raw = df_raw[["Main Port Name","Country Code","Latitude","Longitude",
                  "Harbor Size","World Water Body"]
                ].dropna(subset=["Latitude","Longitude"]).reset_index(drop=True)

print("Building K-Means port risk clusters...")
df_ports = build_cluster_model(df_raw)
print(f"Ready — {len(df_ports)} ports loaded.")

class RouteRequest(BaseModel):
    source     : str
    destination: str

@app.get("/api/health")
def health():
    return {"status": "ok", "ports": len(df_ports)}

@app.get("/api/ports")
def get_ports():
    return df_ports[[
        "Main Port Name","Country Code",
        "Latitude","Longitude",
        "cluster_id","cluster_label","cluster_color"
    ]].to_dict(orient="records")

@app.get("/api/port-search")
def port_search(q: str = ""):
    if len(q) < 2:
        return []
    mask = df_ports["Main Port Name"].str.contains(q, case=False, na=False)
    return df_ports[mask][["Main Port Name","Country Code",
                            "Latitude","Longitude"]].head(12).to_dict(orient="records")

@app.get("/api/chokepoints")
def get_chokepoints():
    result = []
    for name,(lat,lon) in CHOKEPOINTS.items():
        score, reason = CHOKEPOINT_RISK.get(name,(0,"No data"))
        result.append({
            "name":name,"lat":lat,"lon":lon,
            "score":score,"reason":reason,
            "label":("High"     if score>=8 else "Elevated" if score>=6
                     else "Moderate" if score>=4 else "Low" if score>=2 else "Minimal"),
            "color":("#e74c3c" if score>=8 else "#e67e22" if score>=6
                     else "#f39c12" if score>=4 else "#2ecc71"),
        })
    return result

@app.post("/api/routes")
def compute_routes(req: RouteRequest):
    src_m = df_ports[df_ports["Main Port Name"]==req.source]
    dst_m = df_ports[df_ports["Main Port Name"]==req.destination]
    if src_m.empty: raise HTTPException(400, f"Port not found: {req.source}")
    if dst_m.empty: raise HTTPException(400, f"Port not found: {req.destination}")
    if req.source==req.destination: raise HTTPException(400,"Ports must differ")

    src = src_m.iloc[0]
    dst = dst_m.iloc[0]
    src_coords = [float(src["Longitude"]), float(src["Latitude"])]
    dst_coords = [float(dst["Longitude"]), float(dst["Latitude"])]

    routes   = get_routes(src_coords, dst_coords)
    weather  = [get_weather_risk(r["geometry"])  for r in routes]
    conflict = [get_conflict_risk(r["passages"]) for r in routes]
    scored   = score_all_routes(routes, weather, conflict)

    best = min(range(len(scored)), key=lambda i: scored[i]["risk_score"])
    for i,r in enumerate(scored):
        r["recommended"] = (i==best)

    return {"source":req.source,"destination":req.destination,"routes":scored}

# Serve frontend
FRONTEND = os.path.join(BASE_DIR, "..", "frontend")
if os.path.exists(FRONTEND):
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

@app.get("/")
def root():
    idx = os.path.join(FRONTEND,"index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"message":"SeaRoute Intelligence API v2.0"}
