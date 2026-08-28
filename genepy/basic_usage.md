# HPO to Ontologies Mapper

Maps HPO (Human Phenotype Ontology) terms to their corresponding UBERON, CL (Cell Ontology), and GO (Gene Ontology) terms.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install rdflib requests
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