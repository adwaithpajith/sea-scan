#!/usr/bin/env python3
"""
Appends today's chokepoint scores to backend/risk_history.json.

Run by the daily workflow right after update_conflict.py. It reads the scores
that script just wrote to backend/conflict_update_log.json, so update_conflict.py
itself is untouched. One snapshot per UTC date: re-running the same day replaces
that day's entry, so the file never accumulates duplicates.
"""
import json
import os

LOG_PATH     = "backend/conflict_update_log.json"
HISTORY_PATH = "backend/risk_history.json"
MAX_SNAPSHOTS = 730   # ~2 years of daily data


def main():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log = json.load(f)
        date   = str(log["last_updated"])[:10]
        scores = {k: float(v) for k, v in log["scores"].items()}
    except Exception as e:
        print(f"History not updated - cannot read {LOG_PATH}: {e}")
        return

    snapshots = []
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                snapshots = json.load(f).get("snapshots", [])
        except Exception as e:
            print(f"Existing history unreadable ({e}) - starting fresh")

    snapshots = [s for s in snapshots if s.get("date") != date]
    snapshots.append({"date": date, "scores": scores})
    snapshots.sort(key=lambda s: s["date"])
    snapshots = snapshots[-MAX_SNAPSHOTS:]

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "snapshots": snapshots}, f, indent=1)
    print(f"History updated: {len(snapshots)} snapshot(s), latest {date}")


if __name__ == "__main__":
    main()
