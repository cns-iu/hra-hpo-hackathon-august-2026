# LLM coded untested!!!

import argparse
import requests
import pandas as pd

ASCTB_BASE_URL = "https://purl.humanatlas.io/asct-b"

# List of organs available in ASCT-B (verified working endpoints)
ORGANS = [
    "kidney",
    "liver",
    "lung",
    "heart",
    "skin",
    "eye",
    "spleen",
    "thymus",
    "ovary",
    "prostate",
    "pancreas",
    "bone-marrow",
    "lymph-node",
    "large-intestine",
    "small-intestine",
    "blood-vasculature",
    "knee",
    "peripheral-nervous-system",
    "fallopian-tube",
    "uterus",
    "ureter",
]


def fetch_asctb_data(organ):
    """Fetch ASCT-B data for a specific organ"""
    url = f"{ASCTB_BASE_URL}/{organ}"
    try:
        r = requests.get(
            url,
            headers={"Accept": "application/json"},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"  ⚠️  Failed to fetch {organ}: {e}")
        return None


def extract_gene_symbol(hgnc_id, biomarkers_lookup):
    """Extract gene symbol from HGNC ID using biomarkers lookup"""
    # hgnc_id format: "HGNC:123"
    biomarker = biomarkers_lookup.get(hgnc_id, {})
    return biomarker.get("ccf_pref_label", hgnc_id)


def parse_asctb_organ(organ_data, target_genes):
    """
    Parse ASCT-B organ data and extract gene-cell-anatomy relationships

    Returns: list of dicts with gene, cell type, and anatomy info
    """
    if not organ_data or "data" not in organ_data:
        return []

    data = organ_data["data"]

    # Build lookup dictionaries
    biomarkers_lookup = {b["id"]: b for b in data.get("biomarkers", [])}
    cell_types_lookup = {c["id"]: c for c in data.get("cell_types", [])}
    anatomical_structures_lookup = {
        a["id"]: a for a in data.get("anatomical_structures", [])
    }

    rows = []

    # Parse cell_marker_descriptor entries
    for descriptor in data.get("cell_marker_descriptor", []):
        cell_type_id = descriptor.get("primary_cell_type")
        anatomy_id = descriptor.get("primary_anatomical_structure")
        biomarker_set = descriptor.get("biomarker_set", [])

        # Get labels
        cell_type_info = cell_types_lookup.get(cell_type_id, {})
        cell_type_label = cell_type_info.get("ccf_pref_label", cell_type_id)

        anatomy_info = anatomical_structures_lookup.get(anatomy_id, {})
        anatomy_label = anatomy_info.get("ccf_pref_label", anatomy_id)

        # Process each biomarker (gene)
        for hgnc_id in biomarker_set:
            gene_symbol = extract_gene_symbol(hgnc_id, biomarkers_lookup).upper()
            # Check if this gene is in our target list
            if gene_symbol in target_genes:
                rows.append(
                    {
                        "gene": gene_symbol,
                        "HGNC": hgnc_id,
                        "UBERON": (
                            anatomy_id if anatomy_id.startswith("UBERON:") else ""
                        ),
                        "anatomy": anatomy_label,
                        "CL": (
                            cell_type_id
                            if cell_type_id.startswith("CL:")
                            else cell_type_id.split("/")[-1]
                        ),
                        "cell_type": cell_type_label,
                    }
                )

    return rows


def genes_from_file(path):
    """Read gene symbols from file, returning uppercase set"""
    with open(path) as f:
        return {x.strip().upper() for x in f if x.strip() and not x.startswith("#")}


def process_genes(gene_symbols, organs=None):
    """
    Process a list of gene symbols and return mappings to anatomy/cell types.

    Args:
        gene_symbols: Set or list of gene symbols (e.g., {'CTLA4', 'CD4'})
        organs: Optional list of specific organs to query (default: all ORGANS)

    Returns:
        List of dicts with gene, HGNC, UBERON, anatomy, CL, cell_type
    """
    organs_to_query = organs if organs else ORGANS
    all_rows = []

    for organ in organs_to_query:
        organ_data = fetch_asctb_data(organ)
        if organ_data:
            rows = parse_asctb_organ(organ_data, gene_symbols)
            all_rows.extend(rows)

    return all_rows


def main():
    p = argparse.ArgumentParser(
        description="Extract gene-to-anatomy mappings from HRA ASCT-B data"
    )
    p.add_argument("genes", help="File containing gene symbols (one per line)")
    p.add_argument(
        "-o",
        "--output",
        default="hra_gene_locations.csv",
        help="Output CSV file (default: hra_gene_locations.csv)",
    )
    p.add_argument(
        "--organs", nargs="+", help="Specific organs to query (default: all)"
    )
    args = p.parse_args()

    # Load target genes
    target_genes = genes_from_file(args.genes)
    print(
        f"🔍 Searching ASCT-B for {len(target_genes)} genes: {', '.join(sorted(target_genes))}"
    )

    # Determine which organs to query
    organs_to_query = args.organs if args.organs else ORGANS

    all_rows = []

    # Fetch and parse each organ
    for i, organ in enumerate(organs_to_query, 1):
        print(f"[{i}/{len(organs_to_query)}] Fetching {organ}...", end=" ", flush=True)

        organ_data = fetch_asctb_data(organ)
        if organ_data:
            rows = parse_asctb_organ(organ_data, target_genes)
            all_rows.extend(rows)
            print(f"✓ Found {len(rows)} gene-cell-anatomy mappings")
        else:
            print()

    if not all_rows:
        print("\n❌ No matching genes found in ASCT-B data.")
        print("Tip: Check gene symbols and ensure they match HGNC naming.")
        return

    # Create DataFrame and remove duplicates
    df = pd.DataFrame(all_rows).drop_duplicates()

    # Sort by gene and cell type
    df = df.sort_values(["gene", "cell_type", "anatomy"])

    # Save to CSV
    df.to_csv(args.output, index=False)

    print(f"\n✅ Wrote {len(df)} unique mappings to {args.output}")
    print(f"   Genes found: {df['gene'].nunique()}")
    print(f"   Cell types: {df['cell_type'].nunique()}")
    print(f"   Anatomical structures: {df['anatomy'].nunique()}")


if __name__ == "__main__":
    main()
