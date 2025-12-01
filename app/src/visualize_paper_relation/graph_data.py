# src/visualize_paper_relation/graph_data.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

import json
import pandas as pd


def clean_doi(doi: str | None) -> str:
    """
    Normalize DOI format:
      - lowercase
      - strip whitespace
      - remove https?://doi.org/ prefix if present
    Return empty string if missing.
    """
    if not doi:
        return ""

    doi = doi.lower().strip()
    for prefix in ("https://doi.org/", "http://doi.org/"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi


def build_papers_and_edges_from_openalex(
    openalex_dir: Path,
    processed_dir: Path,
) -> Dict[str, Any]:
    """
    Given a directory of per-paper OpenAlex JSON files, build:

      - papers.csv
      - citation_edges_raw.csv

    and save them under `processed_dir`.

    Returns a dict with:
      {
        "papers_csv": Path,
        "edges_csv": Path,
        "papers_df": DataFrame,
        "edges_df": DataFrame,
      }
    """
    processed_dir.mkdir(parents=True, exist_ok=True)

    papers_csv = processed_dir / "papers.csv"
    edges_csv = processed_dir / "citation_edges_raw.csv"

    files = sorted(openalex_dir.glob("*.json"))
    print(f"[GraphData] Found {len(files)} OpenAlex files in {openalex_dir}")

    papers: List[dict] = []
    edges: List[dict] = []

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[GraphData] Skipping {f} (JSON error: {e})")
            continue

        work_id = data.get("id")
        if not work_id:
            continue

        doi = clean_doi(data.get("doi"))
        title = data.get("title", "") or ""
        year = data.get("publication_year") or None

        papers.append(
            {
                "openalex_id": work_id,
                "doi": doi,
                "title": title,
                "year": year,
                "in_collection": True,
            }
        )

        for ref in data.get("referenced_works", []) or []:
            edges.append(
                {
                    "citing_openalex_id": work_id,
                    "cited_openalex_id": ref,
                }
            )

    papers_df = pd.DataFrame(papers).drop_duplicates()
    edges_df = pd.DataFrame(edges).drop_duplicates()

    papers_df.to_csv(papers_csv, index=False)
    edges_df.to_csv(edges_csv, index=False)

    print(f"[GraphData] Wrote {papers_csv}")
    print(f"[GraphData] Wrote {edges_csv}")

    return {
        "papers_csv": papers_csv,
        "edges_csv": edges_csv,
        "papers_df": papers_df,
        "edges_df": edges_df,
    }
