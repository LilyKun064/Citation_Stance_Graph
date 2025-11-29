import json
from pathlib import Path
from typing import List, Dict, Any


def load_zotero_json(path: str | Path) -> List[Dict[str, Any]]:
    """Load a Zotero collection exported as JSON."""
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Unrecognized Zotero JSON structure")


def extract_dois(items: List[Dict[str, Any]]) -> List[str]:
    """Extract DOIs from Zotero JSON items."""
    dois = []
    for it in items:
        doi = it.get("DOI") or it.get("doi")
        if doi:
            doi_clean = (
                doi.strip()
                .replace("https://doi.org/", "")
                .replace("http://doi.org/", "")
                .lower()
            )
            dois.append(doi_clean)
    seen = set()
    unique = []
    for d in dois:
        if d not in seen:
            seen.add(d)
            unique.append(d)
    return unique
