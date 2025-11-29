#!/usr/bin/env python
"""
Step 5A: Fetch scite.ai tallies for each DOI in a given collection.

Usage:
    python fetch_scite_tallies.py <collection_name>

Inputs:
    data/<collection_name>/interim/doi_list.txt

Output:
    data/<collection_name>/raw/scite/tallies.json
"""

import json
import os
import sys
import time
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

SCITE_KEY = os.environ.get("SCITE_API_KEY")  # optional


def fetch_scite_for_doi(doi: str) -> dict | None:
    """
    Returns tallies for a DOI using free or paid scite API.
    """
    url = f"https://api.scite.ai/tallies/{doi}"
    headers = {"x-api-key": SCITE_KEY} if SCITE_KEY else {}

    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 404:
            print(f"  -> Scite: no data for {doi}")
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  !! Scite error for {doi}: {e}")
        return None


def main():
    # --- read CLI argument ---
    if len(sys.argv) < 2:
        print("Usage: python fetch_scite_tallies.py <collection_name>")
        sys.exit(1)

    collection = sys.argv[1]

    # Directory layout
    collection_dir = DATA_DIR / collection
    interim_dir = collection_dir / "interim"
    raw_scite_dir = collection_dir / "raw" / "scite"
    raw_scite_dir.mkdir(parents=True, exist_ok=True)

    doi_list_path = interim_dir / "doi_list.txt"
    out_json = raw_scite_dir / "tallies.json"

    if not doi_list_path.exists():
        raise FileNotFoundError(f"DOI list not found: {doi_list_path}")

    # Load DOIs
    dois = [
        line.strip()
        for line in doi_list_path.read_text().splitlines()
        if line.strip()
    ]
    print(f"Fetching scite tallies for {len(dois)} DOIs.")

    tallies = {}

    # Fetch one by one
    for doi in dois:
        print(f"[scite] {doi}")
        info = fetch_scite_for_doi(doi)
        tallies[doi] = info
        time.sleep(0.3)  # throttle to avoid rate limits

    # Write output
    out_json.write_text(
        json.dumps(tallies, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
