# src/visualize_paper_relation/graph_visualization.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import networkx as nx
from pyvis.network import Network


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


def build_short_label_lookup(raw_oa_dir: Path) -> Dict[str, str]:
    """
    Scan raw_oa_dir/*.json and build:
        openalex_id -> "Author 2019" or "Author1 & Author2 2019" etc.
    """
    labels: Dict[str, str] = {}

    json_files = sorted(raw_oa_dir.glob("*.json"))
    print(
        f"[vis] Loading author info from {len(json_files)} OpenAlex JSON files in {raw_oa_dir} ..."
    )

    for path in json_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  !! [vis] Skipping {path.name}: JSON decode error")
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

    print(f"[vis] Built short labels for {len(labels)} works.")
    return labels


# ---------------------------------------------------------------------
# Main builder: from graphml + edge roles -> HTML
# ---------------------------------------------------------------------


def build_interactive_graph_with_edge_roles(
    graphml_path: Path,
    edge_roles_csv: Path,
    raw_oa_dir: Path,
    out_html_path: Path,
) -> Dict[str, Any]:
    """
    Build an interactive PyVis HTML graph using:

      - citation_graph_openalex_with_scite.graphml
      - edge_roles_llm.csv
      - raw OpenAlex JSON (for author-year labels)

    Semantics:
      - Nodes: papers in the collection
      - Edge A -> B: A cites B
      - Edge colors:
          SUPPORT -> green
          DISPUTE -> red
          else    -> gray

    Physics is DISABLED so the graph is steady.
    """
    if not graphml_path.exists():
        raise FileNotFoundError(f"Missing graph file: {graphml_path}")
    if not edge_roles_csv.exists():
        raise FileNotFoundError(f"Missing edge roles file: {edge_roles_csv}")
    if not raw_oa_dir.exists():
        raise FileNotFoundError(f"Missing OpenAlex dir: {raw_oa_dir}")

    print(f"[vis] Loading graph from {graphml_path} ...")
    G = nx.read_graphml(graphml_path)

    print(f"[vis] Loading edge roles from {edge_roles_csv} ...")
    roles_df = pd.read_csv(edge_roles_csv)

    citing_col = "citing_id"
    cited_col = "cited_id"
    role_col = "role"

    # Build (citing, cited) -> role lookup
    role_lookup = {
        (str(row[citing_col]), str(row[cited_col])): str(row[role_col])
        for _, row in roles_df.iterrows()
        if pd.notna(row[role_col])
    }

    print(f"[vis] Loaded roles for {len(role_lookup)} edges.")

    # Build author-year labels
    short_labels = build_short_label_lookup(raw_oa_dir)

    # Initialize PyVis network
    net = Network(
        height="800px",
        width="100%",
        directed=True,
        notebook=False,
    )

    # Physics disabled: steady graph, no endless spinning
    net.set_options(
        """
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
        "enabled": false,
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
    """
    )

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
            title=role,  # SUPPORT / DISPUTE / BACKGROUND / METHOD on hover
            arrows="to",
        )

    print(f"[vis] Edges with an LLM role (drawn): {edges_with_role}")

    print(f"[vis] Writing interactive graph to {out_html_path} ...")
    out_html_path.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(out_html_path), open_browser=False)
    print(f"[vis] Saved HTML: {out_html_path}")

    return {
        "graph_html_path": out_html_path,
    }
