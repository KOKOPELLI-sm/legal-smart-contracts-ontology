#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
from pathlib import Path
from typing import Tuple, Optional
from rdflib import Graph, Namespace, Literal, RDF, RDFS, XSD, BNode
from rdflib.namespace import OWL
from slither.slither import Slither

EX = Namespace("http://example.org/smartcontracts#")

# ───────────────────────────── UI helpers ───────────────────────────── #

def make_ui(no_emoji: bool, quiet: bool):
    ok_sym   = "OK" if no_emoji else "✅"
    info_sym = "i"  if no_emoji else "ℹ️"
    warn_sym = "!"  if no_emoji else "⚠️"

    def _print(prefix: str, msg: str) -> None:
        if not quiet:
            print(f"{prefix} {msg}")

    def ok(msg: str) -> None:   _print(ok_sym, msg)
    def info(msg: str) -> None: _print(info_sym, msg)
    def warn(msg: str) -> None: _print(warn_sym, msg)
    return ok, info, warn

# ───────────────────────────── Utils ───────────────────────────── #

SAFE_RE = re.compile(r"[^A-Za-z0-9_]+")

def safe_uri(s: str) -> str:
    """Makes string safe for use as fragment IRI."""
    s = s.replace("(", "_").replace(")", "")
    s = s.replace(",", "_").replace(" ", "_")
    s = SAFE_RE.sub("_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unnamed"

MONETARY_KEYS = ("amount", "price", "value", "deposit", "rent", "fee", "cost")

def is_monetary_var(name: Optional[str], typ: Optional[str]) -> bool:
    """
    Heuristics for monetary state variables:
    - name containing one of MONETARY_KEYS,
    - or mapping(... => uint*) type,
    - or int/uint with name-hint.
    """
    n = (name or "").lower()
    t = (typ or "").lower()
    if any(k in n for k in MONETARY_KEYS):
        return True
    if "mapping" in t and "uint" in t:
        return True
    if re.search(r"\b(u?int(8|16|32|64|128|256)?)\b", t) and any(k in n for k in MONETARY_KEYS):
        return True
    return False

# ───────────────────────────── Schema (optional) ───────────────────────────── #

def _rdf_list(g: Graph, items: list) -> BNode:
    """Creates RDF collection (list) and returns head BNode."""
    if not items:
        return RDF.nil  # type: ignore
    head = BNode()
    cur = head
    for i, it in enumerate(items):
        g.add((cur, RDF.first, it))
        if i == len(items) - 1:
            g.add((cur, RDF.rest, RDF.nil))
        else:
            nxt = BNode()
            g.add((cur, RDF.rest, nxt))
            cur = nxt
    return head

def declare_schema(g: Graph) -> None:
    """
    Explicitly declares classes/properties with domains/ranges (safe to coexist with master TTL).
    """
    # Classes
    for cls in (
        EX.ContractComponent, EX.SmartContract, EX.Function, EX.AccessControlledFunction,
        EX.PayableFunction, EX.Event, EX.StateVariable, EX.Modifier,
        EX.Struct, EX.StructMember, EX.Parameter
    ):
        g.add((cls, RDF.type, OWL.Class))

    # Named union: Function ∪ StateVariable (for hasVisibility)
    g.add((EX.FunctionOrState, RDF.type, OWL.Class))
    g.add((EX.FunctionOrState, OWL.unionOf, _rdf_list(g, [EX.Function, EX.StateVariable])))

    # Object properties
    def objprop(p, dom, ran, label: str):
        g.add((p, RDF.type, OWL.ObjectProperty))
        g.add((p, RDFS.domain, dom))
        g.add((p, RDFS.range, ran))
        g.add((p, RDFS.label, Literal(label)))

    objprop(EX.hasFunction, EX.SmartContract, EX.Function, "has function")
    objprop(EX.hasEvent, EX.SmartContract, EX.Event, "has event")
    objprop(EX.hasVariable, EX.SmartContract, EX.StateVariable, "has state variable")
    objprop(EX.hasModifier, EX.SmartContract, EX.Modifier, "has modifier (declared in contract)")
    objprop(EX.hasAccessControl, EX.Function, EX.Modifier, "has access control")
    objprop(EX.hasStruct, EX.SmartContract, EX.Struct, "has struct")
    objprop(EX.hasMember, EX.Struct, EX.StructMember, "has member")
    objprop(EX.hasParameter, EX.Function, EX.Parameter, "has parameter")  # ONLY Function
    objprop(EX.readsVariable, EX.Function, EX.StateVariable, "reads variable")
    objprop(EX.writesVariable, EX.Function, EX.StateVariable, "writes variable")
    objprop(EX.emitsEvent, EX.Function, EX.Event, "emits event")

    # Datatype properties
    def datprop(p, dom, ran, label: str):
        g.add((p, RDF.type, OWL.DatatypeProperty))
        g.add((p, RDFS.domain, dom))
        g.add((p, RDFS.range, ran))
        g.add((p, RDFS.label, Literal(label)))

    datprop(EX.hasName, EX.ContractComponent, XSD.string, "has name")
    datprop(EX.hasType, EX.ContractComponent, XSD.string, "has type string")
    datprop(EX.hasVisibility, EX.FunctionOrState, XSD.string, "has visibility")

    # isMonetaryValue domain = (Parameter ∪ StateVariable)
    union_dom = BNode()
    g.add((union_dom, RDF.type, OWL.Class))
    g.add((union_dom, OWL.unionOf, _rdf_list(g, [EX.Parameter, EX.StateVariable])))
    datprop(EX.isMonetaryValue, union_dom, XSD.boolean, "is monetary value")

# ───────────────────────────── Extraction ───────────────────────────── #

def extract(sl: Slither, g: Graph, ok, info, warn) -> Tuple[int, int, int, int, int, int, int, int, int, int, int]:
    """
    Extracts elements to RDF graph and returns counters for summary.
    """
    n_contracts = n_functions = n_events = n_modifiers = 0
    n_structs = n_members = n_statevars = n_params = 0
    n_reads = n_writes = n_has_access = 0

    for contract in sl.contracts:
        n_contracts += 1
        contract_uri = EX[safe_uri(contract.name)]
        g.add((contract_uri, RDF.type, EX.SmartContract))
        g.add((contract_uri, EX.hasName, Literal(contract.name)))

        # Declared modifiers in the contract
        declared_mods = {}
        for m in getattr(contract, "modifiers", []):
            n_modifiers += 1
            mod_uri = EX[safe_uri(f"{contract.name}_Modifier_{m.name}")]
            declared_mods[m.name] = mod_uri
            g.add((mod_uri, RDF.type, EX.Modifier))
            g.add((mod_uri, EX.hasName, Literal(m.name)))
            g.add((contract_uri, EX.hasModifier, mod_uri))

        # Events (without hasParameter to keep domain=Function)
        for ev in getattr(contract, "events", []):
            n_events += 1
            event_uri = EX[safe_uri(f"{contract.name}_Event_{ev.name}")]
            g.add((event_uri, RDF.type, EX.Event))
            g.add((event_uri, EX.hasName, Literal(ev.name)))
            g.add((contract_uri, EX.hasEvent, event_uri))

        # Structs & members
        for st in getattr(contract, "structs", []):
            n_structs += 1
            struct_uri = EX[safe_uri(f"{contract.name}_Struct_{st.name}")]
            g.add((struct_uri, RDF.type, EX.Struct))
            g.add((struct_uri, EX.hasName, Literal(st.name)))
            g.add((contract_uri, EX.hasStruct, struct_uri))

            elems = getattr(st, "elems", []) or getattr(st, "elements", [])
            for idx, mem in enumerate(elems):
                n_members += 1
                try:
                    mname = getattr(mem, "name", f"m{idx}") or f"m{idx}"
                    mtype = str(getattr(mem, "type", "") or "")
                except Exception:
                    mname, mtype = f"m{idx}", ""
                member_uri = EX[safe_uri(f"{contract.name}_Struct_{st.name}_Member_{mname}")]
                g.add((member_uri, RDF.type, EX.StructMember))
                g.add((member_uri, EX.hasName, Literal(mname)))
                if mtype:
                    g.add((member_uri, EX.hasType, Literal(mtype)))
                g.add((struct_uri, EX.hasMember, member_uri))

        # State variables
        for var in getattr(contract, "state_variables_declared", []):
            n_statevars += 1
            vname = getattr(var, "name", "") or ""
            vtype = str(getattr(var, "type", "") or "")
            var_uri = EX[safe_uri(f"{contract.name}_Var_{vname}")]
            g.add((var_uri, RDF.type, EX.StateVariable))
            g.add((var_uri, EX.hasName, Literal(vname)))
            if vtype:
                g.add((var_uri, EX.hasType, Literal(vtype)))
            vis = getattr(var, "visibility", None)
            if vis is not None:
                g.add((var_uri, EX.hasVisibility, Literal(str(vis))))
            if is_monetary_var(vname, vtype):
                g.add((var_uri, EX.isMonetaryValue, Literal(True)))
            g.add((contract_uri, EX.hasVariable, var_uri))

        # Functions
        for function in getattr(contract, "functions_declared", []):
            n_functions += 1
            fn_name = f"{contract.name}_{function.full_name.replace('(', '_').replace(')', '')}"
            function_uri = EX[safe_uri(fn_name)]

            g.add((contract_uri, EX.hasFunction, function_uri))
            g.add((function_uri, RDF.type, EX.Function))
            g.add((function_uri, EX.hasName, Literal(function.full_name)))

            if getattr(function, "visibility", None):
                g.add((function_uri, EX.hasVisibility, Literal(str(function.visibility))))

            if getattr(function, "payable", False):
                g.add((function_uri, RDF.type, EX.PayableFunction))

            # Modifiers used by the function
            for call in getattr(function, "modifiers", []):
                mobj = getattr(call, "modifier", None) or call
                mname = getattr(mobj, "name", None)
                if not mname:
                    continue
                mod_uri = declared_mods.get(mname)
                if mod_uri is None:
                    # declared on-the-fly if not in declared
                    n_modifiers += 1
                    mod_uri = EX[safe_uri(f"{contract.name}_Modifier_{mname}")]
                    declared_mods[mname] = mod_uri
                    g.add((mod_uri, RDF.type, EX.Modifier))
                    g.add((mod_uri, EX.hasName, Literal(mname)))
                    g.add((contract_uri, EX.hasModifier, mod_uri))
                g.add((function_uri, EX.hasAccessControl, mod_uri))
                g.add((function_uri, RDF.type, EX.AccessControlledFunction))
                n_has_access += 1

            # Parameters (ONLY for Function)
            for idx, p in enumerate(getattr(function, "parameters", [])):
                n_params += 1
                pname = getattr(p, "name", f"p{idx}") or f"p{idx}"
                ptype = str(getattr(p, "type", "") or "")
                param_uri = EX[safe_uri(f"{contract.name}_Func_{function.full_name}_Param_{pname}")]
                g.add((param_uri, RDF.type, EX.Parameter))
                g.add((param_uri, EX.hasName, Literal(pname)))
                if ptype:
                    g.add((param_uri, EX.hasType, Literal(ptype)))
                if any(k in pname.lower() for k in MONETARY_KEYS):
                    g.add((param_uri, EX.isMonetaryValue, Literal(True)))
                g.add((function_uri, EX.hasParameter, param_uri))

            # Reads / writes
            for v in getattr(function, "state_variables_read", []) or []:
                vuri = EX[safe_uri(f"{contract.name}_Var_{getattr(v, 'name', '')}")]
                g.add((function_uri, EX.readsVariable, vuri))
                n_reads += 1
            for v in getattr(function, "state_variables_written", []) or []:
                vuri = EX[safe_uri(f"{contract.name}_Var_{getattr(v, 'name', '')}")]
                g.add((function_uri, EX.writesVariable, vuri))
                n_writes += 1

    return (n_contracts, n_functions, n_events, n_modifiers,
            n_structs, n_members, n_statevars, n_params, n_reads, n_writes, n_has_access)

# ───────────────────────────── CLI ───────────────────────────── #

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Solidity file or project directory for Slither")
    parser.add_argument("-o", "--out", default="contracts.ttl", help="Output TTL path")
    parser.add_argument("--declare-schema", action="store_true",
                        help="If set, also writes schema (classes/properties/domain/range).")
    parser.add_argument("--no-emoji", action="store_true", help="Disable emoji in logs")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    ok, info, warn = make_ui(args.no_emoji, args.quiet)

    info(f"Parsing Slither target: {args.target}")
    sl = Slither(args.target)
    ok("Loaded project with Slither")

    g = Graph()
    g.bind("ex", EX); g.bind("rdf", RDF); g.bind("rdfs", RDFS); g.bind("xsd", XSD); g.bind("owl", OWL)

    if args.declare_schema:
        info("Declaring schema (classes/properties/domains/ranges)")
        declare_schema(g)

    # Extract
    (n_contracts, n_functions, n_events, n_modifiers,
     n_structs, n_members, n_statevars, n_params, n_reads, n_writes, n_has_access) = extract(sl, g, ok, info, warn)

    # Serialize
    out_path = Path(args.out)
    g.serialize(destination=str(out_path), format="turtle")
    ok(f"Wrote RDF to: {out_path}")

    # Summary
    total_triples = len(g)
    info("—" * 60)
    info("Run summary")
    info(f"Contracts: {n_contracts}")
    info(f"Functions: {n_functions}  | Params: {n_params}")
    info(f"StateVars: {n_statevars}  | Reads: {n_reads}  | Writes: {n_writes}")
    info(f"Events:    {n_events}     | Emits (captured): 0 (placeholder)")
    info(f"Modifiers: {n_modifiers}  | AccessControl links: {n_has_access}")
    info(f"Structs:   {n_structs}    | Members: {n_members}")
    ok(f"Triples written: {total_triples}")

if __name__ == "__main__":
    run()
