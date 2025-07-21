import sys
from rdflib import Graph

if len(sys.argv) < 2:
    print("Usage: python validate.py <ontology_file> [format]")
    print("Example: python validate.py ontologies/master_ontology.ttl turtle")
    sys.exit(1)

file_path = sys.argv[1]

# Try to auto-detect format if not given
if len(sys.argv) > 2:
    rdf_format = sys.argv[2]
else:
    # Guess from extension
    if file_path.endswith('.ttl'):
        rdf_format = 'turtle'
    elif file_path.endswith('.rdf') or file_path.endswith('.owl'):
        rdf_format = 'xml'
    elif file_path.endswith('.nt'):
        rdf_format = 'nt'
    else:
        rdf_format = 'turtle'  # fallback

try:
    g = Graph()
    g.parse(file_path, format=rdf_format)
    print(f"Validation successful! File '{file_path}' is valid RDF ({rdf_format}).")
except Exception as e:
    print(f"Validation failed for file '{file_path}'!")
    print(e)
    sys.exit(2)
