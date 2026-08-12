#!/usr/bin/env python3
"""
SeaRoute Intelligence Platform — Conflict Risk Auto-Updater
Runs daily via GitHub Actions.
Sources: MARAD MSCI (primary) -> UKMTO (fallback) -> gCaptain RSS (fallback)
"""
import requests
from bs4 import BeautifulSoup
import re, os, json
from datetime import datetime

REGIONS = {
    "Bab el-Mandeb": {
        "terms"  : ["bab el-mandeb","red sea","houthi","yemen","gulf of aden"],
        "high"   : ["attack","missile","drone","struck","fired upon","vessel hit","explosion","sinking"],
        "medium" : ["threat","caution","advisory","warning","heightened","hostile"],
        "low"    : ["monitor","awareness","routine","transit"],
    },
    "Suez Canal": {
        "terms"  : ["suez","suez canal","egypt"],
        "high"   : ["closed","blocked","attack","suspended","halted"],
        "medium" : ["reduced","disruption","divert","delays","warning"],
        "low"    : ["monitor","normal","routine"],
    },
    "Strait of Hormuz": {
        "terms"  : ["hormuz","iran","persian gulf","gulf of oman"],
        "high"   : ["seized","attack","fired","intercepted","strike","boarded","detained"],
        "medium" : ["threat","tension","warning","advisory","heightened","electronic"],
        "low"    : ["monitor","routine"],
    },
    "Strait of Malacca": {
        "terms"  : ["malacca","indonesia","malaysia","singapore strait"],
        "high"   : ["piracy","hijack","boarded","robbery","attack"],
        "medium" : ["suspicious","warning","attempted","approached"],
        "low"    : ["monitor","routine"],
    },
    "Luzon Strait": {
        "terms"  : ["south china sea","luzon","philippines","taiwan strait","spratly"],
        "high"   : ["fired upon","vessel seized","collision","confrontation","ramming"],
        "medium" : ["tension","warning","dispute","standoff","water cannon"],
        "low"    : ["monitor","routine"],
    },
    "Bosphorus Strait": {
        "terms"  : ["black sea","bosphorus","ukraine","russia","kerch"],
        "high"   : ["attack","mined","struck","missile","drone strike","sunk"],
        "medium" : ["closed","restricted","warning","mine warning"],
        "low"    : ["monitor","routine"],
    },
    "Danish Straits": {
        "terms"  : ["baltic","danish straits","finland","sweden","shadow fleet"],
        "high"   : ["attack","sabotage","pipeline","cable cut","explosion"],
        "medium" : ["shadow fleet","warning","suspicious","surveillance"],
        "low"    : ["monitor","routine"],
    },
    "Panama Canal": {
        "terms"  : ["panama canal","panama"],
        "high"   : ["closed","blocked","attack","suspended"],
        "medium" : ["drought","reduced","restrictions","capacity","delays"],
        "low"    : ["monitor","routine","normal"],
    },
}

BASE_SCORES = {
    "Bab el-Mandeb"       : 8.5,
    "Suez Canal"          : 6.0,
    "Strait of Hormuz"    : 6.5,
    "Strait of Malacca"   : 2.5,
    "Luzon Strait"        : 3.5,
    "Strait of Gibraltar" : 1.0,
    "Dover Strait"        : 1.0,
    "Bosphorus Strait"    : 2.5,
    "Panama Canal"        : 1.5,
    "Cape of Good Hope"   : 1.0,
    "Lombok Strait"       : 2.0,
    "Tsugaru Strait"      : 1.5,
    "Cape Horn"           : 1.0,
    "Strait of Magellan"  : 1.0,
    "Danish Straits"      : 2.0,
}

STATIC_REASONS = {
    "Strait of Gibraltar" : "Stable, NATO presence. No current advisories.",
    "Dover Strait"        : "Stable, heavy naval patrol. No current advisories.",
    "Cape of Good Hope"   : "No conflict risk. Now primary Asia-Europe default route.",
    "Lombok Strait"       : "Minor piracy risk; generally safe Malacca alternative.",
    "Tsugaru Strait"      : "North Korea missile activity in region; Japan-controlled.",
    "Cape Horn"           : "No conflict risk; extreme weather risk only.",
    "Strait of Magellan"  : "Stable, Chile-controlled.",
}

HEADERS = {"User-Agent": "SeaRoute-Intelligence-Platform/2.0 (academic research)"}

def fetch_marad():
    print("Trying MARAD...")
    text = ""
    try:
        r = requests.get(
            "https://www.maritime.dot.gov/msci-advisories",
            headers=HEADERS, timeout=15
        )
        if r.status_code != 200:
            print(f"  MARAD returned {r.status_code}")
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "msci" in href.lower() and any(
                kw in href.lower() for kw in ["advisory","alert","notice"]
            ):
                if not href.startswith("http"):
                    href = "https://www.maritime.dot.gov" + href
                if href not in links:
                    links.append(href)
        print(f"  Found {len(links)} MARAD advisory links")
        for link in links[:10]:
            try:
                r2 = requests.get(link, headers=HEADERS, timeout=10)
                soup2 = BeautifulSoup(r2.text, "html.parser")
                text += " " + soup2.get_text(separator=" ").lower()
            except Exception as e:
                print(f"  Skip {link[:50]}: {e}")
        print(f"  MARAD: {len(text)} chars fetched")
    except Exception as e:
        print(f"  MARAD failed: {e}")
    return text

def fetch_ukmto():
    print("Trying UKMTO...")
    text = ""
    try:
        r = requests.get(
            "https://www.ukmto.org/indian-ocean/recent-incidents",
            headers=HEADERS, timeout=15
        )
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(separator=" ").lower()
            print(f"  UKMTO: {len(text)} chars fetched")
        else:
            print(f"  UKMTO returned {r.status_code}")
    except Exception as e:
        print(f"  UKMTO failed: {e}")
    return text

def fetch_gcaptain():
    print("Trying gCaptain RSS...")
    text = ""
    try:
        r = requests.get("https://gcaptain.com/feed/", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "xml")
            items = soup.find_all("item")[:20]
            for item in items:
                title = item.find("title")
                desc  = item.find("description")
                if title: text += " " + title.get_text().lower()
                if desc:  text += " " + desc.get_text().lower()
            print(f"  gCaptain: {len(text)} chars from {len(items)} articles")
        else:
            print(f"  gCaptain returned {r.status_code}")
    except Exception as e:
        print(f"  gCaptain failed: {e}")
    return text

def score_region(text, region):
    base = BASE_SCORES.get(region, 1.0)
    if region in STATIC_REASONS:
        return base, STATIC_REASONS[region]
    cfg = REGIONS.get(region)
    if not cfg:
        return base, "No advisory data available."
    if not any(term in text for term in cfg['terms']):
        return base, f'No specific advisory mentions for {region} in current sources.'
    high_hits   = sum(1 for kw in cfg['high']   if kw in text)
    medium_hits = sum(1 for kw in cfg['medium'] if kw in text)
    low_hits    = sum(1 for kw in cfg['low']    if kw in text)
    score = base
    if   high_hits >= 4:    score = min(10.0, base + 2.5)
    elif high_hits >= 2:    score = min(10.0, base + 1.5)
    elif high_hits >= 1:    score = min(10.0, base + 0.8)
    elif medium_hits >= 3:  score = min(10.0, base + 0.5)
    elif medium_hits >= 1:  score = min(10.0, base + 0.2)
    elif low_hits    >= 3:  score = max(0,    base - 0.3)
    now = datetime.utcnow().strftime('%d %b %Y %H:%M UTC')
    reason = (
        f'Advisory scan {now}: '
        f'{high_hits} critical + {medium_hits} elevated keyword matches. '
        f'Sources: MARAD / UKMTO / gCaptain.'
    )
    return round(score, 1), reason

def read_existing_scores():
    existing = {}
    try:
        with open("backend/conflict.py", "r") as f:
            content = f.read()
        matches = re.findall(r'"([^"]+)":\s*\(([\d.]+),\s*"([^"]+)"\)', content)
        for name, score, reason in matches:
            existing[name] = (float(score), reason)
        print(f"  Read {len(existing)} existing scores as fallback")
    except Exception as e:
        print(f"  Could not read existing scores: {e}")
    return existing

def rebuild_conflict_py(scores):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    lines = []
    lines.append("# conflict.py")
    lines.append(f"# Auto-updated by GitHub Actions on {now}")
    lines.append("# Sources: MARAD MSCI · UKMTO · gCaptain RSS")
    lines.append("# Schedule: Daily at 06:00 UTC")
    lines.append("# DO NOT EDIT MANUALLY")
    lines.append("")
    lines.append("CHOKEPOINT_RISK = {")
    for name, (score, reason) in scores.items():
        reason_clean = reason.replace('"', '\\"').replace("\n", " ")
        lines.append(f'    "{name}": ({score}, "{reason_clean}"),')
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("def get_conflict_risk(passages):")
    lines.append("    breakdown = {}")
    lines.append("    for p in passages:")
    lines.append("        if p in CHOKEPOINT_RISK:")
    lines.append("            score, reason = CHOKEPOINT_RISK[p]")
    lines.append('            breakdown[p] = {"score": score, "reason": reason}')
    lines.append("    if not breakdown:")
    lines.append("        return {")
    lines.append('            "conflict_risk_score" : 0.0,')
    lines.append('            "risk_label"          : "Minimal",')
    lines.append('            "highest_risk_point"  : "None",')
    lines.append('            "key_concern"         : "No major chokepoints on this route",')
    lines.append('            "breakdown"           : {},')
    lines.append("        }")
    lines.append("    worst = max(breakdown, key=lambda p: breakdown[p]['score'])")
    lines.append("    score = breakdown[worst]['score']")
    lines.append("    return {")
    lines.append('        "conflict_risk_score" : score,')
    lines.append('        "risk_label"          : ("Minimal" if score<2 else "Low" if score<4')
    lines.append('                                 else "Moderate" if score<6 else "Elevated"')
    lines.append('                                 if score<8 else "High"),')
    lines.append('        "highest_risk_point"  : worst,')
    lines.append('        "key_concern"         : breakdown[worst]["reason"],')
    lines.append('        "breakdown"           : {k: v["score"] for k,v in breakdown.items()},')
    lines.append("    }")
    lines.append("")
    with open("backend/conflict.py", "w") as f:
        f.write("\n".join(lines))
    print("✅ conflict.py rebuilt successfully")

def main():
    print(f"\n{'='*55}")
    print(f"SeaRoute Conflict Updater — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}\n")
    existing = read_existing_scores()
    combined = ""
    combined += fetch_marad()
    combined += fetch_ukmto()
    combined += fetch_gcaptain()
    if not combined.strip():
        print("\n⚠ All sources failed — keeping existing scores unchanged.")
        return
    print(f"\nTotal advisory text: {len(combined):,} characters")
    print("\nScoring chokepoints:")
    scores = {}
    changed = []
    for region, base in BASE_SCORES.items():
        new_score, reason = score_region(combined, region)
        old_score = existing.get(region, (base, ''))[0] if existing else base
        delta = round(new_score - old_score, 1)
        delta_str = f"  ({'+' if delta>0 else ''}{delta})" if delta != 0 else ''
        print(f"  {region:<25} {new_score}/10{delta_str}")
        scores[region] = (new_score, reason)
        if delta != 0:
            changed.append(f'{region}: {old_score} -> {new_score}')
    if changed:
        print(f"\n📊 Changes detected ({len(changed)}):")
        for c in changed: print(f'  {c}')
    else:
        print("\n✓ No score changes detected today.")
    rebuild_conflict_py(scores)
    log = {
        "last_updated"     : datetime.utcnow().isoformat(),
        "sources_used"     : ["MARAD", "UKMTO", "gCaptain"],
        "text_chars"       : len(combined),
        "changes_detected" : len(changed),
        "changes"          : changed,
        "scores"           : {k: v[0] for k, v in scores.items()},
    }
    os.makedirs("backend", exist_ok=True)
    with open("backend/conflict_update_log.json", "w") as f:
        json.dump(log, f, indent=2)
    print("\n✅ Update log written to backend/conflict_update_log.json")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    main()