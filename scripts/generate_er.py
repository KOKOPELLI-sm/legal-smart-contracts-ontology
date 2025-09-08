#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
from rdflib import Graph, URIRef, Literal
import graphviz

# ---------------------------------------
# Helpers
# ---------------------------------------

def localname(term: URIRef) -> str:
    """Return a readable local name from a URI or a blank node id."""
    s = str(term)
    if isinstance(term, URIRef):
        # split on # or / and keep the last token
        if "#" in s:
            return s.rsplit("#", 1)[-1] or s
        return s.rstrip("/").rsplit("/", 1)[-1] or s
    return s

def safe_id(text: str) -> str:
    """Make a Graphviz-safe node id (no spaces/quotes)."""
    return re.sub(r'[^A-Za-z0-9_:\.-]', '_', text)

def label_for(term, g: Graph) -> str:
    """
    Prefer rdfs:label if present; otherwise use localname().
    Works for URIs; for Literals just return string.
    """
    if isinstance(term, Literal):
        return str(term)
    if isinstance(term, URIRef):
        # try to fetch a label
        for _, _, lab in g.triples((term, URIRef("http://www.w3.org/2000/01/rdf-schema#label"), None)):
            return str(lab)
        return localname(term)
    return str(term)

# ---------------------------------------
# CLI (positional input, optional output)
# ---------------------------------------

if len(sys.argv) < 2:
    print("Usage: python generate_er.py path/to/file.ttl [out.svg]")
    sys.exit(1)

ttl_path = sys.argv[1]
if not os.path.isfile(ttl_path):
    print(f"❌ File not found: {ttl_path}")
    sys.exit(1)

out_svg = None
if len(sys.argv) >= 3:
    out_svg = sys.argv[2]

# ---------------------------------------
# Load RDF
# ---------------------------------------
g = Graph()
g.parse(ttl_path, format="turtle")

# ---------------------------------------
# Graphviz setup
# ---------------------------------------
dot = graphviz.Digraph(comment="ER Diagram")
dot.attr(rankdir="LR")       # Horizontal layout
dot.attr(dpi="600")          # High resolution

styles = {
    "entity":       {"shape": "rectangle", "style": "filled", "fillcolor": "#f0f8ff"},
    "attribute":    {"shape": "oval",      "style": "filled", "fillcolor": "#ffe4e1"},
    "relationship": {"shape": "diamond",   "style": "filled", "fillcolor": "#e6e6fa"},
}

# Collect triples per subject
triples_by_s = {}
for s, p, o in g:
    triples_by_s.setdefault(s, []).append((p, o))

# To avoid duplicate node creation
created = set()

def ensure_node(node_id: str, label: str, kind: str):
    key = (node_id, kind)
    if key in created:
        return
    dot.node(node_id, label, **styles[kind])
    created.add(key)

# ---------------------------------------
# Build ER-ish view:
#   - Subject as entity (rectangle)
#   - If object is URI: make a diamond (relationship) with predicate label, then entity for object
#   - If object is literal: make an oval (attribute) and edge labeled with predicate
# ---------------------------------------
for s, props in triples_by_s.items():
    s_label = label_for(s, g)
    s_id = safe_id(localname(s))
    ensure_node(s_id, s_label, "entity")

    for p, o in props:
        pred_lab = localname(p)

        if isinstance(o, URIRef):
            o_label = label_for(o, g)
            o_id = safe_id(localname(o))
            # relationship node id must be unique per (s,p,o)
            rel_id = safe_id(f"{s_id}__{pred_lab}__{o_id}")
            ensure_node(rel_id, pred_lab, "relationship")
            ensure_node(o_id, o_label, "entity")

            # connect s -> rel (no arrow) and rel -> o
            dot.edge(s_id, rel_id, arrowhead="none")
            dot.edge(rel_id, o_id)
        else:
            # literal attribute
            lit = str(o)
            # optional truncation for very long literals
            label_lit = lit if len(lit) <= 64 else (lit[:61] + "…")
            attr_id = safe_id(f"{s_id}__{pred_lab}__{hash(lit)}")
            ensure_node(attr_id, label_lit, "attribute")
            dot.edge(s_id, attr_id, label=pred_lab)

# ---------------------------------------
# Render
# ---------------------------------------
if not out_svg:
    stem = os.path.splitext(os.path.basename(ttl_path))[0]
    out_svg = f"{stem}_ER.svg"

# Graphviz render() expects name without extension when using format=...
out_name = os.path.splitext(out_svg)[0]
dot.render(out_name, format="svg", cleanup=True)
print(f"✅ ER diagram created: {out_name}.svg")