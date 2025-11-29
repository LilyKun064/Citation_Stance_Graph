#!/usr/bin/env python
"""
Step 6: Merge scite tallies into your papers table.

Inputs:
    data/processed/papers.csv
    data/processed/scite_tallies.csv

Output:
    data/processed/papers_with_scite.csv

Result:
    Same rows as papers.csv, but with extra columns:
        - scite_supporting
        - scite_contradicting
        - scite_mentioning
        - scite_unclassified
        - scite_total
        - scite_citingPublications
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PAPERS_CSV = PROCESSED_DIR / "papers.csv"
SCITE_CSV = PROCESSED_DIR / "scite_tallies.csv"
OUT_CSV = PROCESSED_DIR / "papers_with_scite.csv"


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
    if not PAPERS_CSV.exists():
        raise FileNotFoundError(f"Missing {PAPERS_CSV}")
    if not SCITE_CSV.exists():
        raise FileNotFoundError(f"Missing {SCITE_CSV}")

    papers = pd.read_csv(PAPERS_CSV)
    scite = pd.read_csv(SCITE_CSV)

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

    # Drop helper doi_norm if you don't want it
    merged.drop(columns=["doi_norm"], inplace=True)

    merged.to_csv(OUT_CSV, index=False)

    print(f"Wrote {OUT_CSV} with {len(merged)} papers.")
    print("Columns now include scite_* tallies.")


if __name__ == "__main__":
    main()
