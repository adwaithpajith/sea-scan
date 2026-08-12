#!/usr/bin/env python3
"""
SeaRoute Intelligence Platform — Port Data Auto-Updater
Runs monthly via GitHub Actions.
Downloads latest NGA World Port Index CSV.
"""
import requests, os, hashlib
from datetime import datetime

HEADERS = {"User-Agent": "SeaRoute-Intelligence-Platform/2.0 (academic research)"}
NGA_URL = (
    "https://msi.nga.mil/api/publications/download"
    "?key=16920959/SFH00000/UpdatedPub150.csv&type=download"
)
OUTPUT_PATH = "backend/data/UpdatedPub150.csv"

def file_hash(path):
    if not os.path.exists(path): return None
    with open(path, "rb") as f: return hashlib.md5(f.read()).hexdigest()

def main():
    print(f"\n{'='*55}")
    print(f"SeaRoute Port Updater — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}\n")
    old_hash = file_hash(OUTPUT_PATH)
    print(f"Current file hash: {old_hash or chr(110)+chr(111)+chr(116)+chr(32)+chr(102)+chr(111)+chr(117)+chr(110)+chr(100)}")
    print("Downloading NGA World Port Index...")
    try:
        r = requests.get(NGA_URL, headers=HEADERS, timeout=60)
        if r.status_code != 200:
            print(f"⚠ NGA returned {r.status_code} — keeping existing file.")
            return
        content = r.content
        if len(content) < 100_000:
            print(f"⚠ Download too small ({len(content)} bytes) — likely error page.")
            return
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "wb") as f: f.write(content)
        new_hash = file_hash(OUTPUT_PATH)
        size_mb  = len(content) / 1_048_576
        if old_hash == new_hash:
            print(f"✓ No changes ({size_mb:.1f} MB) — NGA data is current.")
        else:
            print(f"✅ Port data updated ({size_mb:.1f} MB)")
            print(f"   Old hash: {old_hash}")
            print(f"   New hash: {new_hash}")
            lines = content.decode("latin-1").split("\n")
            port_count = len([l for l in lines if l.strip() and not l.startswith("OID")]) - 1
            print(f"   Ports in dataset: ~{port_count:,}")
    except Exception as e:
        print(f"⚠ Download failed: {e} — keeping existing file.")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    main()