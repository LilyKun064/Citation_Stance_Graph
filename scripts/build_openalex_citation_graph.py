#!/usr/bin/env python
"""
Step 3: Build node + raw edge tables from OpenAlex JSON.

Inputs:
    data/raw/openalex/*.json   (one work JSON per DOI)

Outputs:
    data/processed/papers.csv
        - openalex_id
        - doi
        - title
        - year
        - in_collection  (True for all, since they come from your Zotero collection)

    data/processed/citation_edges_raw.csv
        - citing_openalex_id
        - cited_openalex_id
"""

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_OA_DIR = PROJECT_ROOT / "data" / "raw" / "openalex"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

PAPERS_CSV = PROCESSED_DIR / "papers.csv"
EDGES_RAW_CSV = PROCESSED_DIR / "citation_edges_raw.csv"


def clean_doi(doi: str | None) -> str:
    if not doi:
        return ""
    doi = doi.strip()
    if doi.lower().startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    if doi.lower().startswith("http://doi.org/"):
        doi = doi[len("http://doi.org/"):]
    return doi.lower()


def main():
    if not RAW_OA_DIR.exists():
        raise FileNotFoundError(f"OpenAlex directory not found: {RAW_OA_DIR}")

    paper_records = []
    edge_records = []

    json_files = sorted(RAW_OA_DIR.glob("*.json"))
    print(f"Found {len(json_files)} OpenAlex JSON files in {RAW_OA_DIR}")

    for path in json_files:
        text = path.read_text(encoding="utf-8")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"!! Skipping {path.name}: JSON error: {e}")
            continue

        # Some sanity checks
        work_id = data.get("id")
        if not work_id:
            print(f"!! Skipping {path.name}: no 'id' field")
            continue

        doi = clean_doi(data.get("doi"))
        title = data.get("title") or ""
        year = data.get("publication_year")

        # Fallback: sometimes only publication_date exists
        if not year:
            pub_date = data.get("publication_date") or ""
            year = pub_date[:4] if len(pub_date) >= 4 else None

        paper_records.append({
            "openalex_id": work_id,
            "doi": doi,
            "title": title,
            "year": year,
            "in_collection": True,  # all came from your Zotero collection
        })

        # referenced_works is a list of OpenAlex IDs that this paper cites
        refs = data.get("referenced_works") or []
        for ref_id in refs:
            if not ref_id:
                continue
            edge_records.append({
                "citing_openalex_id": work_id,
                "cited_openalex_id": ref_id,
            })

    # Build DataFrames
    papers_df = pd.DataFrame(paper_records).drop_duplicates(subset=["openalex_id"])
    edges_df = pd.DataFrame(edge_records).drop_duplicates()

    # Save
    papers_df.to_csv(PAPERS_CSV, index=False)
    edges_df.to_csv(EDGES_RAW_CSV, index=False)

    print(f"Wrote {PAPERS_CSV} with {len(papers_df)} rows.")
    print(f"Wrote {EDGES_RAW_CSV} with {len(edges_df)} rows.")


if __name__ == "__main__":
    main()
