# conflict.py
# Auto-updated by GitHub Actions on 2026-09-09 10:36 UTC
# Sources: MARAD MSCI · Maritime Executive · gCaptain RSS · UKMTO
# Schedule: Daily at 06:00 UTC
# DO NOT EDIT MANUALLY

CHOKEPOINT_RISK = {
    "Bab el-Mandeb": (9.0, "\"Houthi Forces Attack Saudi Aramco's Jazan Refinery\" — scan 09 Sep 2026 10:36 UTC: 3 critical + 2 elevated keyword matches."),
    "Suez Canal": (4.3, "\"Suez Canal Revival Gathers Pace as Hormuz Crisis Reroutes Ships\" — scan 09 Sep 2026 10:36 UTC: 1 critical + 1 elevated keyword matches."),
    "Strait of Hormuz": (9.5, "\"U.S. Hits Five More Iranian Tankers After Second Attack on U.S. Warship\" — scan 09 Sep 2026 10:36 UTC: 2 critical + 3 elevated keyword matches."),
    "Strait of Malacca": (3.0, "No specific advisory mentions for Strait of Malacca in current sources."),
    "Luzon Strait": (4.0, "No specific advisory mentions for Luzon Strait in current sources."),
    "Strait of Gibraltar": (1.5, "Stable, NATO presence. No current advisories."),
    "Dover Strait": (1.0, "Stable, heavy naval patrol. No current advisories."),
    "Bosphorus Strait": (7.0, "\"Russia’s Arctic LNG 2 Files $1B Arbitration Claim for Canceled DSME Tankers\" — scan 09 Sep 2026 10:36 UTC: 2 critical + 1 elevated keyword matches."),
    "Panama Canal": (2.8, "\"New Panama Canal Chief Takes Office With Water, Expansion Projects in Focus\" — scan 09 Sep 2026 10:36 UTC: 1 critical + 1 elevated keyword matches."),
    "Cape of Good Hope": (1.0, "No conflict risk. Now primary Asia-Europe default route."),
    "Lombok Strait": (2.0, "Minor piracy risk; generally safe Malacca alternative."),
    "Tsugaru Strait": (1.5, "North Korea missile activity in region; Japan-controlled."),
    "Cape Horn": (1.0, "No conflict risk; extreme weather risk only."),
    "Strait of Magellan": (1.0, "Stable, Chile-controlled."),
    "Danish Straits": (3.8, "Tanker Anchor Dragging Case Reopened by Helsinki Appeals Court: \"Nearly a year after the Helsinki District Court in Finland dismissed the case against three of the officers aboard the shadow fleet tanker Eagle S…\" — scan 09 Sep 2026 10:36 UTC: 1 critical + 2 elevated keyword matches."),
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
