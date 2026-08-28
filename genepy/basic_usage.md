# HPO to Ontologies Mapper

Maps HPO (Human Phenotype Ontology) terms to their corresponding UBERON, CL (Cell Ontology), and GO (Gene Ontology) terms.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install rdflib requests pandas
python genepy/connect_hpo_to_ontologies.py example_input.txt output.tsv
```

## Usage

Create an input file with HPO IDs (one per line):

```
# my_patient_hpos.txt
HP:0100886
HP:0007373
```

Run the script:

```bash
python genepy/connect_hpo_to_ontologies.py my_patient_hpos.txt results.tsv
```

## Output Format

TSV file with columns:
- `HPO_ID`: HPO identifier
- `HPO_Label`: Human-readable phenotype name
- `Mapped_ID`: Single UBERON/CL/GO identifier (one row per mapping)
- `Mapped_Label`: Corresponding label (fetched from OLS API if available)

**Note:** If one HPO term maps to multiple ontology terms, it will appear on multiple rows.

## Example

Input (`example_input.txt`):
```
HP:0100886
HP:0007373
```

Output (`output.tsv`):
```
HPO_ID      HPO_Label                        Mapped_ID       Mapped_Label
HP:0100886  Abnormality of globe location    UBERON:0010230  eyeball of camera-type eye
HP:0007373  Motor neuron atrophy             CL:0000100      motor neuron
```

If an HPO maps to multiple terms:
```
HPO_ID      HPO_Label    Mapped_ID       Mapped_Label
HP:0001234  Example      UBERON:0001     tissue A
HP:0001234  Example      UBERON:0002     tissue B
HP:0001234  Example      CL:0001         cell type
```

## Notes

- HPO ontology file (`hp.owl`) is cached in genepy/ directory
- Comments in input file (lines starting with `#`) are ignored
- Ontology labels fetched via OLS API (fails gracefully if offline)

---

# Gene to HRA Anatomy/Cell Types Mapper

Maps gene symbols to their anatomical locations and cell types using HRA ASCT-B (Anatomical Structures, Cell Types, plus Biomarkers) curated data.

## Quick Start

```bash
python genepy/gene_to_ontos_HRA.py gene.txt
```

## Usage

Create an input file with gene symbols (one per line):

```
# my_genes.txt
CTLA4
CD4
INS
```

Run the script:

```bash
# Query all organs
python genepy/gene_to_ontos_HRA.py my_genes.txt -o gene_results.csv

# Query specific organs only
python genepy/gene_to_ontos_HRA.py my_genes.txt --organs lung thymus kidney
```

## Output Format

CSV file with columns:
- `gene`: Gene symbol (uppercase)
- `HGNC`: HGNC identifier
- `UBERON`: UBERON anatomical structure ID
- `anatomy`: Human-readable anatomical structure name
- `CL`: Cell type identifier
- `cell_type`: Human-readable cell type name

## Example

Input (`gene.txt`):
```
CTLA4
```

Output (`hra_gene_locations.csv`):
```csv
gene,HGNC,UBERON,anatomy,CL,cell_type
CTLA4,HGNC:2505,UBERON:0002405,immune system of respiratory tract,CL:0000815,regulatory T cell
CTLA4,HGNC:2505,UBERON:0002371,Bone marrow,CL:0000824,mature Natural killer
CTLA4,HGNC:2505,UBERON:0002124,medulla of thymus,CL:0002677,regulatory T cells
```

## Available Organs

Queries 21 HRA organs: kidney, liver, lung, heart, skin, eye, spleen, thymus, ovary, prostate, pancreas, bone-marrow, lymph-node, large-intestine, small-intestine, blood-vasculature, knee, peripheral-nervous-system, fallopian-tube, uterus, ureter.

## Notes

- Uses HRA ASCT-B JSON API (no SPARQL dependency)
- Gene symbols must match HGNC naming conventions
- Returns curated biomarker-cell-anatomy relationships from ASCT-B tables

---

# Patient-Gene Ontology Comparison

Combines patient HPO phenotypes with candidate gene mappings to identify overlapping anatomical/cellular contexts.

## Quick Start

```bash
python genepy/compare_patient_genes.py patient_hpo.txt candidate_genes.txt
```

## Workflow

The script performs three steps:
1. **Maps patient HPO terms** → CL, UBERON, GO ontology terms
2. **Maps candidate genes** → CL, UBERON terms from HRA ASCT-B
3. **Compares term sets** using set operations (placeholder implementation)

## Usage

Create input files:
```
# patient_hpo.txt
HP:0001876
HP:0002716
HP:0002583

# candidate_genes.txt
CTLA4
CD4
IL2RA
```

Run comparison:
```bash
# Basic usage
python genepy/compare_patient_genes.py patient_hpo.txt candidate_genes.txt

# Save intermediate mappings
python genepy/compare_patient_genes.py patient_hpo.txt candidate_genes.txt --save-intermediate

# Query specific organs only
python genepy/compare_patient_genes.py patient_hpo.txt candidate_genes.txt --organs lung thymus
```

## Output

Main output (`comparison_results.csv`):
```csv
gene,cl_overlap_count,uberon_overlap_count,total_overlap,cl_matches,uberon_matches
CD4,2,1,3,CL:0000624;CL:0000815,UBERON:0002371
CTLA4,1,1,2,CL:0000815,UBERON:0002371
```

Optional intermediate files (with `--save-intermediate`):
- `patient_hpo_mappings.tsv` - HPO term mappings
- `candidate_gene_mappings.csv` - Gene-to-anatomy/cell mappings

## Customization

The `compare_terms()` function contains placeholder logic. Implement your own strategy:

```python
def compare_terms(patient_terms, gene_terms):
    # Your custom comparison logic here
    # Examples:
    # - Jaccard similarity
    # - Weighted scoring (CL vs UBERON)
    # - Ontology graph distance
    # - Ranking by relevance
    return results
```

## Example Use Case

Prioritize candidate genes for a patient with immune phenotypes:
1. Patient has HPO terms related to immune dysfunction
2. These map to specific cell types (T cells, B cells) and tissues (thymus, bone marrow)
3. Compare with genes known to be expressed in those cell types/tissues
4. Rank genes by anatomical/cellular context overlap with patient phenotype