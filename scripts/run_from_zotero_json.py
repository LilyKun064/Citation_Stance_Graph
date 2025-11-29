#!/usr/bin/env python
"""
Step 1: Extract DOIs from a given Zotero JSON export.

Usage:
    python extract_dois.py <collection_name>
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def normalize_doi(raw: str | None) -> str | None:
    if not raw:
        return None
    doi = raw.strip()

    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "DOI:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]

    return doi.lower() if "/" in doi else None


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_dois.py <collection_name>")
        sys.exit(1)

    collection = sys.argv[1]

    # Directories
    root = DATA_DIR / collection
    zotero_dir = root / "raw" / "zotero"
    interim_dir = root / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)

    zotero_json = zotero_dir / f"{collection}.json"
    out_path = interim_dir / "doi_list.txt"

    if not zotero_json.exists():
        raise FileNotFoundError(f"Zotero JSON not found: {zotero_json}")

    # Load
    data = json.loads(zotero_json.read_text(encoding="utf-8"))

    # Determine structure
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("items", [data])
    else:
        raise TypeError("Unexpected JSON structure.")

    # Extract DOIs
    dois = []
    for it in items:
        inner = it.get("data") if isinstance(it.get("data"), dict) else it
        doi = normalize_doi(inner.get("DOI") or inner.get("doi"))
        if doi:
            dois.append(doi)

    dois = sorted(set(dois))

    out_path.write_text("\n".join(dois), encoding="utf-8")
    print(f"Extracted {len(dois)} DOIs → {out_path}")


if __name__ == "__main__":
    main()
