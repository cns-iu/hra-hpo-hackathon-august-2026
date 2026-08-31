# GenePy HRA-HPO Pipeline

Tools for mapping patient phenotypes and gene locations using Human Reference Atlas (HRA) and Human Phenotype Ontology (HPO) data.

## Table of Contents

1. [Quick Setup](#quick-setup)
2. [HPO to Ontologies Mapper](#hpo-to-ontologies-mapper) - Map patient phenotypes to anatomical/cellular terms
3. [Gene to HRA Mapper](#gene-to-hra-mapper) - Map genes to anatomical locations and cell types
4. [Patient-Gene Comparison & 3D Visualization](#patient-gene-comparison--3d-visualization) - Compare and visualize patient-gene matches

---

## Quick Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install rdflib requests pandas matplotlib numpy oaklib
```

---

# HPO to Ontologies Mapper

Maps HPO (Human Phenotype Ontology) terms to their corresponding UBERON, CL (Cell Ontology), and GO (Gene Ontology) terms.

## Usage

Input file with HPO IDs (one per line):
```
HP:0100886
HP:0007373
```

Run:
```bash
python genepy/connect_hpo_to_ontologies.py my_patient_hpos.txt results.tsv
```

## Output Format

TSV with columns: `HPO_ID`, `HPO_Label`, `Mapped_ID`, `Mapped_Label`

**Note:** One HPO term may map to multiple ontology terms (one row per mapping).

---

# Gene to HRA Mapper

# Gene to HRA Mapper

Maps gene symbols to anatomical locations and cell types using HRA ASCT-B (Anatomical Structures, Cell Types, plus Biomarkers).

## Usage

Input file with gene symbols (one per line):
```
CTLA4
CD4
INS
```

Run:
```bash
# Query all 21 organs
python genepy/gene_to_ontos_HRA.py genes.txt -o results.csv

# Query specific organs only
python genepy/gene_to_ontos_HRA.py genes.txt --organs lung thymus kidney
```

## Output Format

CSV with columns: `gene`, `HGNC`, `UBERON`, `anatomy`, `CL`, `cell_type`

**Available organs:** kidney, liver, lung, heart, skin, eye, spleen, thymus, ovary, prostate, pancreas, bone-marrow, lymph-node, large-intestine, small-intestine, blood-vasculature, knee, peripheral-nervous-system, fallopian-tube, uterus, ureter

---

# Patient-Gene Comparison & 3D Visualization

Compares patient HPO phenotypes with candidate genes and generates a 3D scatter plot showing phenotype score, GenePy score, and ontology overlap score.

## Usage

### Input Format

**Option 1: Simple gene list** (`genes.txt`):
```
CTLA4
CD4
IL2RA
```

**Option 2: TSV with scores** (`candidate_genes.tsv`):
```tsv
gene    phenotype    GenePy
CTLA4   0.906        1.000
CD4     0.514        0.891
IL2RA   0.413        0.647
```

### Run Comparison

```bash
# With TSV input (includes 3D visualization)
python genepy/compare_patient_genes.py patient_hpo.txt candidate_genes.tsv

# Save intermediate mappings
python genepy/compare_patient_genes.py patient_hpo.txt candidate_genes.tsv --save-intermediate

# Custom output paths
python genepy/compare_patient_genes.py patient_hpo.txt genes.tsv -o results.csv --plot 3d_plot.png

# Query specific organs
python genepy/compare_patient_genes.py patient_hpo.txt genes.tsv --organs lung thymus
```

## Output Files

- **comparison_results.csv** - All genes with overlap scores and matches
- **gene_comparison_3d.png** - 3D scatter plot (if TSV input used)
- **patient_hpo_mappings.tsv** - Patient HPO→ontology mappings (with `--save-intermediate`)
- **candidate_gene_mappings.csv** - Gene→anatomy/cell mappings (with `--save-intermediate`)

## Scoring Formula

```
score = intersection_size / log₁₀(gene_union_size)
```

Where:
- **Patient union**: All CL + UBERON terms from patient's HPO phenotype
- **Gene union**: All CL + UBERON terms from gene's ASCT-B mappings
- **Intersection**: Terms appearing in both unions

## 3D Visualization

When using TSV input with `phenotype` and `GenePy` columns:
- **X-axis**: Phenotype score
- **Y-axis**: GenePy score  
- **Z-axis**: Ontology overlap score (calculated by formula above)
- Top 10 genes labeled automatically
- Color-coded by comparison score

## Notes

- **Exact term matching**: Currently uses exact ontology ID matching (no hierarchical expansion)
- **Limited matches expected**: CL/UBERON terms may not overlap due to granularity differences
  - Example: Patient has `CL:0000542` (lymphocyte), gene has `CL:0000815` (regulatory T cell)
  - These are hierarchically related but won't match with exact comparison
- **Future enhancement**: Load CL.owl/UBERON.owl to expand terms to ancestors for hierarchical matching