#!/usr/bin/env python
"""
Step 1: Extract DOIs from Zotero JSON export.

Input:
    data/raw/zotero/LLM_Gender_Bias.json

Output:
    data/interim/doi_list.txt
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "zotero"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

ZOTERO_JSON = RAW_DIR / "LLM_Gender_Bias.json"
OUT_PATH = INTERIM_DIR / "doi_list.txt"


def normalize_doi(raw: str | None) -> str | None:
    if not raw:
        return None
    doi = raw.strip()

    # Strip common prefixes
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "DOI:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]

    doi = doi.strip()
    # Very rough sanity check
    if "/" not in doi:
        return None

    return doi.lower()


def main():
    print(f"Loading Zotero JSON from {ZOTERO_JSON} ...")
    raw_text = ZOTERO_JSON.read_text(encoding="utf-8")
    data = json.loads(raw_text)

    # --- figure out where the items actually are ---
    if isinstance(data, list):
        items = data
        print("Top-level JSON is a LIST.")
    elif isinstance(data, dict):
        if "items" in data:
            items = data["items"]
            print("Top-level JSON is a DICT with 'items' key.")
        else:
            # Fallback: treat the dict itself as a single item
            items = [data]
            print("Top-level JSON is a DICT (no 'items'); treating as single item.")
    else:
        raise TypeError(f"Unexpected JSON top-level type: {type(data)}")

    dois: list[str] = []

    for it in items:
        if not isinstance(it, dict):
            # skip anything weird
            continue

        # Zotero export usually nests fields under "data"
        if "data" in it and isinstance(it["data"], dict):
            inner = it["data"]
        else:
            inner = it

        doi_raw = inner.get("DOI") or inner.get("doi")

        doi_norm = normalize_doi(doi_raw)
        if doi_norm:
            dois.append(doi_norm)

    dois = sorted(set(dois))
    print(f"Extracted {len(dois)} unique DOIs.")

    OUT_PATH.write_text("\n".join(dois), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
