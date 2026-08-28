#!/usr/bin/env python3
"""
Compare Patient HPO Terms to Candidate Gene Mappings

This script takes:
1. Patient HPO terms → maps to CL/UBERON terms
2. Candidate genes → maps to CL/UBERON terms from HRA ASCT-B
3. Compares the sets to find overlapping anatomical/cellular contexts

Usage:
    python compare_patient_genes.py <patient_hpo_file> <candidate_genes_file> [options]
"""

import argparse
import pandas as pd
import numpy as np
import math
from pathlib import Path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Import functions from existing scripts
from connect_hpo_to_ontologies import process_hpo_terms
from gene_to_ontos_HRA import process_genes


def extract_ontology_terms(hpo_mappings):
    """
    Extract CL and UBERON terms from HPO mapping results.

    Args:
        hpo_mappings: List of tuples (hpo_id, hpo_label, mapped_id, mapped_label)

    Returns:
        dict with 'CL' and 'UBERON' sets
    """
    patient_terms = {"CL": set(), "UBERON": set(), "GO": set()}

    for hpo_id, hpo_label, mapped_id, mapped_label in hpo_mappings:
        if not mapped_id:
            continue

        if mapped_id.startswith("CL:"):
            patient_terms["CL"].add(mapped_id)
        elif mapped_id.startswith("UBERON:"):
            patient_terms["UBERON"].add(mapped_id)
        elif mapped_id.startswith("GO:"):
            patient_terms["GO"].add(mapped_id)

    return patient_terms


def load_candidate_genes_with_scores(tsv_file):
    """
    Load candidate genes from TSV file with phenotype and GenePy scores.

    Args:
        tsv_file: Path to TSV file with columns: gene, phenotype, GenePy, etc.

    Returns:
        DataFrame with gene, phenotype, GenePy scores
    """
    df = pd.read_csv(tsv_file, sep="\t")

    # Validate required columns
    required_cols = ["gene", "phenotype", "GenePy"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"TSV file missing required columns: {missing}")

    return df[["gene", "phenotype", "GenePy"]].copy()


def extract_gene_terms(gene_mappings):
    """
    Extract CL and UBERON terms from gene mapping results.

    Args:
        gene_mappings: List of dicts with gene, HGNC, UBERON, anatomy, CL, cell_type

    Returns:
        dict mapping gene -> {'CL': set, 'UBERON': set}
    """
    gene_terms = {}

    for row in gene_mappings:
        gene = row["gene"]
        if gene not in gene_terms:
            gene_terms[gene] = {"CL": set(), "UBERON": set()}

        if row.get("CL"):
            # Extract just the CL ID (handles both "CL:123" and full URIs)
            cl_id = row["CL"]
            if cl_id.startswith("CL:"):
                gene_terms[gene]["CL"].add(cl_id)
            elif "/" in cl_id:
                # Extract from URI like "http://purl.obolibrary.org/obo/CL_0000815"
                cl_part = cl_id.split("/")[-1].replace("_", ":")
                gene_terms[gene]["CL"].add(cl_part)

        if row.get("UBERON"):
            uberon_id = row["UBERON"]
            if uberon_id.startswith("UBERON:"):
                gene_terms[gene]["UBERON"].add(uberon_id)

    return gene_terms


def compare_terms(patient_terms, gene_terms):
    """
    Compare patient ontology terms with gene ontology terms.

    Score formula:
    1. Union gene's CL and UBERON terms
    2. Union patient's CL and UBERON terms
    3. Find intersection size
    4. Score = intersection_size / log10(gene_union_size)

    Args:
        patient_terms: dict with 'CL', 'UBERON', 'GO' sets from patient HPO
        gene_terms: dict mapping gene -> {'CL': set, 'UBERON': set}

    Returns:
        dict mapping gene -> comparison metrics including score
    """
    results = {}

    # Patient union of CL and UBERON terms
    patient_union = patient_terms["CL"] | patient_terms["UBERON"]

    for gene, gene_ontologies in gene_terms.items():
        # Gene union of CL and UBERON terms
        gene_union = gene_ontologies["CL"] | gene_ontologies["UBERON"]

        # Find intersection between patient and gene unions
        intersection = patient_union & gene_union
        intersection_size = len(intersection)

        # Calculate score: intersection_size / log10(gene_union_size)
        gene_union_size = len(gene_union)
        if gene_union_size > 1:
            log_denominator = math.log10(gene_union_size)
            score = intersection_size / log_denominator
        elif gene_union_size == 1:
            # log10(1) = 0, so just use intersection size
            score = float(intersection_size)
        else:
            score = 0.0

        # Also track individual overlaps for reference
        cl_overlap = patient_terms["CL"] & gene_ontologies["CL"]
        uberon_overlap = patient_terms["UBERON"] & gene_ontologies["UBERON"]

        results[gene] = {
            "cl_overlap_count": len(cl_overlap),
            "uberon_overlap_count": len(uberon_overlap),
            "cl_matches": cl_overlap,
            "uberon_matches": uberon_overlap,
            "total_overlap": intersection_size,
            "score": score,
        }

    return results


def create_3d_plot(results_df, output_file="gene_comparison_3d.png"):
    """
    Create a 3D scatter plot of gene comparison results.

    Args:
        results_df: DataFrame with columns: gene, phenotype, GenePy, comparison_score
        output_file: Path to save the plot image
    """
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    # Extract coordinates
    x = results_df["phenotype"].values
    y = results_df["GenePy"].values
    z = results_df["comparison_score"].values

    # Color by comparison score (Z axis)
    colors = plt.cm.viridis(z / (z.max() if z.max() > 0 else 1))

    # Create scatter plot
    scatter = ax.scatter(
        x,
        y,
        z,
        c=z,
        cmap="viridis",
        s=100,
        alpha=0.7,
        edgecolors="black",
        linewidth=0.5,
    )

    # Add labels for top genes
    top_genes = results_df.nlargest(10, "comparison_score")
    for _, row in top_genes.iterrows():
        ax.text(
            row["phenotype"],
            row["GenePy"],
            row["comparison_score"],
            row["gene"],
            fontsize=8,
            alpha=0.8,
        )

    # Labels and title
    ax.set_xlabel("Phenotype Score", fontsize=11, labelpad=10)
    ax.set_ylabel("GenePy Score", fontsize=11, labelpad=10)
    ax.set_zlabel("Comparison Score (Ontology Overlap)", fontsize=11, labelpad=10)
    ax.set_title(
        "3D Gene Comparison: Phenotype × GenePy × Ontology Overlap", fontsize=13, pad=20
    )

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, pad=0.1, shrink=0.8)
    cbar.set_label("Comparison Score", fontsize=10)

    # Set view angle
    ax.view_init(elev=20, azim=45)

    # Grid
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"\n📊 3D plot saved to {output_file}")

    return fig


def main():
    parser = argparse.ArgumentParser(
        description="Compare patient HPO phenotypes to candidate gene mappings with 3D visualization"
    )
    parser.add_argument(
        "patient_hpo", help="File with patient HPO terms (one per line)"
    )
    parser.add_argument(
        "candidate_genes_tsv",
        help="TSV file with candidate genes (columns: gene, phenotype, GenePy)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="comparison_results.csv",
        help="Output CSV file (default: comparison_results.csv)",
    )
    parser.add_argument(
        "--plot",
        default="gene_comparison_3d.png",
        help="3D plot output file (default: gene_comparison_3d.png)",
    )
    parser.add_argument(
        "--organs",
        nargs="+",
        help="Specific HRA organs to query for genes (default: all)",
    )
    parser.add_argument(
        "--save-intermediate",
        action="store_true",
        help="Save intermediate patient and gene mapping files",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Patient-Gene Ontology Comparison Pipeline with 3D Visualization")
    print("=" * 70)

    # Step 1: Process patient HPO terms
    print("\n[Step 1/4] Processing patient HPO terms...")
    with open(args.patient_hpo) as f:
        hpo_terms = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    print(
        f"  Found {len(hpo_terms)} HPO terms: {', '.join(hpo_terms[:5])}"
        + (f" ... (+{len(hpo_terms)-5} more)" if len(hpo_terms) > 5 else "")
    )

    hpo_mappings = process_hpo_terms(hpo_terms)
    patient_terms = extract_ontology_terms(hpo_mappings)

    print(
        f"  ✓ Mapped to {len(patient_terms['CL'])} CL terms, "
        f"{len(patient_terms['UBERON'])} UBERON terms, "
        f"{len(patient_terms['GO'])} GO terms"
    )

    if args.save_intermediate:
        hpo_df = pd.DataFrame(
            hpo_mappings, columns=["HPO_ID", "HPO_Label", "Mapped_ID", "Mapped_Label"]
        )
        hpo_file = "patient_hpo_mappings.tsv"
        hpo_df.to_csv(hpo_file, sep="\t", index=False)
        print(f"  Saved to {hpo_file}")

    # Step 2: Load candidate genes with their scores
    print("\n[Step 2/4] Loading candidate genes with phenotype and GenePy scores...")
    genes_df = load_candidate_genes_with_scores(args.candidate_genes_tsv)
    gene_symbols = set(genes_df["gene"].str.upper())

    print(f"  Found {len(gene_symbols)} genes from TSV")
    print(
        f"  Phenotype score range: {genes_df['phenotype'].min():.3f} - {genes_df['phenotype'].max():.3f}"
    )
    print(
        f"  GenePy score range: {genes_df['GenePy'].min():.3f} - {genes_df['GenePy'].max():.3f}"
    )

    # Step 3: Process candidate genes for ontology mappings
    print("\n[Step 3/4] Processing candidate genes for ontology mappings...")
    gene_mappings = process_genes(gene_symbols, organs=args.organs)
    gene_terms = extract_gene_terms(gene_mappings)

    print(f"  ✓ Retrieved mappings for {len(gene_terms)} genes")
    for gene, terms in list(gene_terms.items())[:3]:
        print(f"    {gene}: {len(terms['CL'])} CL, {len(terms['UBERON'])} UBERON")

    if args.save_intermediate:
        gene_df = pd.DataFrame(gene_mappings)
        gene_file = "candidate_gene_mappings.csv"
        gene_df.to_csv(gene_file, index=False)
        print(f"  Saved to {gene_file}")

    # Step 4: Compare patient and gene terms
    print("\n[Step 4/4] Comparing patient phenotype to gene contexts...")
    comparison_results = compare_terms(patient_terms, gene_terms)

    # Format results and merge with input scores
    output_rows = []
    for gene, result in comparison_results.items():
        output_rows.append(
            {
                "gene": gene,
                "cl_overlap_count": result["cl_overlap_count"],
                "uberon_overlap_count": result["uberon_overlap_count"],
                "total_overlap": result["total_overlap"],
                "score": result["score"],
                "cl_matches": ";".join(sorted(result["cl_matches"])),
                "uberon_matches": ";".join(sorted(result["uberon_matches"])),
            }
        )

    results_df = pd.DataFrame(output_rows)

    # Merge with phenotype and GenePy scores
    # Use left join from genes_df to ensure all genes from TSV are included
    genes_df["gene"] = genes_df["gene"].str.upper()
    results_df = genes_df.merge(results_df, on="gene", how="left")

    # Fill NaN values for genes without ASCT-B matches
    results_df["cl_overlap_count"] = (
        results_df["cl_overlap_count"].fillna(0).astype(int)
    )
    results_df["uberon_overlap_count"] = (
        results_df["uberon_overlap_count"].fillna(0).astype(int)
    )
    results_df["total_overlap"] = results_df["total_overlap"].fillna(0).astype(int)
    results_df["score"] = results_df["score"].fillna(0.0)
    results_df["cl_matches"] = results_df["cl_matches"].fillna("")
    results_df["uberon_matches"] = results_df["uberon_matches"].fillna("")

    # Use the calculated score as comparison_score for plotting
    results_df["comparison_score"] = results_df["score"]

    # Sort by comparison score
    results_df = results_df.sort_values("comparison_score", ascending=False)
    results_df.to_csv(args.output, index=False)

    print(f"\n✅ Comparison complete!")
    print(f"   Results saved to {args.output}")
    print(f"\nTop genes by comparison score:")
    display_cols = ["gene", "phenotype", "GenePy", "comparison_score", "total_overlap"]
    for _, row in results_df[display_cols].head(10).iterrows():
        print(
            f"  {row['gene']:10s} - Phenotype: {row['phenotype']:.3f}, "
            f"GenePy: {row['GenePy']:.3f}, Comparison: {row['comparison_score']:.3f} "
            f"({row['total_overlap']} overlaps)"
        )

    # Create 3D plot
    print("\n📊 Generating 3D visualization...")
    create_3d_plot(results_df, output_file=args.plot)

    print("\n" + "=" * 70)
    print("Scoring formula:")
    print("  score = intersection_size / log10(gene_union_size)")
    print(
        "  where intersection = (patient_CL ∪ patient_UBERON) ∩ (gene_CL ∪ gene_UBERON)"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
