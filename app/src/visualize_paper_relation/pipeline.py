# src/visualize_paper_relation/pipeline.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any

from .zotero import extract_dois_from_zotero_json, write_dois_to_file
from .openalex import fetch_openalex_for_dois
from .graph_data import build_papers_and_edges_from_openalex
from .edge_filter import filter_collection_edges
from .scite_api import fetch_scite_tallies
from .scite_tallies_table import scite_tallies_json_to_csv
from .scite_merge import merge_scite_into_papers
from .graph_build import build_graph_openalex_with_scite
from .llm_edge_roles import classify_edge_roles_for_edges
from .graph_visualization import build_interactive_graph_with_edge_roles


def run_pipeline_step1_extract_dois(
    zotero_json_path: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """
    Step 1:
      - extract DOIs from a Zotero JSON export
      - save them to <output_dir>/doi_list.txt
      - also return the DOI list in-memory
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    dois: List[str] = extract_dois_from_zotero_json(zotero_json_path)
    doi_list_path = output_dir / "doi_list.txt"
    write_dois_to_file(dois, doi_list_path)

    return {
        "dois": dois,
        "doi_list": doi_list_path,
    }


def run_pipeline_step2_fetch_openalex(
    dois: List[str],
    output_dir: Path,
) -> Dict[str, Any]:
    """
    Step 2:
      - fetch OpenAlex metadata for the DOIs
      - save each record as JSON in <output_dir>/openalex_raw
    """
    oa_dir = output_dir / "openalex_raw"
    saved_paths = fetch_openalex_for_dois(dois, oa_dir)

    return {
        "openalex_dir": oa_dir,
        "openalex_files": saved_paths,
    }


def run_pipeline_step3_build_graph_tables(
    openalex_dir: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """
    Step 3:
      - read all OpenAlex JSON files from `openalex_dir`
      - build `papers.csv` and `citation_edges_raw.csv`
      - save them under <output_dir>/processed
    """
    processed_dir = output_dir / "processed"
    result = build_papers_and_edges_from_openalex(openalex_dir, processed_dir)

    # also remember processed_dir for later steps
    result["processed_dir"] = processed_dir
    return result


def run_pipeline_step4_filter_collection_edges(
    processed_dir: Path,
) -> Dict[str, Any]:
    """
    Step 4:
      - take papers.csv and citation_edges_raw.csv in `processed_dir`
      - filter edges so only those from collection papers remain
      - save as citation_edges_collection.csv
    """
    papers_csv = processed_dir / "papers.csv"
    edges_raw_csv = processed_dir / "citation_edges_raw.csv"
    edges_coll_csv = processed_dir / "citation_edges_collection.csv"

    result = filter_collection_edges(papers_csv, edges_raw_csv, edges_coll_csv)
    return result

def run_pipeline_step5A_scite_tallies(
    dois: list[str],
    output_dir: Path,
) -> Dict[str, Any]:
    """
    Step 5A:
      - fetch scite.ai tallies for all DOIs
      - saves as <output_dir>/scite/tallies.json
      - returns the tallies dict
    """
    scite_dir = output_dir / "scite"
    out_json = scite_dir / "tallies.json"

    tallies = fetch_scite_tallies(
        dois=dois,
        out_json_path=out_json,
    )

    return {
        "scite_tallies_json": out_json,
        "scite_tallies": tallies,
    }

def run_pipeline_step5B_scite_tallies_csv(
    tallies_json: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """
    Step 5B:
      - take scite/tallies.json
      - convert to processed/scite_tallies.csv
    """
    processed_dir = output_dir / "processed"
    out_csv = processed_dir / "scite_tallies.csv"

    result = scite_tallies_json_to_csv(tallies_json, out_csv)
    return result

def run_pipeline_step6_merge_scite_into_papers(
    processed_dir: Path,
) -> Dict[str, Any]:
    """
    Step 6:
      - merge processed/papers.csv and processed/scite_tallies.csv
      - save processed/papers_with_scite.csv
    """
    papers_csv = processed_dir / "papers.csv"
    scite_csv = processed_dir / "scite_tallies.csv"
    out_csv = processed_dir / "papers_with_scite.csv"

    result = merge_scite_into_papers(papers_csv, scite_csv, out_csv)
    return result

def run_pipeline_step7_build_graphml(
    processed_dir: Path,
) -> Dict[str, Any]:
    """
    Step 7:
      - build NetworkX graph from:
          processed/papers_with_scite.csv
          processed/citation_edges_collection.csv
      - save as processed/citation_graph_openalex_with_scite.graphml
    """
    papers_with_scite_csv = processed_dir / "papers_with_scite.csv"
    edges_coll_csv = processed_dir / "citation_edges_collection.csv"
    graph_path = processed_dir / "citation_graph_openalex_with_scite.graphml"

    result = build_graph_openalex_with_scite(
        papers_with_scite_csv=papers_with_scite_csv,
        edges_coll_csv=edges_coll_csv,
        graph_path=graph_path,
    )
    return result

def run_pipeline_step8_classify_edge_roles_llm(
    processed_dir: Path,
    openalex_dir: Path,
) -> Dict[str, Any]:
    """
    Step 8:
      - run LLM-based rhetorical role classification
      - uses:
          processed/papers_with_scite.csv
          processed/citation_edges_collection.csv
          openalex_raw/ (for abstracts)
      - outputs:
          processed/edge_roles_llm.csv
    """
    papers_with_scite_csv = processed_dir / "papers_with_scite.csv"
    edges_coll_csv = processed_dir / "citation_edges_collection.csv"
    out_csv = processed_dir / "edge_roles_llm.csv"

    result = classify_edge_roles_for_edges(
        papers_with_scite_csv=papers_with_scite_csv,
        edges_coll_csv=edges_coll_csv,
        raw_oa_dir=openalex_dir,
        out_csv=out_csv,
    )
    return result

def run_pipeline_step9_build_interactive_html(
    processed_dir: Path,
    openalex_dir: Path,
) -> Dict[str, Any]:
    """
    Step 9:
      - build interactive HTML graph with per-edge LLM roles
      - uses:
          processed/citation_graph_openalex_with_scite.graphml
          processed/edge_roles_llm.csv
          openalex_raw/ (for author-year labels)
      - outputs:
          processed/citation_graph_edge_roles.html
    """
    graphml_path = processed_dir / "citation_graph_openalex_with_scite.graphml"
    edge_roles_csv = processed_dir / "edge_roles_llm.csv"
    out_html_path = processed_dir / "citation_graph_edge_roles.html"

    result = build_interactive_graph_with_edge_roles(
        graphml_path=graphml_path,
        edge_roles_csv=edge_roles_csv,
        raw_oa_dir=openalex_dir,
        out_html_path=out_html_path,
    )

    # Convenience alias for the app
    result["graph_html"] = result["graph_html_path"]
    return result


def run_pipeline(
    zotero_json_path: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """
    High-level pipeline entry point used by the CLI and the Streamlit app.

    Steps:
      1) Extract DOIs from Zotero JSON
      2) Fetch OpenAlex metadata
      3) Build node/edge tables
      4) Filter edges to collection
      5A) Fetch scite tallies (JSON)
      5B) Convert scite tallies to CSV
      6) Merge scite tallies into papers
      7) Build NetworkX graph (GraphML)
      8) Run LLM edge role classification
      9) Build interactive HTML graph with edge roles
    """
    outputs: Dict[str, Any] = {}

    # --- Step 1 ---
    step1 = run_pipeline_step1_extract_dois(zotero_json_path, output_dir)
    outputs.update(step1)
    dois: list[str] = step1["dois"]

    # --- Step 2 ---
    step2 = run_pipeline_step2_fetch_openalex(dois, output_dir)
    outputs.update(step2)
    openalex_dir: Path = step2["openalex_dir"]

    # --- Step 3 ---
    step3 = run_pipeline_step3_build_graph_tables(openalex_dir, output_dir)
    outputs.update(step3)
    processed_dir: Path = step3["processed_dir"]

    # --- Step 4 ---
    step4 = run_pipeline_step4_filter_collection_edges(processed_dir)
    outputs.update(step4)

    # --- Step 5A ---
    step5a = run_pipeline_step5A_scite_tallies(dois, output_dir)
    outputs.update(step5a)
    tallies_json: Path = step5a["scite_tallies_json"]

    # --- Step 5B ---
    step5b = run_pipeline_step5B_scite_tallies_csv(tallies_json, output_dir)
    outputs.update(step5b)

    # --- Step 6 ---
    step6 = run_pipeline_step6_merge_scite_into_papers(processed_dir)
    outputs.update(step6)

    # --- Step 7 ---
    step7 = run_pipeline_step7_build_graphml(processed_dir)
    outputs.update(step7)

    # --- Step 8 ---
    step8 = run_pipeline_step8_classify_edge_roles_llm(processed_dir, openalex_dir)
    outputs.update(step8)

    # --- Step 9: interactive HTML with LLM roles ---
    step9 = run_pipeline_step9_build_interactive_html(processed_dir, openalex_dir)
    outputs.update(step9)

    return outputs
