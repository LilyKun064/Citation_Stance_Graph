#!/usr/bin/env python
"""
Step 7: Build NetworkX graph with node attributes.

Inputs:
    data/processed/papers_with_scite.csv
    data/processed/citation_edges_collection.csv

Output:
    data/processed/citation_graph_openalex_with_scite.graphml

Nodes:
    - openalex_id (as node id)
    - title
    - year
    - doi
    - in_collection
    - scite_* tallies (if available)

Edges:
    citing_openalex_id -> cited_openalex_id
"""

from pathlib import Path

import pandas as pd
import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PAPERS_CSV = PROCESSED_DIR / "papers_with_scite.csv"  # from step 6
EDGES_COLL_CSV = PROCESSED_DIR / "citation_edges_collection.csv"
GRAPH_PATH = PROCESSED_DIR / "citation_graph_openalex_with_scite.graphml"


def main():
    if not PAPERS_CSV.exists():
        raise FileNotFoundError(f"Missing {PAPERS_CSV}")
    if not EDGES_COLL_CSV.exists():
        raise FileNotFoundError(f"Missing {EDGES_COLL_CSV}")

    papers = pd.read_csv(PAPERS_CSV)
    edges = pd.read_csv(EDGES_COLL_CSV)

    print(f"Loaded {len(papers)} papers and {len(edges)} edges.")

    G = nx.DiGraph()

    # --- Add nodes with attributes ---
    for _, row in papers.iterrows():
        node_id = str(row["openalex_id"])
        attrs = row.to_dict()
        # Ensure we don't have numpy types that cause GraphML issues
        attrs = {k: (None if pd.isna(v) else v) for k, v in attrs.items()}
        G.add_node(node_id, **attrs)

    # --- Add edges (only if both endpoints present as nodes) ---
    edge_count = 0
    for _, row in edges.iterrows():
        u = str(row["citing_openalex_id"])
        v = str(row["cited_openalex_id"])
        if u in G and v in G:
            G.add_edge(u, v)
            edge_count += 1

    print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges "
          f"({edge_count} edges actually added).")

    # --- Save as GraphML ---
    nx.write_graphml(G, GRAPH_PATH)
    print(f"Wrote {GRAPH_PATH}")


if __name__ == "__main__":
    main()
