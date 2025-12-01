# src/visualize_paper_relation/scite_api.py
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests

SCITE_KEY = os.environ.get("SCITE_API_KEY")  # optional


def fetch_scite_for_doi(doi: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch scite.ai tallies for a DOI.
    Works with:
      - paid API key
      - free (no key) endpoint (limited data)
    """
    url = f"https://api.scite.ai/tallies/{doi}"
    headers = {"x-api-key": api_key or SCITE_KEY} if (api_key or SCITE_KEY) else {}

    try:
        r = requests.get(url, headers=headers, timeout=20)

        if r.status_code == 404:
            print(f"[scite] No data for DOI {doi}")
            return None

        r.raise_for_status()
        return r.json()

    except Exception as e:
        print(f"[scite] ERROR fetching DOI {doi}: {e}")
        return None


def fetch_scite_tallies(
    dois: list[str],
    out_json_path: Path,
    api_key: Optional[str] = None,
    sleep_s: float = 0.3,
) -> Dict[str, Any]:
    """
    Fetch scite tallies for a list of DOIs.

    Args:
        dois: list of DOI strings
        out_json_path: where to save tallies.json
        api_key: optional scite API key (fallback: environment SCITE_API_KEY)
        sleep_s: delay between requests

    Returns:
        A dict mapping doi -> tallies (or None)
    """
    out_json_path.parent.mkdir(parents=True, exist_ok=True)

    tallies: Dict[str, Any] = {}

    print(f"[scite] Fetching tallies for {len(dois)} DOIs")

    for doi in dois:
        print(f"[scite] {doi}")
        tallies[doi] = fetch_scite_for_doi(doi, api_key=api_key)
        time.sleep(sleep_s)

    # Save to disk
    out_json_path.write_text(
        json.dumps(tallies, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"[scite] Wrote {out_json_path}")

    return tallies
