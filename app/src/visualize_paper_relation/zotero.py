# src/visualize_paper_relation/zotero.py
from __future__ import annotations

from pathlib import Path
import json
from typing import Iterable, List, Dict, Any


def normalize_doi(raw: str | None) -> str | None:
    """
    Normalize a raw DOI string:
      - strip whitespace
      - remove common prefixes (https://doi.org/, doi:, etc.)
      - return lowercase DOI if it looks valid (contains '/')
    """
    if not raw:
        return None

    doi = raw.strip()
    prefixes = (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
        "DOI:",
    )

    lower = doi.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            doi = doi[len(prefix):]
            lower = doi.lower()
            break

    return lower if "/" in doi else None


def _load_items_from_zotero_json(zotero_json_path: Path) -> List[Dict[str, Any]]:
    """
    Load a Zotero JSON export and return a flat list of item dicts,
    regardless of whether the file is a list or a dict with 'items'.
    """
    text = zotero_json_path.read_text(encoding="utf-8")
    data = json.loads(text)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Some exports use {"items": [...]} structure
        if isinstance(data.get("items"), list):
            return data["items"]
        # Fallback: treat the dict itself as a single item
        return [data]

    raise TypeError(f"Unexpected JSON structure in {zotero_json_path}")


def extract_dois_from_zotero_json(zotero_json_path: Path) -> list[str]:
    """
    High-level helper:
      - loads the Zotero JSON
      - extracts DOIs from either item['data']['DOI'] or item['DOI']
      - normalizes them
      - returns a sorted list of unique DOIs
    """
    items = _load_items_from_zotero_json(zotero_json_path)

    dois: list[str] = []
    for it in items:
        # Some Zotero exports nest metadata under "data"
        inner = it.get("data") if isinstance(it.get("data"), dict) else it
        raw = inner.get("DOI") or inner.get("doi")
        doi = normalize_doi(raw)
        if doi:
            dois.append(doi)

    # Deduplicate + sort for stable output
    unique_sorted = sorted(set(dois))
    return unique_sorted


def write_dois_to_file(dois: Iterable[str], out_path: Path) -> None:
    """
    Save DOIs to a simple text file, one DOI per line.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(dois), encoding="utf-8")
