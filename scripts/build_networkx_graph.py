#!/usr/bin/env python
"""
Step 7: Build NetworkX graph with node attributes for a given collection.

Usage:
    python build_graph_openalex_with_scite.py <collection_name>

Inputs:
    data/<collection_name>/processed/papers_with_scite.csv
    data/<collection_name>/processed/citation_edges_collection.csv

Output:
    data/<collection_name>/processed/citation_graph_openalex_with_scite.graphml

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

import sys
from pathlib import Path

import pandas as pd
import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_graph_openalex_with_scite.py <collection_name>")
        sys.exit(1)

    collection = sys.argv[1]

    processed_dir = DATA_DIR / collection / "processed"
    papers_csv = processed_dir / "papers_with_scite.csv"
    edges_coll_csv = processed_dir / "citation_edges_collection.csv"
    graph_path = processed_dir / "citation_graph_openalex_with_scite.graphml"

    if not papers_csv.exists():
        raise FileNotFoundError(f"Missing {papers_csv}")
    if not edges_coll_csv.exists():
        raise FileNotFoundError(f"Missing {edges_coll_csv}")

    papers = pd.read_csv(papers_csv)
    edges = pd.read_csv(edges_coll_csv)

    print(f"Loaded {len(papers)} papers and {len(edges)} edges for collection '{collection}'.")

    G = nx.DiGraph()

    # --- Add nodes with attributes ---
    for _, row in papers.iterrows():
        node_id = str(row["openalex_id"])
        attrs = row.to_dict()
        # Ensure we don't have numpy NaNs that cause GraphML issues
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

    print(
        f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges "
        f"({edge_count} edges actually added)."
    )

    # --- Save as GraphML ---
    nx.write_graphml(G, graph_path)
    print(f"Wrote {graph_path}")


if __name__ == "__main__":
    main()
