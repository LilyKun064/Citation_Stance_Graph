# src/visualize_paper_relation/edge_filter.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import pandas as pd


def filter_collection_edges(
    papers_csv: Path,
    edges_raw_csv: Path,
    edges_coll_csv: Path,
) -> Dict[str, Any]:
    """
    Filter edges so that only those with a citing paper that is
    IN the Zotero-based collection are kept.

    Inputs:
      - papers_csv: path to papers.csv
      - edges_raw_csv: path to citation_edges_raw.csv
      - edges_coll_csv: output path for citation_edges_collection.csv

    Returns:
      {
        "edges_collection_csv": Path,
        "edges_collection_df": DataFrame,
      }
    """
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
        f"[EdgeFilter] Wrote {edges_coll_csv} with {len(edges_coll)} edges "
        f"from {len(in_coll_ids)} collection papers."
    )

    return {
        "edges_collection_csv": edges_coll_csv,
        "edges_collection_df": edges_coll,
    }
