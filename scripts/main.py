import click
from pathlib import Path
from slither.slither import Slither
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL, XSD
from urllib.parse import quote

# Define the namespace for the example ontology
EX = Namespace("http://example.org/smartcontracts#")


def safe_uri(name):
    """
    Create a safe URI by replacing spaces with underscores and quoting the name.
    """
    return URIRef(EX[quote(name.replace(" ", "_"))])


def contract_to_triples(slith):
    name_to_uri = {}
    def find_uri_by_name(name):
        return name_to_uri.get(name)

    """
    Convert a Slither contract to RDF triples with full semantic structure.
    """
    triples = Graph()
    triples.bind("ex", EX)
    triples.bind("rdfs", RDFS)
    triples.bind("owl", OWL)

    # --- Ontology: Class and Property Declarations (not instances!) ---
    # Classes
    for cls in [
        "SmartContract",
        "Function",
        "StateVariable",
        "Struct",
        "Member",
        "Parameter",
        "Event",
        "Modifier",
        "Role"
    ]:
        triples.add((EX[cls], RDF.type, OWL.Class))

    # Object Properties
    object_properties = [
        (EX.hasFunction, EX.SmartContract, EX.Function),
        (EX.hasVariable, EX.SmartContract, EX.StateVariable),
        (EX.hasEvent, EX.SmartContract, EX.Event),
        (EX.hasModifier, EX.Function, EX.Modifier),
        (EX.hasStruct, EX.SmartContract, EX.Struct),
        (EX.hasMember, EX.Struct, EX.Member),
        (EX.hasParameter, EX.Function, EX.Parameter),
        (EX.hasParameter, EX.Event, EX.Parameter),
        (EX.hasMember, EX.Struct, EX.Member),
        (EX.readsVariable, EX.Function, EX.StateVariable),
        (EX.writesVariable, EX.Function, EX.StateVariable),
        (EX.inheritsFrom, EX.SmartContract, EX.SmartContract),
        (EX.emitsEvent, EX.Function, EX.Event),
    ]
    for prop, dom, rng in object_properties:
        triples.add((prop, RDF.type, OWL.ObjectProperty))
        triples.add((prop, RDFS.domain, dom))
        triples.add((prop, RDFS.range, rng))

    # --- Dynamic ObjectProperty declaration for domain-specific or new predicates ---
    # After all triples are created, scan for any EX predicates that are not already declared as OWL.ObjectProperty
    declared_object_properties = set(prop for prop, _, _ in object_properties)
    for s, p, o in list(triples):
        if isinstance(p, URIRef) and str(p).startswith(str(EX)) and p not in declared_object_properties:
            # Only declare as ObjectProperty if not already declared
            triples.add((p, RDF.type, OWL.ObjectProperty))
            # Heuristic: if subject is Function, set domain to Function, else SmartContract
            if (s, RDF.type, EX.Function) in triples or "Function" in str(s):
                triples.add((p, RDFS.domain, EX.Function))
            else:
                triples.add((p, RDFS.domain, EX.SmartContract))
            triples.add((p, RDFS.range, OWL.Thing))
            declared_object_properties.add(p)
    # This enables main.py to dynamically extend the ontology with new properties from the contract, supporting open-world extensibility.
        triples.add((prop, RDF.type, OWL.DatatypeProperty))
        triples.add((prop, RDFS.domain, dom))
        triples.add((prop, RDFS.range, rng))

    for contract in slith.contracts:
        # --- SmartContract instance ---
        contract_uri = safe_uri(contract.name)
        triples.add((contract_uri, RDF.type, EX.SmartContract))
        triples.add((contract_uri, EX.hasName, Literal(contract.name)))

        # Inheritance
        for base in contract.inheritance:
            base_uri = safe_uri(base.name)
            triples.add((contract_uri, EX.inheritsFrom, base_uri))
            triples.add((base_uri, RDF.type, EX.SmartContract))

        # --- State Variables ---
        address_roles = set()
        for var in contract.state_variables_declared:
            var_uri = safe_uri(contract.name + "_" + var.name)
            name_to_uri[var.name] = var_uri
            name_to_uri[var.name] = var_uri

            triples.add((contract_uri, EX.hasVariable, var_uri))
            triples.add((var_uri, RDF.type, EX.StateVariable))
            triples.add((var_uri, EX.hasName, Literal(var.name)))
            var_type_str = str(var.type)
            triples.add((var_uri, EX.hasType, Literal(var_type_str)))
            triples.add((var_uri, EX.hasVisibility, Literal(var.visibility)))
            if any(
                k in var.name.lower() for k in ("amount", "deposit", "price", "rent")
            ):
                triples.add((var_uri, EX.isMonetaryValue, Literal(True)))
            if "mapping" in var_type_str.lower():
                triples.add((var_uri, RDF.type, EX.MappingVariable))
            elif var_type_str.endswith("[]"):
                triples.add((var_uri, RDF.type, EX.ArrayVariable))
            # if variable is of type address, treat as potential role ---
            if var_type_str.strip().lower() == "address" or var_type_str.strip().lower() == "address payable":
                role_name = var.name
                # Remove common suffixes/prefixes
                for suffix in ["Address", "address"]:
                    if role_name.endswith(suffix):
                        role_name = role_name[:-len(suffix)]
                role_name = role_name[0].upper() + role_name[1:] if role_name else "Role"
                if role_name:
                    address_roles.add(role_name)

        # --- Functions ---
        for function in contract.functions_declared:
            fn_name = contract.name + "_" + function.name
            function_uri = safe_uri(fn_name)
            name_to_uri[function.name] = function_uri

            fn_name = (
                contract.name
                + "_"
                + function.full_name.replace("(", "_")
                .replace(")", "")
                .replace(",", "_")
            )
            function_uri = safe_uri(fn_name)
            triples.add((contract_uri, EX.hasFunction, function_uri))
            triples.add((function_uri, RDF.type, EX.Function))
            triples.add((function_uri, EX.hasName, Literal(function.name)))
            triples.add((function_uri, EX.hasVisibility, Literal(function.visibility)))
            if hasattr(function, "payable") and function.payable:
                triples.add((function_uri, EX.isPayable, Literal(True)))
            if any(k in function.name.lower() for k in ("pay", "deposit", "rent")):
                triples.add((function_uri, RDF.type, EX.MonetaryFunction))

            # --- Function Preconditions ---
            for node in getattr(function, 'nodes', []):
                if hasattr(node, "expression") and hasattr(node.expression, "function_name") and node.expression.function_name == "require":
                    # Υποθέτουμε ότι το πρώτο argument είναι το dependency
                    if hasattr(node.expression, "arguments") and node.expression.arguments:
                        dependency_name = str(node.expression.arguments[0])
                        dependency_uri = find_uri_by_name(dependency_name)
                        if dependency_uri:
                            triples.add((function_uri, EX.hasPrecondition, dependency_uri))

            # --- Function Parameters ---
            for param in function.parameters:
                param_uri = safe_uri(fn_name + "_param_" + param.name)
                name_to_uri[param.name] = param_uri

                param_uri = safe_uri(fn_name + "_param_" + param.name)
                triples.add((function_uri, EX.hasParameter, param_uri))
                triples.add((param_uri, RDF.type, EX.Parameter))
                triples.add((param_uri, EX.hasName, Literal(param.name)))
                triples.add((param_uri, EX.hasType, Literal(param.type)))
                if any(
                    key in param.name.lower() for key in ("amount", "price", "value")
                ):
                    triples.add((param_uri, EX.isMonetaryValue, Literal(True)))

            # --- State variables read/written ---
            for var in function.state_variables_read:
                var_uri = safe_uri(contract.name + "_" + var.name)
                triples.add((function_uri, EX.readsVariable, var_uri))
            for var in function.state_variables_written:
                var_uri = safe_uri(contract.name + "_" + var.name)
                triples.add((function_uri, EX.writesVariable, var_uri))

            # --- Modifiers ---
            for mod in function.modifiers:
                mod_uri = safe_uri(contract.name + "_mod_" + mod.name)
                triples.add((function_uri, EX.hasModifier, mod_uri))

            # --- Events emitted ---
            if hasattr(function, "events_emitted"):
                for event in function.events_emitted:
                    event_uri = safe_uri(contract.name + "_event_" + event.name)
                    triples.add((function_uri, EX.emitsEvent, event_uri))

        # --- Events ---
        for event in contract.events:
            event_uri = safe_uri(contract.name + "_event_" + event.name)
            triples.add((contract_uri, EX.hasEvent, event_uri))
            triples.add((event_uri, RDF.type, EX.Event))
            triples.add((event_uri, EX.hasName, Literal(event.name)))
            for param in event.elems:
                param_uri = safe_uri(event.name + "_param_" + param.name)
                triples.add((event_uri, EX.hasParameter, param_uri))
                triples.add((param_uri, RDF.type, EX.Parameter))
                triples.add((param_uri, EX.hasName, Literal(param.name)))
                triples.add((param_uri, EX.hasType, Literal(param.type)))

        # --- Modifiers ---
        for modifier in contract.modifiers:
            modifier_uri = safe_uri(contract.name + "_mod_" + modifier.name)
            triples.add((contract_uri, EX.hasModifier, modifier_uri))
            triples.add((modifier_uri, RDF.type, EX.Modifier))
            triples.add((modifier_uri, EX.hasName, Literal(modifier.name)))

        # --- Structs ---
        struct_roles = set()
        for struct in contract.structures:
            struct_uri = safe_uri(contract.name + "_struct_" + struct.name)
            triples.add((contract_uri, EX.hasStruct, struct_uri))
            triples.add((struct_uri, RDF.type, EX.Struct))
            triples.add((struct_uri, EX.hasName, Literal(struct.name)))
            struct_roles.add(struct.name)
            for name, elem in struct.elems.items():
                member_uri = safe_uri(struct.name + "_member_" + name)
                triples.add((struct_uri, EX.hasMember, member_uri))
                triples.add((member_uri, RDF.type, EX.Member))
                triples.add((member_uri, EX.hasName, Literal(name)))
                if hasattr(elem.type, "name"):
                    triples.add((member_uri, EX.hasType, Literal(elem.type.name)))
        # --- Emit all discovered roles as subclasses of ex:Role ---
        for role in struct_roles.union(address_roles):
            triples.add((EX[role], RDF.type, OWL.Class))
            triples.add((EX[role], RDFS.subClassOf, EX.Role))

    # --- Extract all classes, functions, and properties directly from the Solidity contract ---
    # For each discovered class, function, or property, generate the corresponding OWL class/property dynamically.
    # For classes whose names match legal concepts (Agreement, Certification, etc.), map to LKIF superclass using pattern matching.
    # Link functions and properties to the classes they belong to.
    # No hardcoded checks for class existence—everything is based on what is parsed from the Solidity contract.

    # Mapping patterns for LKIF concepts
    legal_patterns = {
        'Agreement': URIRef("http://www.estrellaproject.org/lkif-core/legal-action.owl#Agreement"),
        'Certification': URIRef("http://www.estrellaproject.org/lkif-core/legal-action.owl#Certification"),
        'Assignment': URIRef("http://www.estrellaproject.org/lkif-core/legal-action.owl#Assignment"),
        'Revocation': URIRef("http://www.estrellaproject.org/lkif-core/legal-action.owl#Revocation"),
        'Payment': URIRef("http://www.estrellaproject.org/lkif-core/legal-action.owl#Payment"),
        'Transfer': URIRef("http://www.estrellaproject.org/lkif-core/legal-action.owl#Transfer"),
        'Contract': URIRef("http://www.estrellaproject.org/lkif-core/legal-action.owl#Contract"),
        'Legal_Action': URIRef("http://www.estrellaproject.org/lkif-core/legal-action.owl#Legal_Action"),
    }

    # 1. For every class (contract, struct, address-typed variable as role):
    discovered_classes = set()
    for s, p, o in triples:
        if p == RDF.type and o == OWL.Class and isinstance(s, URIRef):
            discovered_classes.add(s)

    for cls in discovered_classes:
        cls_name = str(cls).split("#")[-1]
        # Pattern-based mapping to LKIF
        for pattern, lkif_uri in legal_patterns.items():
            if pattern.lower() in cls_name.lower():
                triples.add((cls, RDFS.subClassOf, lkif_uri))
                triples.add((cls, RDFS.label, Literal(cls_name.replace('_', ' '))))
                break
        else:
            # If not mapped, just add label
            triples.add((cls, RDFS.label, Literal(cls_name.replace('_', ' '))))

    # 2. For every function, create a class for the function and link to its parent contract
    for s, p, o in triples:
        if p == RDF.type and o == EX.Function:
            fn_name = None
            parent_contract = None
            for f_s, f_p, f_o in triples.triples((s, EX.hasName, None)):
                fn_name = str(f_o)
            for f_s, f_p, f_o in triples.triples((None, EX.hasFunction, s)):
                parent_contract = f_s
            if fn_name:
                triples.add((s, RDFS.label, Literal(fn_name)))
            if parent_contract:
                triples.add((s, RDFS.comment, Literal(f"Function of contract {parent_contract.split('#')[-1]}")))

    # 3. For every property (state variable, parameter, struct member), add label and link to parent
    for s, p, o in triples:
        if p == RDF.type and o in [EX.StateVariable, EX.Parameter, EX.Member]:
            prop_name = None
            parent = None
            for f_s, f_p, f_o in triples.triples((s, EX.hasName, None)):
                prop_name = str(f_o)
            # Find parent contract/function/struct
            for f_s, f_p, f_o in triples:
                if f_o == s and f_p in [EX.hasVariable, EX.hasParameter, EX.hasMember]:
                    parent = f_s
            if prop_name:
                triples.add((s, RDFS.label, Literal(prop_name)))
            if parent:
                triples.add((s, RDFS.comment, Literal(f"Property of {parent.split('#')[-1]}")))

    # 4. For payable functions, add equivalence axiom
    for s, p, o in triples:
        if p == RDF.type and o == EX.Function:
            if (s, EX.isPayable, Literal(True)) in triples:
                pf_class = URIRef(str(s) + "_PayableFunction")
                triples.add((pf_class, RDF.type, OWL.Class))
                triples.add((pf_class, OWL.equivalentClass, URIRef("_:PayableFunctionRestriction_" + s.split('#')[-1])))
                triples.add((URIRef("_:PayableFunctionRestriction_" + s.split('#')[-1]), RDF.type, OWL.Restriction))
                triples.add((URIRef("_:PayableFunctionRestriction_" + s.split('#')[-1]), OWL.onProperty, EX.isPayable))
                triples.add((URIRef("_:PayableFunctionRestriction_" + s.split('#')[-1]), OWL.hasValue, Literal(True)))
                triples.add((pf_class, RDFS.label, Literal(f"Payable Function for {s.split('#')[-1]}")))

    # 5. SWRL-like rule comments for assignment/transfer/approval functions (pattern-based)

    # --- [NEW] Αυτόματη παραγωγή domain/range για κάθε property χωρίς hardcoding ---
    from collections import defaultdict
    property_domains = defaultdict(set)
    property_ranges = defaultdict(set)
    # Συλλογή όλων των triples για properties που είναι URIRef και στο EX namespace
    for s, p, o in triples:
        if isinstance(p, URIRef) and str(p).startswith(str(EX)):
            # Βρες το type του subject
            subj_type = None
            for s2, p2, o2 in triples.triples((s, RDF.type, None)):
                subj_type = o2
                break
            # Βρες το type του object (αν είναι URIRef)
            obj_type = None
            if isinstance(o, URIRef):
                for s2, p2, o2 in triples.triples((o, RDF.type, None)):
                    obj_type = o2
                    break
            if subj_type:
                property_domains[p].add(subj_type)
            if obj_type:
                property_ranges[p].add(obj_type)
    # Για κάθε property, γράψε domain/range (χωρίς duplicates)
    for prop in set(property_domains.keys()).union(property_ranges.keys()):
        for dom in property_domains[prop]:
            triples.add((prop, RDFS.domain, dom))
        for rng in property_ranges[prop]:
            triples.add((prop, RDFS.range, rng))

    return triples


@click.command()
@click.argument("filename")
@click.option("--verbose", "-v", count=True)
def main(filename, verbose=False):
    """
    Convert a Solidity file to RDF triples.
    """
    print(f"Converting {filename} to Turtle syntax...")
    try:
        slith = Slither(filename)
        triples = contract_to_triples(slith)
        out = Path(filename).with_suffix(".ttl")
        triples.serialize(destination=out, format="turtle")
        print(f"✅ Turtle file created: {out}")
    except Exception as e:
        if verbose:
            raise
        print(f"❌ Error processing {filename}: {e}")


if __name__ == "__main__":
    main()
