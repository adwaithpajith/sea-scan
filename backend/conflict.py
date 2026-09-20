# conflict.py
# Auto-updated by GitHub Actions on 2026-09-20 10:26 UTC
# Sources: MARAD MSCI · Maritime Executive · gCaptain RSS · UKMTO
# Schedule: Daily at 06:00 UTC
# DO NOT EDIT MANUALLY

CHOKEPOINT_RISK = {
    "Bab el-Mandeb": (9.0, "\"Africa’s Red Sea States Face Growing Risks as Houthis Expand Their Reach\" — scan 20 Sep 2026 10:26 UTC: 3 critical + 2 elevated keyword matches."),
    "Suez Canal": (3.5, "No specific advisory mentions for Suez Canal in current sources."),
    "Strait of Hormuz": (8.8, "\"Iran Exploits Attack on Small Product Tanker to Assert Hormuz Control\" — scan 20 Sep 2026 10:26 UTC: 1 critical + 2 elevated keyword matches."),
    "Strait of Malacca": (3.8, "\"Indonesia Takes Delivery of a \"Free\" Aircraft Carrier\" — scan 20 Sep 2026 10:26 UTC: 1 critical + 0 elevated keyword matches."),
    "Luzon Strait": (4.2, "\"Chinese Coast Guard Vessel Hits Philippine Supply Boat in Spratly Islands\" — scan 20 Sep 2026 10:26 UTC: 0 critical + 1 elevated keyword matches."),
    "Strait of Gibraltar": (1.5, "Stable, NATO presence. No current advisories."),
    "Dover Strait": (1.0, "Stable, heavy naval patrol. No current advisories."),
    "Bosphorus Strait": (7.0, "\"London’s Marine Insurers Widen Black Sea High Risk Zone as Shipping Attacks Surge\" — scan 20 Sep 2026 10:26 UTC: 2 critical + 0 elevated keyword matches."),
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
