import json
import time
from pathlib import Path
from typing import Dict, Any

import requests


BASE_URL = "https://api.openalex.org/works"


def _sanitize_filename(s: str) -> str:
    """Turn a DOI or OpenAlex ID into a safe filename."""
    return (
        s.replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
        .replace(":", "_")
    )


def fetch_openalex_work_for_doi(
    doi: str,
    raw_dir: Path,
    mailto: str,
    sleep_seconds: float = 0.2,
) -> Dict[str, Any]:
    """
    Fetch OpenAlex 'work' JSON for a given DOI.
    Cache the raw JSON under raw_dir so we don't refetch unnecessarily.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Use DOI to build a cache filename
    cache_name = _sanitize_filename(doi) + ".json"
    cache_path = raw_dir / cache_name

    # If we already have it cached, load and return
    if cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Otherwise, call OpenAlex
    params = {}
    if mailto:
        params["mailto"] = mailto

    # OpenAlex pattern: /works/https://doi.org/{doi}
    url = f"{BASE_URL}/https://doi.org/{doi}"
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # Cache it
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Be polite to the API
    time.sleep(sleep_seconds)

    return data
