
import sys
import os
from rdflib import Graph, URIRef, Literal
import graphviz

# === Usage: python generate_er.py path/to/file.ttl ===

if len(sys.argv) < 2:
    print("❌ Please provide a path to a .ttl file as an argument.")
    sys.exit(1)

ttl_path = sys.argv[1]

if not os.path.isfile(ttl_path):
    print(f"❌ File not found: {ttl_path}")
    sys.exit(1)

# === Load RDF file ===
g = Graph()
g.parse(ttl_path, format="turtle")

# === Graphviz setup ===
dot = graphviz.Digraph(comment="ER Diagram")
dot.attr(rankdir="LR")  # Horizontal layout
dot.attr(dpi="600")  # High resolution

styles = {
    "entity": {"shape": "rectangle", "style": "filled", "fillcolor": "#f0f8ff"},
    "attribute": {"shape": "oval", "style": "filled", "fillcolor": "#ffe4e1"},
    "relationship": {"shape": "diamond", "style": "filled", "fillcolor": "#e6e6fa"}
}

triples_dict = {}
for s, p, o in g:
    triples_dict.setdefault(s, []).append((p, o))

for s, props in triples_dict.items():
    subj_label = str(s).split("#")[-1]
    dot.node(subj_label, subj_label, **styles["entity"])
    for p, o in props:
        pred_label = str(p).split("#")[-1]
        if isinstance(o, URIRef):
            obj_label = str(o).split("#")[-1]
            rel_id = f"{subj_label}_{pred_label}_{obj_label}"
            dot.node(rel_id, pred_label, **styles["relationship"])
            dot.edge(subj_label, rel_id, arrowhead="none")
            dot.edge(rel_id, obj_label)
            dot.node(obj_label, obj_label, **styles["entity"])
        elif isinstance(o, Literal):
            obj_label = str(o)
            dot.node(obj_label, obj_label, **styles["attribute"])
            dot.edge(subj_label, obj_label, label=pred_label)

# Set output name based on input file
output_name = os.path.splitext(os.path.basename(ttl_path))[0] + "_ER"
dot.render(output_name, format="svg", cleanup=True)
print(f"✅ ER diagram created: {output_name}.svg")
