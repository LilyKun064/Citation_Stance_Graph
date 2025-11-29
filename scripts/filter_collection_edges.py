#!/usr/bin/env python
"""
Step 4: Filter edges to only those originating from your collection.

Usage:
    python filter_collection_edges.py <collection_name>

Inputs (for that collection):
    data/<collection_name>/processed/papers.csv
    data/<collection_name>/processed/citation_edges_raw.csv

Output:
    data/<collection_name>/processed/citation_edges_collection.csv

Each row:
    citing_openalex_id, cited_openalex_id
where citing_openalex_id is in the Zotero-based collection.
"""

import sys
from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def main():
    if len(sys.argv) < 2:
        print("Usage: python filter_collection_edges.py <collection_name>")
        sys.exit(1)

    collection = sys.argv[1]

    processed_dir = DATA_DIR / collection / "processed"
    papers_csv = processed_dir / "papers.csv"
    edges_raw_csv = processed_dir / "citation_edges_raw.csv"
    edges_coll_csv = processed_dir / "citation_edges_collection.csv"

    if not papers_csv.exists():
        raise FileNotFoundError(f"Missing papers.csv at {papers_csv}")
    if not edges_raw_csv.exists():
        raise FileNotFoundError(f"Missing citation_edges_raw.csv at {edges_raw_csv}")

    papers = pd.read_csv(papers_csv)
    edges_raw = pd.read_csv(edges_raw_csv)

    # All OpenAlex IDs that are in your Zotero collection
    in_coll_ids = set(papers["openalex_id"].astype(str))

    # Keep only edges where the citing paper is in your collection
    edges_raw["citing_openalex_id"] = edges_raw["citing_openalex_id"].astype(str)
    edges_raw["cited_openalex_id"] = edges_raw["cited_openalex_id"].astype(str)

    edges_coll = edges_raw[edges_raw["citing_openalex_id"].isin(in_coll_ids)].copy()

    edges_coll.to_csv(edges_coll_csv, index=False)
    print(
        f"Wrote {edges_coll_csv} with {len(edges_coll)} edges "
        f"from {len(in_coll_ids)} collection papers."
    )


if __name__ == "__main__":
    main()
