
import requests
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta, timezone

def haversine_nm(lat1, lon1, lat2, lon2):
    R = 3440.065
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2-lat1, lon2-lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def sample_waypoints(coords, n=8):
    total = len(coords)
    if total <= n:
        return coords
    step = total / n
    return [coords[int(i * step)] for i in range(n)]

def compute_etas(coords, speed_knots=24):
    waypoints = sample_waypoints(coords, n=8)
    result = []
    cumulative_nm = 0.0
    for i, (lon, lat) in enumerate(waypoints):
        if i > 0:
            prev_lon, prev_lat = waypoints[i-1]
            cumulative_nm += haversine_nm(prev_lat, prev_lon, lat, lon)
        result.append((lon, lat, cumulative_nm / speed_knots))
    return result

def fetch_weather_at(lat, lon, eta_hours):
    now         = datetime.now(timezone.utc)
    capped      = eta_hours > 168
    forecast_dt = now + timedelta(hours=min(eta_hours, 168))
    date_str    = forecast_dt.strftime("%Y-%m-%d")
    hour        = forecast_dt.hour
    try:
        mr = requests.get("https://marine-api.open-meteo.com/v1/marine", params={
            "latitude": lat, "longitude": lon,
            "hourly": ["wave_height","wind_wave_height",
                       "swell_wave_height","swell_wave_period"],
            "start_date": date_str, "end_date": date_str,
            "length_unit": "metric", "timezone": "UTC",
        }, timeout=10)
        md       = mr.json().get("hourly", {})
        wave_h   = md.get("wave_height",       [0]*24)[hour] or 0
        wind_w   = md.get("wind_wave_height",  [0]*24)[hour] or 0
        swell_h  = md.get("swell_wave_height", [0]*24)[hour] or 0
        swell_p  = md.get("swell_wave_period", [8]*24)[hour] or 8

        ar = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "hourly": ["wind_speed_10m","visibility"],
            "start_date": date_str, "end_date": date_str,
            "timezone": "UTC", "wind_speed_unit": "kn",
        }, timeout=10)
        ad       = ar.json().get("hourly", {})
        wind_spd = ad.get("wind_speed_10m", [0]*24)[hour] or 0
        vis_m    = ad.get("visibility",  [10000]*24)[hour] or 10000

        return {
            "lat": round(lat,2), "lon": round(lon,2),
            "eta_hours": round(eta_hours,1),
            "eta_days": round(eta_hours/24,1),
            "wave_height": round(wave_h,2),
            "wind_wave": round(wind_w,2),
            "swell_height": round(swell_h,2),
            "swell_period": round(swell_p,1),
            "wind_speed_kn": round(wind_spd,1),
            "visibility_m": round(vis_m),
            "capped": capped,
        }
    except:
        return {
            "lat":round(lat,2),"lon":round(lon,2),
            "eta_hours":round(eta_hours,1),"eta_days":round(eta_hours/24,1),
            "wave_height":0,"wind_wave":0,"swell_height":0,"swell_period":8,
            "wind_speed_kn":0,"visibility_m":10000,"capped":capped,
        }

def wave_label(wh):
    if wh < 0.5: return "Calm"
    if wh < 1.5: return "Slight"
    if wh < 2.5: return "Moderate"
    if wh < 4.0: return "Rough"
    return "Very Rough"

def score_reading(w):
    wh,ww,sh = w["wave_height"],w["wind_wave"],w["swell_height"]
    sp,ws,vis = w["swell_period"],w["wind_speed_kn"],w["visibility_m"]
    if   wh<0.5: s_wave=wh*4
    elif wh<1.5: s_wave=2+(wh-0.5)*2
    elif wh<3.0: s_wave=4+(wh-1.5)*(2/1.5)
    elif wh<5.0: s_wave=6+(wh-3.0)*1
    else:        s_wave=min(10,8+(wh-5.0)*0.5)
    pp=1.3 if sp<8 else 1.0
    if   sh<1.0: s_sw=sh*3
    elif sh<2.5: s_sw=3+(sh-1.0)*(2/1.5)
    elif sh<4.0: s_sw=5+(sh-2.5)*(2/1.5)
    else:        s_sw=min(10,7+(sh-4.0)*0.5)
    s_sw=min(10,s_sw*pp)
    if   ww<1.0: s_ww=ww*4
    elif ww<2.0: s_ww=4+(ww-1.0)*2
    else:        s_ww=min(10,6+(ww-2.0)*1.5)
    if   ws<10:  s_ws=ws*0.3
    elif ws<20:  s_ws=3+(ws-10)*0.3
    elif ws<35:  s_ws=6+(ws-20)*0.2
    else:        s_ws=min(10,9+(ws-35)*0.1)
    s_vis=0 if vis>5000 else 3 if vis>2000 else 6 if vis>500 else 9
    return round(s_wave*0.35+s_sw*0.25+s_ww*0.15+s_ws*0.15+s_vis*0.10,1)

def score_weather(readings):
    if not readings:
        return {
            "weather_risk_score":0,"risk_label":"Unknown",
            "avg_wave_height_m":0,"samples":0,
            "any_capped":False,"waypoints":[]
        }
    scores, waves = [], []
    waypoints = []
    for w in readings:
        sc = score_reading(w)
        scores.append(sc)
        waves.append(w["wave_height"])
        waypoints.append({
            "lat"          : w["lat"],
            "lon"          : w["lon"],
            "eta_hours"    : w["eta_hours"],
            "eta_days"     : w["eta_days"],
            "wave_height"  : w["wave_height"],
            "wind_speed_kn": w["wind_speed_kn"],
            "swell_height" : w["swell_height"],
            "weather_score": sc,
            "condition"    : wave_label(w["wave_height"]),
            "capped"       : w["capped"],
        })
    avg = round(float(np.mean(scores)),1)
    return {
        "weather_risk_score": avg,
        "risk_label": ("Calm" if avg<2 else "Slight" if avg<4
                       else "Moderate" if avg<6 else "Rough" if avg<8 else "Very Rough"),
        "avg_wave_height_m": round(float(np.mean(waves)),2),
        "samples": len(readings),
        "any_capped": any(w["capped"] for w in readings),
        "waypoints": waypoints,
    }

def get_weather_risk(geometry_coords, speed_knots=24):
    wpts     = compute_etas(geometry_coords, speed_knots)
    readings = [fetch_weather_at(lat, lon, eta) for lon, lat, eta in wpts]
    return score_weather(readings)
