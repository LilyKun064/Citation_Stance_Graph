from __future__ import annotations

import json
import os
from typing import Dict, Any

from openai import OpenAI
from dotenv import load_dotenv  # make sure python-dotenv is installed

EDGE_ROLE_CATEGORIES = ["BACKGROUND", "SUPPORT", "DISPUTE", "METHOD"]


def get_openai_client() -> OpenAI:
    """
    Create an OpenAI client, loading OPENAI_API_KEY from .env or environment.

    Expected:
        .env at your project root, containing:
            OPENAI_API_KEY=sk-xxxx
    """
    # Load .env from current working dir (when run from project root)
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment / .env")
    return OpenAI(api_key=api_key)


def classify_edge_role(
    citing_title: str,
    cited_title: str,
    citing_year: int | None = None,
    cited_year: int | None = None,
    model: str = "gpt-4.1-mini",
) -> Dict[str, Any]:
    """
    Heuristic edge-level role based on relationship between two papers.
    Uses ONLY titles and (optionally) years, no PDFs.

    Returns: dict with keys: role, confidence, reason.
    """

    client = get_openai_client()

    year_info = ""
    if citing_year is not None or cited_year is not None:
        year_info = f"Citing paper year: {citing_year}, cited paper year: {cited_year}."

    prompt = f"""
You are analyzing how one scientific paper is likely to use another paper in its references.

CITING paper title:
"{citing_title}"

CITED paper title:
"{cited_title}"

{year_info}

Based ONLY on these titles, infer the *most likely* rhetorical role of the citation from the CITING paper to the CITED paper.

Choose exactly one of:

- BACKGROUND: Cited as prior work / motivation / context / related work.
- SUPPORT: Cited as key evidence that directly supports the citing paper's main claims (e.g., empirical results the citing paper builds on).
- DISPUTE: Cited mainly to criticize, challenge, or show limitations of the cited paper.
- METHOD: Cited mainly for methodology, datasets, benchmarks, or tools used in the citing paper.

You are guessing, but be as reasonable as possible.

Respond ONLY in JSON with keys:
- "role": one of {EDGE_ROLE_CATEGORIES}
- "confidence": a number between 0 and 1
- "reason": a short explanation (1–2 sentences).
    """.strip()

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You infer citation roles between pairs of papers."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content

    try:
        data = json.loads(content)
    except Exception:
        data = {"raw": content}

    return data
