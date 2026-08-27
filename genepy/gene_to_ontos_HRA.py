# LLM coded untested!!!

import argparse
import math
import requests
import pandas as pd

SPARQL = "https://lod.humanatlas.io/sparql"
API = "https://apps.humanatlas.io/api/grlc/hra-pop/datasets-with-ct"

PREFIX = """
PREFIX ccf: <http://purl.org/ccf/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX HRApop: <https://purl.humanatlas.io/graph/hra-pop>
"""

def sparql(q):
    r = requests.get(
        SPARQL,
        params={"query": q, "format": "json"},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["results"]["bindings"]

def get_cell_types():
    q = PREFIX + """
    SELECT DISTINCT ?cell ?label
    FROM HRApop:
    WHERE {
        ?x ccf:has_cell_summary [
            ccf:has_cell_summary_row [
                ccf:cell_id ?cell
            ]
        ] .
        FILTER(STRSTARTS(STR(?cell),
               "http://purl.obolibrary.org/obo/CL_"))
        ?cell rdfs:label ?label .
    }
    """
    return [
        (x["cell"]["value"], x["label"]["value"])
        for x in sparql(q)
    ]

def get_ct_expression(celltype):
    r = requests.get(
        API,
        params={"celltype": celltype},
        headers={"Accept": "application/json"},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()

def genes_from_file(path):
    with open(path) as f:
        return {
            x.strip().upper()
            for x in f
            if x.strip() and not x.startswith("#")
        }

def main():

    p = argparse.ArgumentParser()
    p.add_argument("genes")
    p.add_argument("-o", "--output",
                   default="hra_gene_locations.csv")
    args = p.parse_args()

    genes = genes_from_file(args.genes)

    print(f"Searching HRApop for {len(genes)} genes...")

    rows = []

    for i, (cl_id, cl_label) in enumerate(get_cell_types(), 1):

        print(f"\rCell types queried: {i}", end="", flush=True)

        try:
            data = get_ct_expression(cl_id)
        except requests.RequestException:
            continue

        # HRA GRLC responses are normally JSON objects containing
        # a list of records. Be permissive about the exact wrapper.
        records = (
            data.get("results")
            or data.get("data")
            or data
        )

        if isinstance(records, dict):
            records = records.get("results", records)

        if not isinstance(records, list):
            continue

        for x in records:

            gene = str(
                x.get("b_label")
                or x.get("gene_label")
                or x.get("B_label")
                or ""
            ).upper()

            if gene not in genes:
                continue

            expression = x.get(
                "mean_expression",
                x.get(
                    "mean_b_expression",
                    x.get("mean_gene_expr_value")
                )
            )

            try:
                expression = float(expression)
            except (TypeError, ValueError):
                continue

            uberon = (
                x.get("organ_id")
                or x.get("organ")
                or x.get("anatomical_structure")
                or ""
            )

            anatomy = (
                x.get("organ_label")
                or x.get("organ_name")
                or x.get("organ")
                or ""
            )

            rows.append({
                "gene": gene,
                "UBERON": uberon,
                "anatomy": anatomy,
                "CL": cl_id.rsplit("/", 1)[-1],
                "cell type": cl_label,
                "mean expression": expression,
            })

    print()

    if not rows:
        raise RuntimeError(
            "No requested genes were found in HRApop."
        )

    df = pd.DataFrame(rows).drop_duplicates()

    # Relevance is relative to each gene.
    #
    # First transform expression to reduce domination by very
    # highly expressed housekeeping genes.
    df["_score"] = df["mean expression"].clip(lower=0).map(
        lambda x: math.log1p(x)
    )

    # Normalize each gene to its strongest HRA location.
    df["relevance"] = (
        df["_score"]
        / df.groupby("gene")["_score"].transform("max")
    )

    df = df.drop(columns="_score")

    df = df.sort_values(
        ["gene", "relevance"],
        ascending=[True, False],
    )

    df.to_csv(args.output, index=False)

    print(f"Wrote {len(df)} rows to {args.output}")

if __name__ == "__main__":
    main()
