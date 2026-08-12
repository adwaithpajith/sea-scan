
CHOKEPOINT_RISK = {
    "Bab el-Mandeb"       : (9.5, "CRITICAL — Houthi attacks resumed Feb 2026. Most carriers routing via Cape of Good Hope. MARAD advisory active."),
    "Suez Canal"          : (7.0, "HIGH — Red Sea crisis ongoing. ~26 ships/week vs 80 pre-crisis. War risk insurance premiums prohibitive."),
    "Strait of Hormuz"    : (7.5, "HIGH — UKMTO advisory active. US-Israeli strikes on Iran elevated shipping threat. Electronic interference reported."),
    "Strait of Malacca"   : (3.0, "LOW — Petty piracy; well-patrolled by regional navies. No major incidents in 2026."),
    "Luzon Strait"        : (4.5, "MODERATE — South China Sea tensions. China-Philippines standoffs ongoing in 2025-2026."),
    "Strait of Gibraltar" : (1.0, "MINIMAL — Stable, NATO presence."),
    "Dover Strait"        : (1.0, "MINIMAL — Stable, heavy naval patrol."),
    "Bosphorus Strait"    : (3.0, "LOW — Black Sea war ongoing; Turkey controls access with restrictions."),
    "Panama Canal"        : (1.5, "MINIMAL — Stable; drought capacity constraints easing in 2026."),
    "Cape of Good Hope"   : (1.0, "MINIMAL — No conflict risk. Now primary Asia-Europe default route."),
    "Lombok Strait"       : (2.0, "LOW — Minor piracy risk; generally safe Malacca alternative."),
    "Tsugaru Strait"      : (2.0, "LOW — North Korea missile activity in region; Japan-controlled waters."),
    "Cape Horn"           : (1.0, "MINIMAL — No conflict risk; extreme weather risk only."),
    "Strait of Magellan"  : (1.0, "MINIMAL — Stable, Chile-controlled."),
    "Danish Straits"      : (2.5, "LOW — Baltic NATO tensions; Russian shadow fleet incidents reported."),
}

def get_conflict_risk(passages):
    breakdown = {}
    for p in passages:
        if p in CHOKEPOINT_RISK:
            score, reason = CHOKEPOINT_RISK[p]
            breakdown[p] = {"score": score, "reason": reason}
    if not breakdown:
        return {"conflict_risk_score":0.0,"risk_label":"Minimal",
                "highest_risk_point":"None",
                "key_concern":"No major chokepoints on this route",
                "breakdown":{}}
    worst = max(breakdown, key=lambda p: breakdown[p]["score"])
    score = breakdown[worst]["score"]
    return {
        "conflict_risk_score": score,
        "risk_label": ("Minimal" if score<2 else "Low" if score<4
                       else "Moderate" if score<6 else "Elevated" if score<8 else "High"),
        "highest_risk_point": worst,
        "key_concern": breakdown[worst]["reason"],
        "breakdown": {k: v["score"] for k,v in breakdown.items()},
    }
