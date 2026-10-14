"""
history.py - read access to the daily chokepoint risk snapshots.

backend/risk_history.json is written by update_history.py (run by the daily
GitHub Actions workflow) and committed to the repo, so history survives
Render's ephemeral filesystem. Format:
    {"version": 1, "snapshots": [{"date": "YYYY-MM-DD", "scores": {name: score}}]}
"""
import json
import os
from datetime import datetime, timedelta, timezone

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "risk_history.json")
_cache = {"mtime": None, "snapshots": []}


def load_snapshots():
    try:
        mtime = os.path.getmtime(HISTORY_PATH)
    except OSError:
        return []
    if _cache["mtime"] != mtime:
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            snaps = [s for s in data.get("snapshots", [])
                     if isinstance(s, dict) and "date" in s and isinstance(s.get("scores"), dict)]
            snaps.sort(key=lambda s: s["date"])
        except Exception as e:
            print(f"  risk_history.json unreadable: {e}")
            snaps = []
        _cache["mtime"], _cache["snapshots"] = mtime, snaps
    return _cache["snapshots"]


def _window(days):
    snaps = load_snapshots()
    if not days:
        return snaps
    cutoff = (datetime.now(timezone.utc) - timedelta(days=int(days))).strftime("%Y-%m-%d")
    return [s for s in snaps if s["date"] >= cutoff]


def get_history(days=None):
    """All chokepoint series over the window, aligned on a shared date axis."""
    snaps = _window(days)
    names = []
    for s in snaps:
        for n in s["scores"]:
            if n not in names:
                names.append(n)
    return {
        "snapshots": len(snaps),
        "first": snaps[0]["date"] if snaps else None,
        "last": snaps[-1]["date"] if snaps else None,
        "dates": [s["date"] for s in snaps],
        "series": {n: [s["scores"].get(n) for s in snaps] for n in names},
    }


def route_conflict_trend(passages, days=90):
    """Per-day conflict score of a route = worst chokepoint it crosses that day."""
    if not passages:
        return []
    out = []
    for s in _window(days):
        vals = [s["scores"][p] for p in passages if p in s["scores"]]
        if vals:
            out.append({"date": s["date"], "score": max(vals)})
    return out
