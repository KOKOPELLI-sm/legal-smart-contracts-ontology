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
    # Datatype Properties
    datatype_properties = [
        (EX.hasName, EX.SmartContract, XSD.string),
        (EX.hasName, EX.Function, XSD.string),
        (EX.hasName, EX.StateVariable, XSD.string),
        (EX.hasName, EX.Parameter, XSD.string),
        (EX.hasName, EX.Event, XSD.string),
        (EX.hasName, EX.Modifier, XSD.string),
        (EX.hasName, EX.Struct, XSD.string),
        (EX.hasName, EX.Member, XSD.string),
        (EX.hasType, EX.StateVariable, XSD.string),
        (EX.hasType, EX.Parameter, XSD.string),
        (EX.hasType, EX.Member, XSD.string),
        (EX.hasType, EX.Function, XSD.string),
        (EX.hasVisibility, EX.StateVariable, XSD.string),
        (EX.hasVisibility, EX.Function, XSD.string),
        (EX.isPayable, EX.Function, XSD.boolean),
        (EX.isMonetaryValue, EX.StateVariable, XSD.boolean),
        (EX.isMonetaryValue, EX.Parameter, XSD.boolean),
    ]
    for prop, dom, rng in datatype_properties:
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
        for var in contract.state_variables:
            var_uri = safe_uri(contract.name + "_" + var.name)
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

        # --- Functions ---
        for function in contract.functions_declared:
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

            # --- Function Parameters ---
            for param in function.parameters:
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
        for struct in contract.structures:
            struct_uri = safe_uri(contract.name + "_struct_" + struct.name)
            triples.add((contract_uri, EX.hasStruct, struct_uri))
            triples.add((struct_uri, RDF.type, EX.Struct))
            triples.add((struct_uri, EX.hasName, Literal(struct.name)))
            for name, elem in struct.elems.items():
                member_uri = safe_uri(struct.name + "_member_" + name)
                triples.add((struct_uri, EX.hasMember, member_uri))
                triples.add((member_uri, RDF.type, EX.Member))
                triples.add((member_uri, EX.hasName, Literal(name)))
                if hasattr(elem.type, "name"):
                    triples.add((member_uri, EX.hasType, Literal(elem.type.name)))

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
