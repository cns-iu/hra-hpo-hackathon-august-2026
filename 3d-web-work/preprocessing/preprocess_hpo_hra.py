#!/usr/bin/env python3
"""Preprocess the HPO-HRA digital-object mapping CSV into JSON for the 3D viewer.

Reads hpo-uberon-terms/data/hpo-hra-relevant-dos.csv (HPO term -> cell type ->
Human Reference Atlas digital object) and writes:

  - public/data/hpo_hra_terms.json   flat list of cleaned records
  - public/data/hpo_hra_by_do.json   records grouped by digital_object

Usage:
    python preprocess_hpo_hra.py
    python preprocess_hpo_hra.py --input path/to.csv --output-dir path/to/dir
"""

import argparse
import json
from pprint import pprint
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "hpo-uberon-terms" / "data" / "hpo-hra-relevant-dos.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "3d-web-work" / "public" / "data"


def iri_to_curie(iri: str) -> str:
    """Convert an OBO purl IRI (e.g. .../HP_0410157) to a CURIE (HP:0410157)."""
    if not isinstance(iri, str) or "/" not in iri:
        return iri
    fragment = iri.rstrip("/").rsplit("/", 1)[-1]
    return fragment.replace("_", ":", 1)

def load_records(input_path: Path) -> pd.DataFrame:
    return pd.read_csv(input_path)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    df = load_records(args.input)
    pprint(df)

if __name__ == "__main__":
    main()
