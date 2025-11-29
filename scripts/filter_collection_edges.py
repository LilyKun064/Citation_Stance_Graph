#!/usr/bin/env python
"""
Step 4: Filter edges to only those originating from your collection.

Inputs:
    data/processed/papers.csv
    data/processed/citation_edges_raw.csv

Output:
    data/processed/citation_edges_collection.csv

Each row:
    citing_openalex_id, cited_openalex_id
where citing_openalex_id is in the Zotero-based collection.
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PAPERS_CSV = PROCESSED_DIR / "papers.csv"
EDGES_RAW_CSV = PROCESSED_DIR / "citation_edges_raw.csv"
EDGES_COLL_CSV = PROCESSED_DIR / "citation_edges_collection.csv"


def main():
    if not PAPERS_CSV.exists():
        raise FileNotFoundError(f"Missing papers.csv at {PAPERS_CSV}")
    if not EDGES_RAW_CSV.exists():
        raise FileNotFoundError(f"Missing citation_edges_raw.csv at {EDGES_RAW_CSV}")

    papers = pd.read_csv(PAPERS_CSV)
    edges_raw = pd.read_csv(EDGES_RAW_CSV)

    # All OpenAlex IDs that are in your Zotero collection
    in_coll_ids = set(papers["openalex_id"].astype(str))

    # Keep only edges where the citing paper is in your collection
    edges_raw["citing_openalex_id"] = edges_raw["citing_openalex_id"].astype(str)
    edges_raw["cited_openalex_id"] = edges_raw["cited_openalex_id"].astype(str)

    edges_coll = edges_raw[edges_raw["citing_openalex_id"].isin(in_coll_ids)].copy()

    edges_coll.to_csv(EDGES_COLL_CSV, index=False)
    print(f"Wrote {EDGES_COLL_CSV} with {len(edges_coll)} edges "
          f"from {len(in_coll_ids)} collection papers.")


if __name__ == "__main__":
    main()
