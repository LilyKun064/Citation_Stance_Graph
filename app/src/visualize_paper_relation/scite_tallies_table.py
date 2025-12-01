# src/visualize_paper_relation/scite_tallies_table.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import json
import pandas as pd


def scite_tallies_json_to_csv(
    tallies_json: Path,
    out_csv: Path,
) -> Dict[str, Any]:
    """
    Convert a tallies.json (doi -> scite tallies dict or None)
    into a flat CSV with one row per DOI.

    Fields:
      - doi
      - supporting
      - contradicting
      - mentioning
      - unclassified
      - total
      - citingPublications
    """
    if not tallies_json.exists():
        raise FileNotFoundError(f"Scite tallies JSON not found: {tallies_json}")

    out_csv.parent.mkdir(parents=True, exist_ok=True)

    data = json.loads(tallies_json.read_text(encoding="utf-8"))

    records = []
    for doi, t in data.items():
        if t is None:
            records.append(
                {
                    "doi": doi,
                    "supporting": 0,
                    "contradicting": 0,
                    "mentioning": 0,
                    "unclassified": 0,
                    "total": 0,
                    "citingPublications": 0,
                }
            )
        else:
            records.append(
                {
                    "doi": doi,
                    "supporting": t.get("supporting", 0),
                    "contradicting": t.get("contradicting", 0),
                    "mentioning": t.get("mentioning", 0),
                    "unclassified": t.get("unclassified", 0),
                    "total": t.get("total", 0),
                    "citingPublications": t.get("citingPublications", 0),
                }
            )

    df = pd.DataFrame(records)
    df.to_csv(out_csv, index=False)

    print(f"[scite] Wrote {out_csv} with {len(df)} DOIs.")

    return {
        "scite_tallies_csv": out_csv,
        "scite_tallies_df": df,
    }
