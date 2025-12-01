#!/usr/bin/env python
"""
Step 6: Merge scite tallies into your papers table for a given collection.

Usage:
    python merge_scite_into_papers.py <collection_name>

Inputs:
    data/<collection_name>/processed/papers.csv
    data/<collection_name>/processed/scite_tallies.csv

Output:
    data/<collection_name>/processed/papers_with_scite.csv

Result:
    Same rows as papers.csv, but with extra columns:
        - scite_supporting
        - scite_contradicting
        - scite_mentioning
        - scite_unclassified
        - scite_total
        - scite_citingPublications
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def clean_doi(doi: str | None) -> str:
    if not isinstance(doi, str):
        return ""
    doi = doi.strip()
    if doi.lower().startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    if doi.lower().startswith("http://doi.org/"):
        doi = doi[len("http://doi.org/"):]
    return doi.lower()


def main():
    if len(sys.argv) < 2:
        print("Usage: python merge_scite_into_papers.py <collection_name>")
        sys.exit(1)

    collection = sys.argv[1]

    processed_dir = DATA_DIR / collection / "processed"
    papers_csv = processed_dir / "papers.csv"
    scite_csv = processed_dir / "scite_tallies.csv"
    out_csv = processed_dir / "papers_with_scite.csv"

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
    scite_small = scite[[
        "doi_norm",
        "supporting",
        "contradicting",
        "mentioning",
        "unclassified",
        "total",
        "citingPublications",
    ]].copy()

    scite_small.rename(columns={
        "supporting": "scite_supporting",
        "contradicting": "scite_contradicting",
        "mentioning": "scite_mentioning",
        "unclassified": "scite_unclassified",
        "total": "scite_total",
        "citingPublications": "scite_citingPublications",
    }, inplace=True)

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

    merged.to_csv(out_csv, index=False)

    print(f"Wrote {out_csv} with {len(merged)} papers.")
    print("Columns now include scite_* tallies.")


if __name__ == "__main__":
    main()
