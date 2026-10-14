"""
cii.py - indicative voyage-level IMO Carbon Intensity Indicator (CII) rating.

Method: MARPOL Annex VI Reg. 28 / MEPC.353(78) (reference lines, G2),
MEPC.338(76) (reduction factors, G3), MEPC.354(78) (rating boundaries, G4).

    attained = fuel_t * CF * 1e6 / (DWT * distance_nm)      [g CO2 / dwt.nm]
    ref      = a * Capacity^-c
    required = (1 - Z/100) * ref
    ratio    = attained / required  ->  A..E via ship-type d-vector

IMPORTANT: the official CII is assessed annually per ship. A single voyage can
only give an INDICATIVE value. At constant speed, route length cancels out of
the formula, so routes differ here only through the weather sea-margin below.
"""
from datetime import datetime, timezone

CO2_FACTOR_HFO = 3.114        # t CO2 per t fuel (HFO), same factor as metrics.py

# ship_type -> (a, c, capacity cap for the reference line or None)
CII_REFERENCE = {
    "container": (1984, 0.489, None),
    "bulk":      (4745, 0.622, 279000),
    "tanker":    (5247, 0.610, None),
}

# d1..d4 rating-boundary multipliers of the required CII
D_VECTORS = {
    "container": (0.83, 0.94, 1.07, 1.19),
    "bulk":      (0.86, 0.94, 1.06, 1.18),
    "tanker":    (0.82, 0.93, 1.08, 1.28),
}

# Reduction factor Z (% vs 2019). Not yet set by IMO beyond 2026, so later
# years reuse the 2026 value.
REDUCTION_PCT = {2023: 5, 2024: 7, 2025: 9, 2026: 11}

RATINGS = [
    ("A", "Major superior", "#3ddc84"),
    ("B", "Minor superior", "#8ab88a"),
    ("C", "Moderate",       "#d4a017"),
    ("D", "Minor inferior", "#cc6600"),
    ("E", "Inferior",       "#cc3333"),
]

# Heuristic weather sea-margin: extra fuel = K * Hs^2 * hull sensitivity, capped.
# (Added resistance in waves grows roughly with the square of wave height.)
WAVE_MARGIN_K  = 0.012
MAX_SEA_MARGIN = 0.25


def sea_margin(avg_wave_height_m, wave_sensitivity=1.0):
    """Fractional extra fuel burn caused by sea state (0.0 - MAX_SEA_MARGIN)."""
    m = WAVE_MARGIN_K * (float(avg_wave_height_m or 0) ** 2) * wave_sensitivity
    return max(0.0, min(MAX_SEA_MARGIN, m))


def reduction_for_year(year):
    applied = min(max(year, 2023), 2026)
    return REDUCTION_PCT[applied], applied


def reference_cii(ship_type, dwt):
    a, c, cap_limit = CII_REFERENCE[ship_type]
    capacity = min(dwt, cap_limit) if cap_limit else dwt
    return a * capacity ** (-c)


def rate(ratio, ship_type):
    d = D_VECTORS[ship_type]
    idx = 4
    for i, bound in enumerate(d):
        if ratio <= bound:
            idx = i
            break
    return RATINGS[idx]


def compute_cii(vessel, fuel_tonnes, distance_nm, sea_margin_frac=0.0, year=None):
    ship_type = vessel["ship_type"]
    year = year or datetime.now(timezone.utc).year
    z, z_year = reduction_for_year(year)

    fuel_eff = fuel_tonnes * (1.0 + sea_margin_frac)
    attained = fuel_eff * CO2_FACTOR_HFO * 1e6 / (vessel["dwt"] * max(distance_nm, 1))
    ref      = reference_cii(ship_type, vessel["dwt"])
    required = (1 - z / 100.0) * ref
    ratio    = attained / required
    letter, label, color = rate(ratio, ship_type)

    return {
        "attained":   round(attained, 2),
        "required":   round(required, 2),
        "reference":  round(ref, 2),
        "ratio":      round(ratio, 3),
        "rating":     letter,
        "rating_label": label,
        "color":      color,
        "unit":       "gCO2/(dwt.nm)",
        "year":       year,
        "reduction_pct": z,
        "reduction_year_applied": z_year,
        "sea_margin_pct": round(sea_margin_frac * 100, 1),
        "boundaries": {k: round(m * required, 2)
                       for k, m in zip("ABCD", D_VECTORS[ship_type])},
        "indicative": True,
    }
