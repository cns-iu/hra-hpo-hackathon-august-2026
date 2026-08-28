# Quickly vibe coded but seems to do the job of getting UBERON and CL and GO terms present in HPO terms.

# Intended use case: enter a set of HPO terms, most likely a patient's set of HPOs, but also all HPOs 
# associated to a gene may be valuable, and get a set of all possible terms connected to these. 

# The idea: use this to construct a sort of UBERON/CL/... patient "profile", maybe also traversing these
# ontologies further (use predefined classes of interest for immunology?). Can we then connect this to, e.g.
# tissue specific expression levels of a given gene of interest with HRA, creating a sort of gene "profile"
# and then map those to the mentioned ontologies, then we compare patient and gene to prioritize the pathogenic
# gene more effectively?

from rdflib import Graph, URIRef, OWL, RDF, RDFS
import requests
import os
import sys

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HPO_OWL_CACHE = os.path.join(SCRIPT_DIR, "hp.owl")
HPO = "http://purl.obolibrary.org/obo/"
wanted = ("UBERON_", "CL_", "GO_")

# Download HPO ontology if not cached
if not os.path.exists(HPO_OWL_CACHE):
    print(f"Downloading HPO ontology to {HPO_OWL_CACHE}...", file=sys.stderr)
    response = requests.get("https://purl.obolibrary.org/obo/hp.owl")
    with open(HPO_OWL_CACHE, 'w') as f:
        f.write(response.text)
    print("Download complete.", file=sys.stderr)

# Load graph
g = Graph()
print(f"Loading ontology from {HPO_OWL_CACHE}...", file=sys.stderr)
g.parse(HPO_OWL_CACHE, format="xml")
print("Ontology loaded.", file=sys.stderr)

def get_label(uri):
    """Get the label for a term from the graph."""
    for label in g.objects(uri, RDFS.label):
        return str(label)
    return ""

def fetch_ontology_label(term_id):
    """Fetch label from OLS API. Returns empty string on failure."""
    try:
        url = f"https://www.ebi.ac.uk/ols/api/terms?iri=http://purl.obolibrary.org/obo/{term_id.replace(':', '_')}"
        resp = requests.get(url, timeout=2)
        if resp.ok:
            data = resp.json()
            if data.get("_embedded", {}).get("terms"):
                return data["_embedded"]["terms"][0].get("label", "")
    except:
        pass
    return ""

def extract(node, seen=None):
    seen = set() if seen is None else seen
    if node in seen:
        return set()
    seen.add(node)

    found = set()

    # A class itself
    if isinstance(node, URIRef):
        s = str(node)
        if s.startswith(HPO) and any(x in s for x in wanted):
            found.add(s[len(HPO):].replace("_", ":", 1))

    # ONLY follow OWL expression constructs
    for predicate, obj in g.predicate_objects(node):

        if predicate in {
            OWL.intersectionOf,
            OWL.unionOf,
            OWL.someValuesFrom,
            OWL.allValuesFrom,
            OWL.hasValue,
            OWL.onClass,
            OWL.onProperty,
        }:
            found |= extract(obj, seen)

        # RDF list
        elif predicate == RDF.first:
            found |= extract(obj, seen)

        elif predicate == RDF.rest and obj != RDF.nil:
            found |= extract(obj, seen)

    return found


# Read input and output file paths from command line
if len(sys.argv) != 3:
    print("Usage: python connect_hpo_to_ontologies.py <input.txt> <output.tsv>", file=sys.stderr)
    print("  input.txt: HPO terms, one per line (e.g., HP:0100886)", file=sys.stderr)
    print("  output.tsv: Output TSV file", file=sys.stderr)
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

# Read HPO terms from input file
with open(input_file) as f:
    hpo_terms = [line.strip() for line in f if line.strip() and not line.startswith("#")]

print(f"Processing {len(hpo_terms)} HPO terms...", file=sys.stderr)

# Process each HPO term
results = []
for hpo in hpo_terms:
    uri = URIRef(HPO + hpo.replace(":", "_"))
    label = get_label(uri)
    
    mapped = set()
    for definition in g.objects(uri, OWL.equivalentClass):
        mapped |= extract(definition)
    
    # Create one row per mapped term, or one row with empty mapping if none found
    if mapped:
        for mapped_id in sorted(mapped):
            results.append((hpo, label, mapped_id))
    else:
        results.append((hpo, label, ""))

# Write TSV output
with open(output_file, 'w') as f:
    f.write("HPO_ID\tHPO_Label\tMapped_ID\tMapped_Label\n")
    for hpo, label, mapped_id in results:
        mapped_label = fetch_ontology_label(mapped_id) if mapped_id else ""
        f.write(f"{hpo}\t{label}\t{mapped_id}\t{mapped_label}\n")

print(f"Results written to {output_file}", file=sys.stderr)
