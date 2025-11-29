from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


def load_openalex_work_file(path: Path) -> Dict[str, Any]:
    """Load a single OpenAlex work JSON file."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi_clean = (
        doi.strip()
        .replace("https://doi.org/", "")
        .replace("http://doi.org/", "")
        .lower()
    )
    return doi_clean


def collect_papers_and_edges(
    raw_dir: Path,
    doi_list_path: Path,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Read all cached OpenAlex JSON files and build:

    - papers: list of dicts with info about each paper
    - edges: list of dicts with citing -> cited relationships
    """

    # Load the DOIs that came from your Zotero collection
    collection_dois: List[str] = []
    if doi_list_path.exists():
        with doi_list_path.open("r", encoding="utf-8") as f:
            collection_dois = [line.strip().lower() for line in f if line.strip()]
    collection_doi_set = set(collection_dois)

    # First pass: load all works and build a mapping OpenAlex ID -> (doi, ...)
    papers: List[Dict[str, Any]] = []
    openalex_to_doi: Dict[str, str | None] = {}

    for json_path in sorted(raw_dir.glob("*.json")):
        data = load_openalex_work_file(json_path)

        openalex_id = data.get("id")  # e.g. "https://openalex.org/W123..."
        doi_raw = data.get("doi") or data.get("ids", {}).get("doi")
        doi_norm = normalize_doi(doi_raw)
        title = data.get("title") or data.get("display_name")
        year = data.get("publication_year")

        in_collection = doi_norm in collection_doi_set

        papers.append(
            {
                "openalex_id": openalex_id,
                "doi": doi_norm,
                "title": title,
                "year": year,
                "in_collection": in_collection,
            }
        )

        if openalex_id:
            openalex_to_doi[openalex_id] = doi_norm

    # Build a set of OpenAlex IDs that are in the original collection
    collection_openalex_ids = {
        p["openalex_id"] for p in papers if p["in_collection"] and p["openalex_id"]
    }

    # Second pass: build edges
    edges: List[Dict[str, Any]] = []
    for data in (load_openalex_work_file(p) for p in sorted(raw_dir.glob("*.json"))):
        citing_oa_id = data.get("id")
        citing_doi = normalize_doi(data.get("doi") or data.get("ids", {}).get("doi"))
        referenced = data.get("referenced_works") or []

        for cited_oa_id in referenced:
            cited_doi = openalex_to_doi.get(cited_oa_id)
            edge = {
                "citing_openalex_id": citing_oa_id,
                "citing_doi": citing_doi,
                "cited_openalex_id": cited_oa_id,
                "cited_doi": cited_doi,
                "citing_in_collection": citing_oa_id in collection_openalex_ids,
                "cited_in_collection": cited_oa_id in collection_openalex_ids,
            }
            edges.append(edge)

    return papers, edges
