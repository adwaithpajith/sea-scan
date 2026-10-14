"""
vessels.py - vessel-class catalogue and canal-eligibility rules.

Each class is a REPRESENTATIVE design point (rounded public figures), not a
specific ship. Drafts are typical laden transit drafts. Canal limits below
change with water levels / authority circulars - review them periodically.
"""

# --- Canal / strait limits (metres) ----------------------------------------
PANAMA_MAX_LOA_M    = 366.0
PANAMA_MAX_BEAM_M   = 51.25
# Neopanamax locks max authorised draft (TFW). ACP Advisory A-36-2026
# (28 Sep 2026): 14.94 m. This moves with Gatun Lake - update when ACP changes it.
PANAMA_MAX_DRAFT_M  = 14.94
SUEZ_MAX_DRAFT_M    = 20.1    # laden; check Suez Canal Authority circulars
MALACCA_MAX_DRAFT_M = 20.5    # "Malaccamax"

DEFAULT_VESSEL_ID = "default"

# ship_type is one of: container | bulk | tanker (the three types with
# confirmed IMO CII reference-line parameters, see cii.py)
VESSEL_CLASSES = [
    dict(id="default", group="Container ships", label="Generic container ship (legacy model, ~10,000 TEU)",
         ship_type="container", dwt=120000, payload=10000, payload_unit="TEU",
         loa_m=335, beam_m=45.6, draft_m=14.0, speed_kn=24, fuel_tpd=180, wave_sensitivity=1.0),
    dict(id="container_feeder", group="Container ships", label="Feeder (~1,700 TEU)",
         ship_type="container", dwt=22000, payload=1700, payload_unit="TEU",
         loa_m=170, beam_m=27.5, draft_m=9.5, speed_kn=17, fuel_tpd=38, wave_sensitivity=1.25),
    dict(id="container_panamax", group="Container ships", label="Panamax (~4,500 TEU)",
         ship_type="container", dwt=55000, payload=4500, payload_unit="TEU",
         loa_m=294, beam_m=32.3, draft_m=12.0, speed_kn=21, fuel_tpd=95, wave_sensitivity=1.1),
    dict(id="container_neopanamax", group="Container ships", label="Neopanamax (~13,000 TEU)",
         ship_type="container", dwt=140000, payload=13000, payload_unit="TEU",
         loa_m=366, beam_m=48.8, draft_m=14.5, speed_kn=22, fuel_tpd=165, wave_sensitivity=0.95),
    dict(id="container_ulcv", group="Container ships", label="Ultra-large (~24,000 TEU)",
         ship_type="container", dwt=230000, payload=24000, payload_unit="TEU",
         loa_m=400, beam_m=61.5, draft_m=16.5, speed_kn=21, fuel_tpd=215, wave_sensitivity=0.9),
    dict(id="bulk_handysize", group="Bulk carriers", label="Handysize bulk (~35,000 dwt)",
         ship_type="bulk", dwt=35000, payload=32000, payload_unit="t",
         loa_m=180, beam_m=28.0, draft_m=10.0, speed_kn=13.5, fuel_tpd=24, wave_sensitivity=1.2),
    dict(id="bulk_panamax", group="Bulk carriers", label="Panamax bulk (~80,000 dwt)",
         ship_type="bulk", dwt=80000, payload=75000, payload_unit="t",
         loa_m=229, beam_m=32.3, draft_m=14.0, speed_kn=13.5, fuel_tpd=30, wave_sensitivity=1.05),
    dict(id="bulk_capesize", group="Bulk carriers", label="Capesize bulk (~180,000 dwt)",
         ship_type="bulk", dwt=180000, payload=170000, payload_unit="t",
         loa_m=292, beam_m=45.0, draft_m=18.2, speed_kn=14, fuel_tpd=52, wave_sensitivity=1.0),
    dict(id="tanker_aframax", group="Tankers", label="Aframax tanker (~115,000 dwt)",
         ship_type="tanker", dwt=115000, payload=105000, payload_unit="t",
         loa_m=245, beam_m=44.0, draft_m=14.8, speed_kn=14, fuel_tpd=42, wave_sensitivity=1.0),
    dict(id="tanker_suezmax", group="Tankers", label="Suezmax tanker (~160,000 dwt)",
         ship_type="tanker", dwt=160000, payload=150000, payload_unit="t",
         loa_m=274, beam_m=48.0, draft_m=17.0, speed_kn=14.5, fuel_tpd=54, wave_sensitivity=1.0),
    dict(id="tanker_vlcc", group="Tankers", label="VLCC (~300,000 dwt)",
         ship_type="tanker", dwt=300000, payload=280000, payload_unit="t",
         loa_m=333, beam_m=60.0, draft_m=21.0, speed_kn=15.5, fuel_tpd=75, wave_sensitivity=0.9),
]

VESSEL_BY_ID = {v["id"]: v for v in VESSEL_CLASSES}


def get_vessel(vessel_id=None):
    """Return the vessel dict for an id (default class if None). KeyError if unknown."""
    return VESSEL_BY_ID[vessel_id or DEFAULT_VESSEL_ID]


def access_report(v):
    """Per-passage eligibility with a human-readable reason when blocked."""
    p = []
    if v["loa_m"]  > PANAMA_MAX_LOA_M:   p.append(f"length {v['loa_m']:g} m > {PANAMA_MAX_LOA_M:g} m")
    if v["beam_m"] > PANAMA_MAX_BEAM_M:  p.append(f"beam {v['beam_m']:g} m > {PANAMA_MAX_BEAM_M:g} m")
    if v["draft_m"] > PANAMA_MAX_DRAFT_M: p.append(f"draft {v['draft_m']:g} m > {PANAMA_MAX_DRAFT_M:g} m")
    s = []
    if v["draft_m"] > SUEZ_MAX_DRAFT_M:  s.append(f"draft {v['draft_m']:g} m > {SUEZ_MAX_DRAFT_M:g} m")
    m = []
    if v["draft_m"] > MALACCA_MAX_DRAFT_M: m.append(f"draft {v['draft_m']:g} m > {MALACCA_MAX_DRAFT_M:g} m")
    return {
        "panama":  {"name": "Panama Canal",      "ok": not p, "reason": "; ".join(p)},
        "suez":    {"name": "Suez Canal",        "ok": not s, "reason": "; ".join(s)},
        "malacca": {"name": "Strait of Malacca", "ok": not m, "reason": "; ".join(m)},
    }


def routing_restrictions(v):
    """searoute restriction keys for every passage this vessel cannot use."""
    return [key for key, info in access_report(v).items() if not info["ok"]]


def describe_vessel(v):
    """Public (JSON-safe) description of a vessel class."""
    return {
        "id": v["id"], "label": v["label"], "group": v["group"],
        "ship_type": v["ship_type"], "dwt": v["dwt"],
        "payload": v["payload"], "payload_unit": v["payload_unit"],
        "loa_m": v["loa_m"], "beam_m": v["beam_m"], "draft_m": v["draft_m"],
        "speed_kn": v["speed_kn"], "fuel_tpd": v["fuel_tpd"],
        "access": access_report(v),
        "restrictions": routing_restrictions(v),
    }
