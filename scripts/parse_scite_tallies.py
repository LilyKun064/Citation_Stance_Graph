#!/usr/bin/env python
"""
Step 5B: Convert tallies.json -> scite_tallies.csv

Input:
    data/raw/scite/tallies.json

Output:
    data/processed/scite_tallies.csv
"""

import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_SCITE_JSON = PROJECT_ROOT / "data" / "raw" / "scite" / "tallies.json"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUT_CSV = PROCESSED_DIR / "scite_tallies.csv"


def main():
    data = json.loads(RAW_SCITE_JSON.read_text(encoding="utf-8"))

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
    df.to_csv(OUT_CSV, index=False)

    print(f"Wrote {OUT_CSV} with {len(df)} DOIs.")


if __name__ == "__main__":
    main()
