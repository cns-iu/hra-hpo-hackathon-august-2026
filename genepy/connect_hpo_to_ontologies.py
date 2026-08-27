from rdflib import Graph, URIRef, OWL, RDF



hpo_terms = ["HP:0100886", "HP:0007373"]


g = Graph()
g.parse("hp.owl")

HPO = "http://purl.obolibrary.org/obo/"
wanted = ("UBERON_", "CL_", "GO_")

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



for hpo in hpo_terms:
    uri = URIRef(HPO + hpo.replace(":", "_"))

    result = set()

    for definition in g.objects(uri, OWL.equivalentClass):
        result |= extract(definition)

    print(hpo, "->", sorted(result))