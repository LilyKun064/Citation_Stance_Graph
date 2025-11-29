#!/usr/bin/env python
"""
Step 2: Fetch OpenAlex metadata for each DOI.

Input:
    data/interim/doi_list.txt

Output:
    data/raw/openalex/{safe_doi}.json
"""

import os
import time
import json
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
RAW_OA_DIR = PROJECT_ROOT / "data" / "raw" / "openalex"
RAW_OA_DIR.mkdir(parents=True, exist_ok=True)

DOI_LIST_PATH = INTERIM_DIR / "doi_list.txt"

# Optional: use OPENALEX_MAILTO from environment / .env
MAILTO = os.environ.get("OPENALEX_MAILTO", "you@example.com")


def doi_to_filename(doi: str) -> str:
    """
    Convert DOI to a filesystem-safe filename.
    """
    return (
        doi.replace("https://doi.org/", "")
           .replace("http://doi.org/", "")
           .replace("/", "_")
           .replace(":", "_")
           .strip()
    )


def fetch_openalex_for_doi(doi: str) -> dict | None:
    """
    Fetch OpenAlex JSON for a single DOI.
    Returns the JSON dict on success, or None on failure.
    """
    # OpenAlex lets you query works via the DOI URL
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    params = {"mailto": MAILTO}

    print(f"[GET] {doi} -> {url}")
    try:
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code == 404:
            print(f"  -> 404 Not Found for DOI {doi}, skipping.")
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  !! Error fetching {doi}: {e}")
        return None


def main():
    if not DOI_LIST_PATH.exists():
        raise FileNotFoundError(f"DOI list not found at {DOI_LIST_PATH}")

    dois = [
        line.strip()
        for line in DOI_LIST_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(f"Found {len(dois)} DOIs in {DOI_LIST_PATH}")

    for doi in dois:
        fname = RAW_OA_DIR / f"{doi_to_filename(doi)}.json"
        if fname.exists():
            print(f"[skip] {doi} (already have {fname.name})")
            continue

        data = fetch_openalex_for_doi(doi)
        if data is None:
            continue

        fname.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  -> Saved to {fname}")

        # be polite to the API
        time.sleep(0.5)

    print("Done fetching OpenAlex metadata.")


if __name__ == "__main__":
    main()
