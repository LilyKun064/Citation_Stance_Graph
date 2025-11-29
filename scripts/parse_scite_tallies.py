#!/usr/bin/env python
"""
Step 5B: Convert tallies.json -> scite_tallies.csv for a given collection.

Usage:
    python scite_tallies_to_csv.py <collection_name>

Input:
    data/<collection_name>/raw/scite/tallies.json

Output:
    data/<collection_name>/processed/scite_tallies.csv
"""

import json
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def main():
    if len(sys.argv) < 2:
        print("Usage: python scite_tallies_to_csv.py <collection_name>")
        sys.exit(1)

    collection = sys.argv[1]

    # Paths for this collection
    collection_dir = DATA_DIR / collection
    raw_scite_json = collection_dir / "raw" / "scite" / "tallies.json"
    processed_dir = collection_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_csv = processed_dir / "scite_tallies.csv"

    if not raw_scite_json.exists():
        raise FileNotFoundError(f"Scite tallies JSON not found: {raw_scite_json}")

    data = json.loads(raw_scite_json.read_text(encoding="utf-8"))

    records = []

    for doi, t in data.items():
        if t is None:  # no scite data
            records.append({
                "doi": doi,
                "supporting": 0,
                "contradicting": 0,
                "mentioning": 0,
                "unclassified": 0,
                "total": 0,
                "citingPublications": 0,
            })
            continue

        records.append({
            "doi": doi,
            "supporting": t.get("supporting", 0),
            "contradicting": t.get("contradicting", 0),
            "mentioning": t.get("mentioning", 0),
            "unclassified": t.get("unclassified", 0),
            "total": t.get("total", 0),
            "citingPublications": t.get("citingPublications", 0),
        })

    df = pd.DataFrame(records)
    df.to_csv(out_csv, index=False)

    print(f"Wrote {out_csv} with {len(df)} DOIs.")


if __name__ == "__main__":
    main()
