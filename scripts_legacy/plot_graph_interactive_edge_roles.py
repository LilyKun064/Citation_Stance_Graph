#!/usr/bin/env python
"""
Final interactive citation graph with per-edge LLM roles,
prettier layout and author-year labels, for a given collection.

Usage:
    python plot_graph_interactive_edge_roles.py <collection_name>

Inputs:
    data/<collection_name>/processed/citation_graph_openalex_with_scite.graphml
    data/<collection_name>/processed/edge_roles_llm.csv
    data/<collection_name>/raw/openalex/*.json  (for author names)

Output:
    data/<collection_name>/processed/citation_graph_edge_roles.html

Semantics:
    - Nodes: papers in your Zotero collection
    - Edge A -> B: A cites B
    - Edge color:
        SUPPORT  -> green (A agrees with B)
        DISPUTE  -> red   (A disagrees with B)
        else     -> gray  (BACKGROUND / METHOD / neutral mention)
"""

import sys
import json
from pathlib import Path

import pandas as pd
import networkx as nx
from pyvis.network import Network


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


# ---------------------------------------------------------------------
# Role -> color mapping
# ---------------------------------------------------------------------

def map_role_to_color(role: str) -> str:
    """
    Map LLM role to edge color.

    SUPPORT  -> green
    DISPUTE  -> red
    BACKGROUND / METHOD / unknown -> gray
    """
    if not isinstance(role, str):
        return "gray"
    r = role.strip().upper()
    if r == "SUPPORT":
        return "green"
    if r == "DISPUTE":
        return "red"
    return "gray"


# ---------------------------------------------------------------------
# Build short labels: "Bordia & Bowman 2019"
# ---------------------------------------------------------------------

def build_short_label_lookup(raw_oa_dir: Path) -> dict:
    """
    Scan raw_oa_dir/*.json and build:
        openalex_id -> "Author 2019" or "Author1 & Author2 2019" etc.
    """
    labels: dict[str, str] = {}

    json_files = sorted(raw_oa_dir.glob("*.json"))
    print(f"Loading author info from {len(json_files)} OpenAlex JSON files in {raw_oa_dir} ...")

    for path in json_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  !! Skipping {path.name}: JSON decode error")
            continue

        work_id = data.get("id")
        if not work_id:
            continue

        year = data.get("publication_year")
        # Fallback: year from date
        if not year:
            pub_date = data.get("publication_date") or ""
            if len(pub_date) >= 4:
                year = pub_date[:4]

        authorships = data.get("authorships") or []
        last_names = []
        for a in authorships:
            author = a.get("author") or {}
            name = author.get("display_name") or ""
            if not name:
                continue
            # Use last token as last name
            parts = name.strip().split()
            if parts:
                last_names.append(parts[-1])

        label_core = ""
        if len(last_names) == 0:
            label_core = "Unknown"
        elif len(last_names) == 1:
            label_core = last_names[0]
        elif len(last_names) == 2:
            label_core = f"{last_names[0]} & {last_names[1]}"
        else:
            label_core = f"{last_names[0]} et al."

        if year:
            label = f"{label_core} {year}"
        else:
            label = label_core

        labels[str(work_id)] = label

    print(f"Built short labels for {len(labels)} works.")
    return labels


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_graph_interactive_edge_roles.py <collection_name>")
        sys.exit(1)

    collection = sys.argv[1]

    collection_dir = DATA_DIR / collection
    processed_dir = collection_dir / "processed"
    raw_oa_dir = collection_dir / "raw" / "openalex"

    graph_path = processed_dir / "citation_graph_openalex_with_scite.graphml"
    edge_roles_path = processed_dir / "edge_roles_llm.csv"
    out_html = processed_dir / "citation_graph_edge_roles.html"

    if not graph_path.exists():
        raise FileNotFoundError(f"Missing graph file: {graph_path}")
    if not edge_roles_path.exists():
        raise FileNotFoundError(f"Missing edge roles file: {edge_roles_path}")
    if not raw_oa_dir.exists():
        raise FileNotFoundError(f"Missing OpenAlex dir: {raw_oa_dir}")

    print(f"Loading graph from {graph_path} ...")
    G = nx.read_graphml(graph_path)

    print(f"Loading edge roles from {edge_roles_path} ...")
    roles_df = pd.read_csv(edge_roles_path)

    citing_col = "citing_id"
    cited_col = "cited_id"
    role_col = "role"

    # Build (citing, cited) -> role lookup
    role_lookup = {
        (str(row[citing_col]), str(row[cited_col])): str(row[role_col])
        for _, row in roles_df.iterrows()
        if pd.notna(row[role_col])
    }

    print(f"Loaded roles for {len(role_lookup)} edges.")

    # Build author-year labels
    short_labels = build_short_label_lookup(raw_oa_dir)

    # Initialize PyVis network
    net = Network(
        height="800px",
        width="100%",
        directed=True,
        notebook=False,
    )

    # Tighter, nicer layout: smaller gaps, readable labels
    net.set_options("""
    {
      "nodes": {
        "shape": "dot",
        "size": 12,
        "font": {
          "size": 16,
          "face": "arial",
          "strokeWidth": 1,
          "strokeColor": "#ffffff"
        }
      },
      "edges": {
        "smooth": {
          "type": "dynamic"
        }
      },
      "physics": {
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -20,
          "centralGravity": 0.015,
          "springLength": 80,
          "springConstant": 0.08,
          "avoidOverlap": 0.5
        },
        "maxVelocity": 50,
        "minVelocity": 0.1,
        "stabilization": {
          "iterations": 500,
          "updateInterval": 50
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 150
      }
    }
    """)

    # Add nodes with hover info
    for node, data in G.nodes(data=True):
        node_id = str(node)
        title = data.get("title", "") or ""
        year = data.get("year", "") or ""
        doi = data.get("doi", "") or ""

        supporting = data.get("scite_supporting", 0)
        contradicting = data.get("scite_contradicting", 0)
        mentioning = data.get("scite_mentioning", 0)

        # Label: "Bordia & Bowman 2019" if we have it, else fallback to short title
        label = short_labels.get(node_id)
        if not label:
            label = title if len(title) <= 60 else title[:57] + "..."

        tooltip = (
            f"<b>{title}</b><br>"
            f"Label: {label}<br>"
            f"Year: {year}<br>"
            f"DOI: {doi}<br>"
            f"Supporting: {supporting}, "
            f"Contradicting: {contradicting}, "
            f"Mentioning: {mentioning}"
        )

        net.add_node(
            n_id=node_id,
            label=label,
            title=tooltip,
        )

    # Add edges *only if* we have an LLM role for them
    edges_with_role = 0
    for u, v in G.edges():
        key = (str(u), str(v))
        role = role_lookup.get(key)
        if role is None:
            continue

        color = map_role_to_color(role)
        edges_with_role += 1

        net.add_edge(
            str(u),
            str(v),
            color=color,
            title=role,   # SUPPORT / DISPUTE / BACKGROUND / METHOD on hover
            arrows="to",
        )

    print(f"Edges with an LLM role (drawn): {edges_with_role}")

    print(f"Writing interactive graph to {out_html} ...")
    net.write_html(str(out_html), open_browser=False)
    print(out_html)


if __name__ == "__main__":
    sys.exit(main())
