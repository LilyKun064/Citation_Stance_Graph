#!/usr/bin/env python
"""
Run the full citation-stance pipeline for a Zotero collection.

Usage (from repo root, inside venv):

    python scripts/run_full_pipeline_from_zotero.py <collection_slug> <zotero_json_path>

- <collection_slug> is something like: LLM_Gender_Bias
- <zotero_json_path> can be ANY .json path (Downloads, temp folder, etc.)

Internally we:
  1. Ensure data/<slug>/raw/zotero/ exists
  2. Copy the JSON there as data/<slug>/raw/zotero/<slug>.json
     (or skip copy if it's already that file)
  3. Run your existing scripts in order
  4. End with data/<slug>/processed/citation_graph_edge_roles.html
"""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    print(">>", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, check=True)


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: run_full_pipeline_from_zotero.py <collection_slug> <zotero_json_path>",
            file=sys.stderr,
        )
        sys.exit(1)

    slug = sys.argv[1]
    zotero_json = Path(sys.argv[2]).resolve()

    # Basic validation of the input path
    if not zotero_json.exists():
        print(f"ERROR: Zotero JSON does not exist: {zotero_json}", file=sys.stderr)
        sys.exit(1)

    if not zotero_json.is_file():
        print(f"ERROR: Expected a .json file, got: {zotero_json}", file=sys.stderr)
        sys.exit(1)

    if zotero_json.suffix.lower() != ".json":
        print(f"ERROR: Expected a .json file, got: {zotero_json}", file=sys.stderr)
        sys.exit(1)

    # Canonical data location for this slug
    data_root = PROJECT_ROOT / "data" / slug
    raw_dir = data_root / "raw" / "zotero"
    raw_dir.mkdir(parents=True, exist_ok=True)

    target = raw_dir / f"{slug}.json"

    # Copy JSON only if source and destination are different
    if zotero_json.resolve() != target.resolve():
        print(f"Copying Zotero JSON from {zotero_json} to {target}")
        shutil.copy2(zotero_json, target)
    else:
        print(f"Zotero JSON already in place at {target}, using it directly")

    scripts = PROJECT_ROOT / "scripts"

    # 1. Extract DOIs from the Zotero JSON
    run([sys.executable, str(scripts / "run_from_zotero_json.py"), slug])

    # 2. Fetch OpenAlex metadata for DOIs
    run([sys.executable, str(scripts / "fetch_openalex_for_dois.py"), slug])

    # 3. Build OpenAlex citation graph
    run([sys.executable, str(scripts / "build_openalex_citation_graph.py"), slug])

    # 4. Filter edges to the collection subgraph
    run([sys.executable, str(scripts / "filter_collection_edges.py"), slug])

    # 5. Fetch Scite tallies
    run([sys.executable, str(scripts / "fetch_scite_tallies.py"), slug])

    # 6. Parse Scite tallies into edge-level data
    run([sys.executable, str(scripts / "parse_scite_tallies.py"), slug])

    # 7. Merge Scite info into paper metadata
    run([sys.executable, str(scripts / "merge_scite_into_papers.py"), slug])

    # 8. Build the NetworkX graph (with attributes)
    run([sys.executable, str(scripts / "build_networkx_graph.py"), slug])

    # 9. Classify collection edges with LLM roles
    run([sys.executable, str(scripts / "classify_collection_edges_llm.py"), slug])

    # 10. Plot interactive graph with edge roles
    run([sys.executable, str(scripts / "plot_graph_interactive_edge_roles.py"), slug])

    out_html = data_root / "processed" / "citation_graph_edge_roles.html"
    print(out_html)


if __name__ == "__main__":
    main()
