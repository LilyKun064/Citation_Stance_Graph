# src/visualize_paper_relation/graph_build.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import pandas as pd
import networkx as nx


def build_graph_openalex_with_scite(
    papers_with_scite_csv: Path,
    edges_coll_csv: Path,
    graph_path: Path,
) -> Dict[str, Any]:
    """
    Build a directed NetworkX graph with node attributes from:

      - papers_with_scite.csv
      - citation_edges_collection.csv

    and save it as a GraphML file.

    Nodes:
      - openalex_id (as node id)
      - title
      - year
      - doi
      - in_collection
      - scite_* tallies (if present)

    Edges:
      citing_openalex_id -> cited_openalex_id
    """
    if not papers_with_scite_csv.exists():
        raise FileNotFoundError(f"Missing {papers_with_scite_csv}")
    if not edges_coll_csv.exists():
        raise FileNotFoundError(f"Missing {edges_coll_csv}")

    papers = pd.read_csv(papers_with_scite_csv)
    edges = pd.read_csv(edges_coll_csv)

    print(
        f"[graph-build] Loaded {len(papers)} papers and {len(edges)} edges "
        f"from processed tables."
    )

    G = nx.DiGraph()

    # --- Add nodes with attributes ---
    for _, row in papers.iterrows():
        node_id = str(row["openalex_id"])
        attrs = row.to_dict()
        # Avoid NaNs for GraphML
        attrs = {k: (None if pd.isna(v) else v) for k, v in attrs.items()}
        G.add_node(node_id, **attrs)

    # --- Add edges (only if both endpoints exist) ---
    edge_count = 0
    for _, row in edges.iterrows():
        u = str(row["citing_openalex_id"])
        v = str(row["cited_openalex_id"])
        if u in G and v in G:
            G.add_edge(u, v)
            edge_count += 1

    print(
        f"[graph-build] Graph has {G.number_of_nodes()} nodes and "
        f"{G.number_of_edges()} edges ({edge_count} edges actually added)."
    )

    graph_path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, graph_path)
    print(f"[graph-build] Wrote {graph_path}")

    return {
        "graphml_path": graph_path,
        "graph": G,
    }
