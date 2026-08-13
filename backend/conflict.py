# conflict.py
# Auto-updated by GitHub Actions on 2026-08-13 07:17 UTC
# Sources: MARAD MSCI · UKMTO · gCaptain RSS
# Schedule: Daily at 06:00 UTC
# DO NOT EDIT MANUALLY

CHOKEPOINT_RISK = {
    "Bab el-Mandeb": (8.5, "No specific advisory mentions for Bab el-Mandeb in current sources."),
    "Suez Canal": (6.0, "No specific advisory mentions for Suez Canal in current sources."),
    "Strait of Hormuz": (6.5, "No specific advisory mentions for Strait of Hormuz in current sources."),
    "Strait of Malacca": (2.5, "No specific advisory mentions for Strait of Malacca in current sources."),
    "Luzon Strait": (3.5, "No specific advisory mentions for Luzon Strait in current sources."),
    "Strait of Gibraltar": (1.0, "Stable, NATO presence. No current advisories."),
    "Dover Strait": (1.0, "Stable, heavy naval patrol. No current advisories."),
    "Bosphorus Strait": (2.5, "No specific advisory mentions for Bosphorus Strait in current sources."),
    "Panama Canal": (1.5, "No specific advisory mentions for Panama Canal in current sources."),
    "Cape of Good Hope": (1.0, "No conflict risk. Now primary Asia-Europe default route."),
    "Lombok Strait": (2.0, "Minor piracy risk; generally safe Malacca alternative."),
    "Tsugaru Strait": (1.5, "North Korea missile activity in region; Japan-controlled."),
    "Cape Horn": (1.0, "No conflict risk; extreme weather risk only."),
    "Strait of Magellan": (1.0, "Stable, Chile-controlled."),
    "Danish Straits": (2.0, "No specific advisory mentions for Danish Straits in current sources."),
}


def get_conflict_risk(passages):
    breakdown = {}
    for p in passages:
        if p in CHOKEPOINT_RISK:
            score, reason = CHOKEPOINT_RISK[p]
            breakdown[p] = {"score": score, "reason": reason}
    if not breakdown:
        return {
            "conflict_risk_score" : 0.0,
            "risk_label"          : "Minimal",
            "highest_risk_point"  : "None",
            "key_concern"         : "No major chokepoints on this route",
            "breakdown"           : {},
        }
    worst = max(breakdown, key=lambda p: breakdown[p]['score'])
    score = breakdown[worst]['score']
    return {
        "conflict_risk_score" : score,
        "risk_label"          : ("Minimal" if score<2 else "Low" if score<4
                                 else "Moderate" if score<6 else "Elevated"
                                 if score<8 else "High"),
        "highest_risk_point"  : worst,
        "key_concern"         : breakdown[worst]["reason"],
        "breakdown"           : {k: v["score"] for k,v in breakdown.items()},
    }
