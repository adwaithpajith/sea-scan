#!/usr/bin/env python3
"""
SeaRoute Intelligence Platform — Conflict Risk Auto-Updater
Runs daily via GitHub Actions.
Sources: MARAD MSCI (primary) -> UKMTO (fallback) -> gCaptain RSS (fallback)
"""
import requests
from bs4 import BeautifulSoup
import re, os, json, time
import xml.etree.ElementTree as ET
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
    "Bab el-Mandeb"       : 7.5,
    "Suez Canal"          : 3.5,
    "Strait of Hormuz"    : 8.0,
    "Strait of Malacca"   : 3.0,
    "Luzon Strait"        : 4.0,
    "Strait of Gibraltar" : 1.5,
    "Dover Strait"        : 1.0,
    "Bosphorus Strait"    : 5.5,
    "Panama Canal"        : 2.0,
    "Cape of Good Hope"   : 1.0,
    "Lombok Strait"       : 2.0,
    "Tsugaru Strait"      : 1.5,
    "Cape Horn"           : 1.0,
    "Strait of Magellan"  : 1.0,
    "Danish Straits"      : 3.0,
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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_marad():
    print("Trying MARAD...")
    text = ""
    headlines = []
    try:
        r = None
        for attempt in range(2):
            r = requests.get(
                "https://www.maritime.dot.gov/msci-advisories",
                headers=HEADERS, timeout=15
            )
            if r.status_code == 200:
                break
            print(f"  MARAD attempt {attempt+1} returned {r.status_code}")
            if attempt == 0:
                time.sleep(3)
        if r.status_code != 200:
            print(f"  MARAD failed after retry: {r.status_code}")
            return "", []
        # Only look at the "Active Advisories" section of the page — cut the
        # HTML off before "Cancelled Advisories" so expired advisories don't
        # get scored as current risk.
        html = r.text
        cutoff = html.find("Cancelled Advisories")
        active_html = html[:cutoff] if cutoff != -1 else html

        soup = BeautifulSoup(active_html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Real MARAD advisory URLs look like:
            #   /msci/2026-006-red-sea-bab-el-mandeb-strait-...-houthi-attacks
            # i.e. a 4-digit year + 3-digit advisory number, NOT the literal
            # word "advisory"/"alert"/"notice" in the URL — matching on those
            # words (the old approach) matches zero real advisory links.
            if re.search(r"/msci/\d{4}-\d{3}-", href):
                full = href if href.startswith("http") else "https://www.maritime.dot.gov" + href
                title = a.get_text(strip=True)
                if full not in [l[0] for l in links]:
                    links.append((full, title))
        print(f"  Found {len(links)} active MARAD advisory links")
        for _, title in links:
            print(f"    - {title}")

        # Advisory titles alone are high-signal (e.g. "Red Sea, Bab el Mandeb
        # Strait ... Houthi Attacks on Commercial Vessels"), so fold them in
        # even before the subpage fetch below, and keep them separately so
        # the actual headline can be quoted in the UI later, not just a
        # keyword-hit count.
        for _, title in links:
            text += " " + title.lower()
            if title:
                headlines.append(title)

        for link, _ in links[:15]:
            try:
                r2 = requests.get(link, headers=HEADERS, timeout=10)
                soup2 = BeautifulSoup(r2.text, "html.parser")
                text += " " + soup2.get_text(separator=" ").lower()
            except Exception as e:
                print(f"  Skip {link[:50]}: {e}")
        print(f"  MARAD: {len(text)} chars fetched")
    except Exception as e:
        print(f"  MARAD failed: {e}")
    return text, headlines

def fetch_ukmto():
    print("Trying UKMTO...")
    text = ""

    # KNOWN LIMITATION: ukmto.org's product/incident listing pages are
    # client-side rendered (React/Vue-style SPA). A plain requests.get() gets
    # back an empty shell ("No products to display" / "0 reports") regardless
    # of what data actually exists behind it — this is a JS-rendering
    # limitation, not a URL or selector bug. Real incident content exists on
    # this domain (e.g. JMIC Advisory Note PDFs), but reliably discovering and
    # reading it needs a headless browser (e.g. Playwright) rather than
    # requests+BeautifulSoup. Left in place as a harmless best-effort call —
    # if UKMTO ever serves this page server-rendered, it starts working with
    # no further changes needed.
    try:
        r = requests.get(
            "https://www.ukmto.org/indian-ocean/recent-incidents",
            headers=HEADERS, timeout=15
        )
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(separator=" ").lower()
            print(f"  UKMTO: {len(text)} chars fetched (likely near-empty — see known limitation above)")
        else:
            print(f"  UKMTO returned {r.status_code}")
    except Exception as e:
        print(f"  UKMTO failed: {e}")
    return text

def fetch_gcaptain():
    print("Trying gCaptain RSS...")
    text = ""
    headlines = []
    try:
        r = requests.get("https://gcaptain.com/feed/", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            # Use the standard-library XML parser rather than
            # BeautifulSoup(..., "xml"), which silently requires the
            # optional `lxml` package that this workflow does not install.
            root = ET.fromstring(r.content)
            items = root.findall(".//item")[:20]
            for item in items:
                title_el = item.find("title")
                desc_el  = item.find("description")
                if title_el is not None and title_el.text:
                    text += " " + title_el.text.lower()
                    headlines.append(title_el.text.strip())
                if desc_el is not None and desc_el.text:
                    text += " " + desc_el.text.lower()
            print(f"  gCaptain: {len(text)} chars from {len(items)} articles")
        else:
            print(f"  gCaptain returned {r.status_code}")
    except Exception as e:
        print(f"  gCaptain failed: {e}")
    return text, headlines

def score_region(text, region, headlines=None):
    headlines = headlines or []
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

    # Find the actual headline that mentions this region, so the reason can
    # name the real event instead of only reporting a keyword-hit count.
    matching_headline = None
    for h in headlines:
        h_lower = h.lower()
        if any(term in h_lower for term in cfg['terms']):
            matching_headline = h.strip()
            break

    if matching_headline:
        reason = (
            f'"{matching_headline}" \u2014 scan {now}: '
            f'{high_hits} critical + {medium_hits} elevated keyword matches.'
        )
    else:
        # No specific headline available (e.g. the match came from a
        # near-empty UKMTO fetch or an advisory subpage body rather than a
        # captured title) — fall back to the count-only summary.
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
    all_headlines = []

    marad_text, marad_headlines = fetch_marad()
    combined += marad_text
    all_headlines += marad_headlines

    ukmto_text = fetch_ukmto()
    combined += ukmto_text

    gcap_text, gcap_headlines = fetch_gcaptain()
    combined += gcap_text
    all_headlines += gcap_headlines

    if not combined.strip():
        print("\n⚠ All sources failed — keeping existing scores unchanged.")
        return
    print(f"\nTotal advisory text: {len(combined):,} characters")
    print("\nScoring chokepoints:")
    scores = {}
    changed = []
    for region, base in BASE_SCORES.items():
        new_score, reason = score_region(combined, region, all_headlines)
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
