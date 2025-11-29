#!/usr/bin/env python
"""
Step 5A: Fetch scite.ai tallies for each DOI.

Input:
    data/interim/doi_list.txt

Output:
    data/raw/scite/tallies.json  (big dict: doi -> tallies)
"""

import json
import os
import time
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
RAW_SCITE_DIR = PROJECT_ROOT / "data" / "raw" / "scite"
RAW_SCITE_DIR.mkdir(parents=True, exist_ok=True)

DOI_LIST_PATH = INTERIM_DIR / "doi_list.txt"
OUT_JSON = RAW_SCITE_DIR / "tallies.json"

SCITE_KEY = os.environ.get("SCITE_API_KEY")  # optional


def fetch_scite_for_doi(doi: str) -> dict | None:
    """
    Returns tallies for a DOI using either:
        - Paid API (if SCITE_API_KEY is set)
        - Public free endpoint (slow but OK)
    """

    # Free endpoint:
    url = f"https://api.scite.ai/tallies/{doi}"

    headers = {}
    if SCITE_KEY:
        headers["x-api-key"] = SCITE_KEY

    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 404:
            print(f"  -> Scite: No data for {doi}")
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  !! Scite error for {doi}: {e}")
        return None


def main():
    dois = [
        line.strip()
        for line in DOI_LIST_PATH.read_text().splitlines()
        if line.strip()
    ]
    print(f"Fetching scite for {len(dois)} DOIs.")

    tallies = {}

    for doi in dois:
        print(f"[scite] {doi}")
        info = fetch_scite_for_doi(doi)
        tallies[doi] = info
        time.sleep(0.3)  # throttle

    OUT_JSON.write_text(
        json.dumps(tallies, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
