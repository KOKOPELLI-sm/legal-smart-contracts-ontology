import click
from pathlib import Path
from slither.slither import Slither
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF
from urllib.parse import quote

EX = Namespace("http://example.org/smartcontracts#")

def safe_uri(name):
    return URIRef(EX[quote(name.replace(" ", "_"))])

def contract_to_triples(slith):
    triples = Graph()
    triples.bind("ex", EX)

    for contract in slith.contracts:
        contract_uri = safe_uri(contract.name)
        triples.add((contract_uri, RDF.type, EX.SmartContract))
        triples.add((contract_uri, EX.hasName, Literal(contract.name)))

        # Inheritance
        for base in contract.inheritance:
            base_uri = safe_uri(base.name)
            triples.add((contract_uri, EX.inheritsFrom, base_uri))
            if hasattr(base, 'is_library') and base.is_library:
                triples.add((base_uri, RDF.type, EX.LibraryContract))

        # State variables
        for var in contract.state_variables:
            var_uri = safe_uri(contract.name + "_" + var.name)
            triples.add((contract_uri, EX.hasVariable, var_uri))
            triples.add((var_uri, RDF.type, EX.StateVariable))
            triples.add((var_uri, EX.hasName, Literal(var.name)))

            var_type_str = str(var.type)
            triples.add((var_uri, EX.hasType, Literal(var_type_str)))
            triples.add((var_uri, EX.hasVisibility, Literal(var.visibility)))

            if "mapping" in var_type_str.lower():
                triples.add((var_uri, RDF.type, EX.MappingVariable))
            elif var_type_str.endswith("[]"):
                triples.add((var_uri, RDF.type, EX.ArrayVariable))

        # Functions
        for function in contract.functions_declared:
            fn_name = contract.name + "_" + function.full_name.replace("(", "_").replace(")", "").replace(",", "_")
            function_uri = safe_uri(fn_name)
            triples.add((contract_uri, EX.hasFunction, function_uri))
            triples.add((function_uri, RDF.type, EX.Function))
            triples.add((function_uri, EX.hasName, Literal(function.name)))
            triples.add((function_uri, EX.hasVisibility, Literal(function.visibility)))

            # Parameters
            for param in function.parameters:
                param_uri = safe_uri(fn_name + "_param_" + param.name)
                triples.add((function_uri, EX.hasParameter, param_uri))
                triples.add((param_uri, RDF.type, EX.Parameter))
                triples.add((param_uri, EX.hasName, Literal(param.name)))
                triples.add((param_uri, EX.hasType, Literal(param.type)))
                if any(key in param.name.lower() for key in ("amount", "price", "value")):
                    triples.add((param_uri, EX.isMonetaryValue, Literal(True)))

            # Read/write state variables
            for var in function.state_variables_read:
                var_uri = safe_uri(contract.name + "_" + var.name)
                triples.add((function_uri, EX.readsVariable, var_uri))
            for var in function.state_variables_written:
                var_uri = safe_uri(contract.name + "_" + var.name)
                triples.add((function_uri, EX.writesVariable, var_uri))

            # Modifiers
            for mod in function.modifiers:
                mod_uri = safe_uri(contract.name + "_mod_" + mod.name)
                triples.add((function_uri, EX.hasModifier, mod_uri))

            # Events emitted
            if hasattr(function, "events_emitted"):
                for event in function.events_emitted:
                    event_uri = safe_uri(contract.name + "_event_" + event.name)
                    triples.add((function_uri, EX.emitsEvent, event_uri))

        # Events
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

        # Modifiers
        for modifier in contract.modifiers:
            modifier_uri = safe_uri(contract.name + "_mod_" + modifier.name)
            triples.add((contract_uri, EX.hasModifier, modifier_uri))
            triples.add((modifier_uri, RDF.type, EX.Modifier))
            triples.add((modifier_uri, EX.hasName, Literal(modifier.name)))

        # Structs
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
                triples.add((member_uri, EX.hasType, Literal(elem.type.name)))

    return triples

@click.command()
@click.argument("filename")
def main(filename):
    print(f"Converting {filename} to Turtle syntax...")
    try:
        slith = Slither(filename)
        triples = contract_to_triples(slith)
        out = Path(filename).with_suffix(".ttl")
        triples.serialize(destination=out, format="turtle")
        print(f"✅ Turtle file created: {out}")
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")

if __name__ == "__main__":
    main()