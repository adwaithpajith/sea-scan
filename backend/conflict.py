# conflict.py
# Auto-updated by GitHub Actions on 2026-11-11 13:23 UTC
# Sources: MARAD MSCI · Maritime Executive · gCaptain RSS · UKMTO
# Schedule: Daily at 06:00 UTC
# DO NOT EDIT MANUALLY

CHOKEPOINT_RISK = {
    "Bab el-Mandeb": (7.5, "No specific advisory mentions for Bab el-Mandeb in current sources."),
    "Suez Canal": (3.5, "No specific advisory mentions for Suez Canal in current sources."),
    "Strait of Hormuz": (9.5, "\"Uncertainty Surrounds Possible Attack on Oman's Strait of Hormuz Lighthouse\" — scan 11 Nov 2026 13:23 UTC: 2 critical + 1 elevated keyword matches."),
    "Strait of Malacca": (3.8, "U.S. Honors USS Houston War Grave Wreck With Plaque: \"…650 US Navy sailors and marines who died when their ship was sunk by the Japanese in Indonesian waters during World War II have been immortalize...\" — scan 11 Nov 2026 13:23 UTC: 1 critical + 0 elevated keyword matches."),
    "Luzon Strait": (4.2, "Analysis: China's Naval Drills Suggest Preparation to Isolate Taiwan: \"The massive Chinese naval exercises around the South China Sea, East China Sea and Philippine Sea last week were structured to prepare for an area…\" — scan 11 Nov 2026 13:23 UTC: 0 critical + 2 elevated keyword matches."),
    "Strait of Gibraltar": (1.5, "Stable, NATO presence. No current advisories."),
    "Dover Strait": (1.0, "Stable, heavy naval patrol. No current advisories."),
    "Bosphorus Strait": (7.0, "\"Video: Ukrainian Strike Causes Major Fire at Russian Oil Port of Ust-Luga\" — scan 11 Nov 2026 13:23 UTC: 3 critical + 1 elevated keyword matches."),
    "Panama Canal": (2.0, "No specific advisory mentions for Panama Canal in current sources."),
    "Cape of Good Hope": (1.0, "No conflict risk. Now primary Asia-Europe default route."),
    "Lombok Strait": (2.0, "Minor piracy risk; generally safe Malacca alternative."),
    "Tsugaru Strait": (1.5, "North Korea missile activity in region; Japan-controlled."),
    "Cape Horn": (1.0, "No conflict risk; extreme weather risk only."),
    "Strait of Magellan": (1.0, "Stable, Chile-controlled."),
    "Danish Straits": (4.5, "\"Russia Warns Europe Against Interference With the Shadow Fleet\" — scan 11 Nov 2026 13:23 UTC: 2 critical + 1 elevated keyword matches."),
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
