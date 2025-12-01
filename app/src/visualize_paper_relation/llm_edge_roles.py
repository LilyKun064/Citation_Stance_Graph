# src/visualize_paper_relation/llm_edge_roles.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables (OPENAI_API_KEY etc.)
load_dotenv()

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """
    Lazy-init OpenAI client using OPENAI_API_KEY from environment.
    """
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


# ---------------------------------------------------------------------
# Helpers: abstracts from OpenAlex
# ---------------------------------------------------------------------


def reconstruct_abstract(inv) -> str:
    """
    Reconstruct abstract text from OpenAlex abstract_inverted_index.

    inv: dict like {word: [pos1, pos2, ...], ...}

    Returns a single string abstract.
    """
    if not isinstance(inv, dict):
        return ""

    word_positions = []
    for word, positions in inv.items():
        if not positions:
            continue
        first_pos = min(positions)
        word_positions.append((first_pos, word))

    word_positions.sort(key=lambda x: x[0])
    words = [w for _, w in word_positions]
    return " ".join(words)


def load_openalex_abstracts(raw_oa_dir: Path) -> Dict[str, str]:
    """
    Scan raw_oa_dir/*.json and build:
        openalex_id -> abstract_text
    """
    abstracts: Dict[str, str] = {}

    json_files = sorted(raw_oa_dir.glob("*.json"))
    print(f"[LLM-roles] Loading abstracts from {len(json_files)} OpenAlex JSON files in {raw_oa_dir} ...")

    for path in json_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  !! Skipping {path.name}: JSON decode error")
            continue

        work_id = data.get("id")
        if not work_id:
            continue

        if "abstract_inverted_index" in data and data["abstract_inverted_index"]:
            abstract_raw = reconstruct_abstract(data["abstract_inverted_index"])
        else:
            # Some works may have a plain 'abstract' field
            abstract_raw = data.get("abstract", "") or ""

        abstracts[str(work_id)] = abstract_raw

    print(f"[LLM-roles] Built abstract lookup for {len(abstracts)} works.")
    return abstracts


# ---------------------------------------------------------------------
# Helper: LLM classifier using title + abstract
# ---------------------------------------------------------------------


def classify_edge_role(
    citing_title: str,
    citing_abs: str,
    cited_title: str,
    cited_abs: str,
    model: str = "gpt-4.1-mini",
) -> Dict[str, Any]:
    """
    Use OpenAI to classify the rhetorical role between A (citing) and B (cited),
    based on BOTH titles and abstracts.

    Returns:
        {
          "role": "SUPPORT"|"DISPUTE"|"BACKGROUND"|"METHOD",
          "confidence": float,
          "reason": str
        }
    """
    system_msg = (
        "You are an expert assistant that classifies the rhetorical relationship "
        "between two academic papers. Paper A cites Paper B.\n\n"
        "You are given the titles and abstracts of both papers. "
        "Infer how A most likely uses B in its argument.\n\n"
        "Allowed roles:\n"
        "- SUPPORT: A agrees with, confirms, extends, or relies positively on B's findings.\n"
        "- DISPUTE: A disagrees with, challenges, contradicts, or shows opposing results to B.\n"
        "- BACKGROUND: A mainly cites B as background, context, a general reference, "
        "  or neutral mention without clear support or dispute.\n"
        "- METHOD: A mainly uses, adapts, or evaluates methods from B, independent of "
        "  whether it supports or disputes B's substantive claims.\n\n"
        "If you cannot clearly infer support or dispute from A's abstract, prefer "
        "BACKGROUND or METHOD.\n\n"
        "Return a JSON object with fields:\n"
        "{\n"
        '  \"role\": \"SUPPORT\" | \"DISPUTE\" | \"BACKGROUND\" | \"METHOD\",\n'
        "  \"confidence\": number between 0 and 1,\n"
        "  \"reason\": short explanation (1-3 sentences)\n"
        "}\n"
    )

    user_msg = (
        "Classify the relationship between these two papers.\n\n"
        "Paper A (citing):\n"
        f"TITLE: {citing_title}\n"
        f"ABSTRACT: {citing_abs}\n\n"
        "Paper B (cited):\n"
        f"TITLE: {cited_title}\n"
        f"ABSTRACT: {cited_abs}\n"
    )

    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {
            "role": "BACKGROUND",
            "confidence": 0.3,
            "reason": f"Could not parse JSON from model: {content!r}",
        }

    role = str(data.get("role", "BACKGROUND")).upper().strip()
    if role not in {"SUPPORT", "DISPUTE", "BACKGROUND", "METHOD"}:
        role = "BACKGROUND"

    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5

    reason = str(data.get("reason", "")).strip()

    return {
        "role": role,
        "confidence": confidence,
        "reason": reason,
    }


# ---------------------------------------------------------------------
# High-level driver for pipeline
# ---------------------------------------------------------------------


def classify_edge_roles_for_edges(
    papers_with_scite_csv: Path,
    edges_coll_csv: Path,
    raw_oa_dir: Path,
    out_csv: Path,
    model: str = "gpt-4.1-mini",
) -> Dict[str, Any]:
    """
    Run LLM role classification for each citation edge where both
    citing and cited papers are in the collection and have titles.

    Inputs:
      - papers_with_scite_csv
      - edges_coll_csv
      - raw_oa_dir: directory with raw OpenAlex JSON (for abstracts)

    Output:
      - out_csv: edge_roles_llm.csv

    Each row in the output:
      - citing_id
      - cited_id
      - role
      - confidence
      - reason
    """
    if not papers_with_scite_csv.exists():
        raise FileNotFoundError(f"Missing {papers_with_scite_csv}")
    if not edges_coll_csv.exists():
        raise FileNotFoundError(f"Missing {edges_coll_csv}")
    if not raw_oa_dir.exists():
        raise FileNotFoundError(f"Missing OpenAlex dir {raw_oa_dir}")

    print(f"[LLM-roles] Loading papers from {papers_with_scite_csv} ...")
    papers = pd.read_csv(papers_with_scite_csv)

    print(f"[LLM-roles] Loading edges from {edges_coll_csv} ...")
    edges = pd.read_csv(edges_coll_csv)

    # Lookup: OpenAlex ID -> title
    title_lookup = dict(
        zip(
            papers["openalex_id"].astype(str),
            papers["title"].fillna("").astype(str),
        )
    )

    # Lookup: OpenAlex ID -> abstract
    abstract_lookup = load_openalex_abstracts(raw_oa_dir)

    records: List[Dict[str, Any]] = []

    for idx, row in edges.iterrows():
        citing_id = str(row["citing_openalex_id"])
        cited_id = str(row["cited_openalex_id"])

        citing_title = title_lookup.get(citing_id, "")
        cited_title = title_lookup.get(cited_id, "")

        # Only classify edges where both A and B are in our collection and have titles
        if not citing_title or not cited_title:
            continue

        citing_abs = abstract_lookup.get(citing_id, "")
        cited_abs = abstract_lookup.get(cited_id, "")

        print(f"[LLM-roles] [{idx+1}/{len(edges)}] {citing_id} -> {cited_id}")
        print(f"  A: {citing_title}")
        print(f"  B: {cited_title}")

        result = classify_edge_role(
            citing_title=citing_title,
            citing_abs=citing_abs,
            cited_title=cited_title,
            cited_abs=cited_abs,
            model=model,
        )

        records.append(
            {
                "citing_id": citing_id,
                "cited_id": cited_id,
                "role": result["role"],
                "confidence": result["confidence"],
                "reason": result["reason"],
            }
        )

    out_df = pd.DataFrame(records)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)

    print(f"[LLM-roles] Wrote {out_csv} with {len(out_df)} classified edges.")

    return {
        "edge_roles_llm_csv": out_csv,
        "edge_roles_llm_df": out_df,
    }
