#!/usr/bin/env python
"""
Step 3: Build paper + citation edge tables from OpenAlex JSON.

Usage:
    python build_nodes_and_edges.py <collection_name>
"""

import sys
import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def clean_doi(doi):
    if not doi:
        return ""
    doi = doi.lower().strip()
    for prefix in ("https://doi.org/", "http://doi.org/"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_nodes_and_edges.py <collection_name>")
        sys.exit(1)

    collection = sys.argv[1]

    root = DATA_DIR / collection
    oa_dir = root / "raw" / "openalex"
    processed_dir = root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    papers_csv = processed_dir / "papers.csv"
    edges_csv = processed_dir / "citation_edges_raw.csv"

    files = sorted(oa_dir.glob("*.json"))
    print(f"Found {len(files)} OpenAlex files.")

    papers = []
    edges = []

    for f in files:
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue

        work_id = data.get("id")
        if not work_id:
            continue

        doi = clean_doi(data.get("doi"))
        title = data.get("title", "")
        year = data.get("publication_year") or None

        papers.append({
            "openalex_id": work_id,
            "doi": doi,
            "title": title,
            "year": year,
            "in_collection": True,
        })

        for ref in data.get("referenced_works", []):
            edges.append({
                "citing_openalex_id": work_id,
                "cited_openalex_id": ref,
            })

    pd.DataFrame(papers).drop_duplicates().to_csv(papers_csv, index=False)
    pd.DataFrame(edges).drop_duplicates().to_csv(edges_csv, index=False)

    print(f"Wrote {papers_csv}")
    print(f"Wrote {edges_csv}")


if __name__ == "__main__":
    main()
