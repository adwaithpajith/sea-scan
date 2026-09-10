# conflict.py
# Auto-updated by GitHub Actions on 2026-09-10 10:23 UTC
# Sources: MARAD MSCI · Maritime Executive · gCaptain RSS · UKMTO
# Schedule: Daily at 06:00 UTC
# DO NOT EDIT MANUALLY

CHOKEPOINT_RISK = {
    "Bab el-Mandeb": (7.5, "No specific advisory mentions for Bab el-Mandeb in current sources."),
    "Suez Canal": (3.5, "No specific advisory mentions for Suez Canal in current sources."),
    "Strait of Hormuz": (9.5, "\"Iran Battles to Beat the Blockade\" — scan 10 Sep 2026 10:23 UTC: 2 critical + 4 elevated keyword matches."),
    "Strait of Malacca": (3.0, "No specific advisory mentions for Strait of Malacca in current sources."),
    "Luzon Strait": (4.2, "Fire Destroys Philippine Ferry, Killing Five and Leaving Dozens Missing: \"A fire aboard a passenger ferry off the coast of the Philippines has killed at least five people, according to the Philippine Coast Guard, and search...\" — scan 10 Sep 2026 10:23 UTC: 0 critical + 2 elevated keyword matches."),
    "Strait of Gibraltar": (1.5, "Stable, NATO presence. No current advisories."),
    "Dover Strait": (1.0, "Stable, heavy naval patrol. No current advisories."),
    "Bosphorus Strait": (7.0, "\"Norway Repatriates 69 Russians After Arresting Research Vessel in Svalbard\" — scan 10 Sep 2026 10:23 UTC: 2 critical + 1 elevated keyword matches."),
    "Panama Canal": (2.0, "No specific advisory mentions for Panama Canal in current sources."),
    "Cape of Good Hope": (1.0, "No conflict risk. Now primary Asia-Europe default route."),
    "Lombok Strait": (2.0, "Minor piracy risk; generally safe Malacca alternative."),
    "Tsugaru Strait": (1.5, "North Korea missile activity in region; Japan-controlled."),
    "Cape Horn": (1.0, "No conflict risk; extreme weather risk only."),
    "Strait of Magellan": (1.0, "Stable, Chile-controlled."),
    "Danish Straits": (3.8, "\"Captain and Boatswain Go on Trial in Finland for Anchor Dragging Incident\" — scan 10 Sep 2026 10:23 UTC: 1 critical + 2 elevated keyword matches."),
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
