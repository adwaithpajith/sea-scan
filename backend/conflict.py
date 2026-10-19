# conflict.py
# Auto-updated by GitHub Actions on 2026-10-19 11:49 UTC
# Sources: MARAD MSCI · Maritime Executive · gCaptain RSS · UKMTO
# Schedule: Daily at 06:00 UTC
# DO NOT EDIT MANUALLY

CHOKEPOINT_RISK = {
    "Bab el-Mandeb": (9.0, "\"Qatar LNG Cargo Makes Rare Red Sea Journey to Get Gas to Europe\" — scan 19 Oct 2026 11:49 UTC: 2 critical + 0 elevated keyword matches."),
    "Suez Canal": (4.3, "\"Ukraine Talks with Turkey, India, Egypt Over Grain Corridor\" — scan 19 Oct 2026 11:49 UTC: 1 critical + 0 elevated keyword matches."),
    "Strait of Hormuz": (9.5, "\"The Blockade on Iran Is Now Hitting Home\" — scan 19 Oct 2026 11:49 UTC: 3 critical + 0 elevated keyword matches."),
    "Strait of Malacca": (3.0, "No specific advisory mentions for Strait of Malacca in current sources."),
    "Luzon Strait": (4.0, "No specific advisory mentions for Luzon Strait in current sources."),
    "Strait of Gibraltar": (1.5, "Stable, NATO presence. No current advisories."),
    "Dover Strait": (1.0, "Stable, heavy naval patrol. No current advisories."),
    "Bosphorus Strait": (6.3, "\"Is Russia Probing NATO Weakness in the Black Sea?\" — scan 19 Oct 2026 11:49 UTC: 1 critical + 0 elevated keyword matches."),
    "Panama Canal": (2.0, "No specific advisory mentions for Panama Canal in current sources."),
    "Cape of Good Hope": (1.0, "No conflict risk. Now primary Asia-Europe default route."),
    "Lombok Strait": (2.0, "Minor piracy risk; generally safe Malacca alternative."),
    "Tsugaru Strait": (1.5, "North Korea missile activity in region; Japan-controlled."),
    "Cape Horn": (1.0, "No conflict risk; extreme weather risk only."),
    "Strait of Magellan": (1.0, "Stable, Chile-controlled."),
    "Danish Straits": (4.5, "\"Baltic Block Of Russian Grain May Open Black Sea, Latvia Says\" — scan 19 Oct 2026 11:49 UTC: 3 critical + 0 elevated keyword matches."),
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
