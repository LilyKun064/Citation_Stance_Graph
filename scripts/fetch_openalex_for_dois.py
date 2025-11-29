#!/usr/bin/env python
"""
Step 2: Fetch OpenAlex metadata for a collection.

Usage:
    python fetch_openalex.py <collection_name>
"""

import os
import sys
import time
import json
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

MAILTO = os.environ.get("OPENALEX_MAILTO", "you@example.com")


def doi_to_filename(doi: str) -> str:
    return doi.replace("/", "_").replace(":", "_")


def fetch_openalex(doi: str):
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    try:
        r = requests.get(url, params={"mailto": MAILTO}, timeout=20)
        if r.status_code == 404:
            print(f"404 for {doi}, skipping")
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"ERROR fetching {doi}: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_openalex.py <collection_name>")
        sys.exit(1)

    collection = sys.argv[1]

    root = DATA_DIR / collection
    interim_dir = root / "interim"
    oa_dir = root / "raw" / "openalex"
    oa_dir.mkdir(parents=True, exist_ok=True)

    doi_list = interim_dir / "doi_list.txt"
    if not doi_list.exists():
        raise FileNotFoundError(f"DOI list not found: {doi_list}")

    dois = [x.strip() for x in doi_list.read_text().splitlines() if x.strip()]

    for doi in dois:
        out = oa_dir / f"{doi_to_filename(doi)}.json"
        if out.exists():
            print(f"[skip] {doi}")
            continue

        data = fetch_openalex(doi)
        if data:
            out.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Saved {out}")

        time.sleep(0.5)


if __name__ == "__main__":
    main()
