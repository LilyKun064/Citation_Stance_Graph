# src/visualize_paper_relation/cli.py
from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visualize Paper Relation – Step 1: extract DOIs from a Zotero JSON export."
    )

    parser.add_argument(
        "--zotero-json",
        "-i",
        required=True,
        help="Path to the Zotero JSON export file (any folder, any name).",
    )

    parser.add_argument(
        "--out-dir",
        "-o",
        default="output",
        help="Output directory for results (default: ./output).",
    )

    args = parser.parse_args()

    zotero_path = Path(args.zotero_json).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    if not zotero_path.exists():
        raise SystemExit(f"Error: Zotero JSON file does not exist:\n  {zotero_path}")

    print(f"Using Zotero JSON: {zotero_path}")
    print(f"Output directory: {out_dir}")

    results = run_pipeline(zotero_path, out_dir)

    print("\nStep 1 completed:")
    for name, path in results.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
