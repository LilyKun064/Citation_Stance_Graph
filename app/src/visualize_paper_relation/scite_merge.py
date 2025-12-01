# src/visualize_paper_relation/scite_merge.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import pandas as pd


def clean_doi(doi: str | None) -> str:
    """
    Normalize DOIs for joining:
      - handle None / non-str
      - strip whitespace
      - remove https://doi.org/ and http://doi.org/ prefixes
      - lowercase
    """
    if not isinstance(doi, str):
        return ""
    doi = doi.strip()
    lower = doi.lower()
    if lower.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/") :]
        lower = doi.lower()
    if lower.startswith("http://doi.org/"):
        doi = doi[len("http://doi.org/") :]
    return doi.lower()


def merge_scite_into_papers(
    papers_csv: Path,
    scite_csv: Path,
    out_csv: Path,
) -> Dict[str, Any]:
    """
    Merge scite_tallies.csv into papers.csv via normalized DOIs.

    Inputs:
      - papers_csv: processed/papers.csv
      - scite_csv: processed/scite_tallies.csv

    Output:
      - out_csv: processed/papers_with_scite.csv

    Result: same rows as papers.csv with extra columns:
      - scite_supporting
      - scite_contradicting
      - scite_mentioning
      - scite_unclassified
      - scite_total
      - scite_citingPublications
    """
    if not papers_csv.exists():
        raise FileNotFoundError(f"Missing {papers_csv}")
    if not scite_csv.exists():
        raise FileNotFoundError(f"Missing {scite_csv}")

    papers = pd.read_csv(papers_csv)
    scite = pd.read_csv(scite_csv)

    # Normalize DOIs on both sides
    papers["doi_norm"] = papers["doi"].apply(clean_doi)
    scite["doi_norm"] = scite["doi"].apply(clean_doi)

    # Select and rename scite columns
    scite_small = scite[
        [
            "doi_norm",
            "supporting",
            "contradicting",
            "mentioning",
            "unclassified",
            "total",
            "citingPublications",
        ]
    ].copy()

    scite_small.rename(
        columns={
            "supporting": "scite_supporting",
            "contradicting": "scite_contradicting",
            "mentioning": "scite_mentioning",
            "unclassified": "scite_unclassified",
            "total": "scite_total",
            "citingPublications": "scite_citingPublications",
        },
        inplace=True,
    )

    # Left-join: keep all papers, attach scite if available
    merged = papers.merge(scite_small, on="doi_norm", how="left")

    # Replace NaNs in scite columns with 0
    scite_cols = [
        "scite_supporting",
        "scite_contradicting",
        "scite_mentioning",
        "scite_unclassified",
        "scite_total",
        "scite_citingPublications",
    ]
    for col in scite_cols:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0).astype(int)

    # Drop helper column
    merged.drop(columns=["doi_norm"], inplace=True)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_csv, index=False)

    print(f"[scite-merge] Wrote {out_csv} with {len(merged)} papers.")
    print("[scite-merge] Columns now include scite_* tallies.")

    return {
        "papers_with_scite_csv": out_csv,
        "papers_with_scite_df": merged,
    }
