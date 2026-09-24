# conflict.py
# Auto-updated by GitHub Actions on 2026-09-24 10:56 UTC
# Sources: MARAD MSCI · Maritime Executive · gCaptain RSS · UKMTO
# Schedule: Daily at 06:00 UTC
# DO NOT EDIT MANUALLY

CHOKEPOINT_RISK = {
    "Bab el-Mandeb": (8.3, "Overcapacity Looms Over Container Shipping as Supply Pressure Mounts: \"The return of container vessels to the Suez Canal - Red Sea route is likely to have a profound impact on the sector, especially as it continues to…\" — scan 24 Sep 2026 10:56 UTC: 1 critical + 0 elevated keyword matches."),
    "Suez Canal": (4.3, "Overcapacity Looms Over Container Shipping as Supply Pressure Mounts: \"The return of container vessels to the Suez Canal - Red Sea route is likely to have a profound impact on the sector, especially as…\" — scan 24 Sep 2026 10:56 UTC: 1 critical + 1 elevated keyword matches."),
    "Strait of Hormuz": (9.5, "\"Indian Seafarer Union Demands Action as Another Ship is Attacked in Hormuz\" — scan 24 Sep 2026 10:56 UTC: 2 critical + 0 elevated keyword matches."),
    "Strait of Malacca": (3.8, "\"Death Toll from Capsized Ship in Indonesia Rises to 20 as Search Continues for 115 Missing Passengers\" — scan 24 Sep 2026 10:56 UTC: 1 critical + 0 elevated keyword matches."),
    "Luzon Strait": (4.0, "No specific advisory mentions for Luzon Strait in current sources."),
    "Strait of Gibraltar": (1.5, "Stable, NATO presence. No current advisories."),
    "Dover Strait": (1.0, "Stable, heavy naval patrol. No current advisories."),
    "Bosphorus Strait": (6.3, "\"Captain Killed in Russia’s Latest Attack on Merchant Shipping\" — scan 24 Sep 2026 10:56 UTC: 1 critical + 0 elevated keyword matches."),
    "Panama Canal": (2.0, "No specific advisory mentions for Panama Canal in current sources."),
    "Cape of Good Hope": (1.0, "No conflict risk. Now primary Asia-Europe default route."),
    "Lombok Strait": (2.0, "Minor piracy risk; generally safe Malacca alternative."),
    "Tsugaru Strait": (1.5, "North Korea missile activity in region; Japan-controlled."),
    "Cape Horn": (1.0, "No conflict risk; extreme weather risk only."),
    "Strait of Magellan": (1.0, "Stable, Chile-controlled."),
    "Danish Straits": (3.0, "No specific advisory mentions for Danish Straits in current sources."),
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
