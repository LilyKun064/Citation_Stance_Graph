# src/visualize_paper_relation/openalex.py
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional

import requests

# Use an environment variable for polite OpenAlex usage
# Example: set OPENALEX_MAILTO="you@example.com"
MAILTO = os.environ.get("OPENALEX_MAILTO", "")


def doi_to_filename(doi: str) -> str:
    """
    Turn a DOI into a filesystem-friendly filename.
    """
    return doi.replace("/", "_").replace(":", "_")


def fetch_openalex_work(
    doi: str,
    mailto: Optional[str] = None,
    timeout: int = 20,
) -> Optional[Dict[str, Any]]:
    """
    Fetch a single OpenAlex work record for a DOI.
    Returns the JSON dict, or None if not found / error.
    """
    base_url = "https://api.openalex.org/works/https://doi.org/"
    url = f"{base_url}{doi}"
    params: Dict[str, str] = {}

    use_mailto = mailto or MAILTO
    if use_mailto:
        params["mailto"] = use_mailto

    try:
        r = requests.get(url, params=params, timeout=timeout)
        if r.status_code == 404:
            print(f"[OpenAlex] 404 for {doi}, skipping")
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[OpenAlex] ERROR fetching {doi}: {e}")
        return None


def fetch_openalex_for_dois(
    dois: Iterable[str],
    out_dir: Path,
    sleep_s: float = 0.5,
    mailto: Optional[str] = None,
) -> List[Path]:
    """
    Fetch OpenAlex metadata for a list of DOIs and save each record as a JSON file.

    - dois: an iterable of DOI strings
    - out_dir: directory where per-DOI JSON files will be saved
    - sleep_s: delay between requests to be nice to the API
    - mailto: optional email to pass to OpenAlex (overrides env var)

    Returns a list of saved file paths.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: List[Path] = []

    for doi in dois:
        out_path = out_dir / f"{doi_to_filename(doi)}.json"
        if out_path.exists():
            print(f"[OpenAlex] [skip] {doi}")
            continue

        data = fetch_openalex_work(doi, mailto=mailto)
        if data:
            out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            saved_paths.append(out_path)
            print(f"[OpenAlex] Saved {out_path}")

        if sleep_s > 0:
            time.sleep(sleep_s)

    return saved_paths
