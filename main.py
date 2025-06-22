import click
from pathlib import Path
from slither.slither import Slither
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF

EX = Namespace("http://example.org/smartcontracts")


def contract_to_triples(slith):
    triples = Graph()
    for contract in slith.contracts:
        contract_uri = URIRef(EX[contract.name])
        triples.add((contract_uri, RDF.type, EX.SmartContract))

        # Add contract-level information
        triples.add((contract_uri, EX.hasName, Literal(contract.name)))

        # Iterate through functions declared in the contract
        for function in contract.functions_declared:
            function_uri = URIRef(EX[function.name])
            triples.add((contract_uri, EX.hasFunction, function_uri))
            triples.add((function_uri, RDF.type, EX.Function))
            triples.add((function_uri, EX.hasName, Literal(function.name)))
            triples.add((function_uri, EX.hasVisibility, Literal(function.visibility)))

            # Add parameters of the function
            for param in function.parameters:
                param_uri = URIRef(EX[param.name])
                triples.add((function_uri, EX.hasParameter, param_uri))
                triples.add((param_uri, RDF.type, EX.Parameter))
                triples.add((param_uri, EX.hasName, Literal(param.name)))
                triples.add((param_uri, EX.hasType, Literal(param.type)))

        # Iterate through state variables
        for var in contract.state_variables:
            var_uri = URIRef(EX[var.name])
            triples.add((contract_uri, EX.hasVariable, var_uri))
            triples.add((var_uri, RDF.type, EX.StateVariable))
            triples.add((var_uri, EX.hasName, Literal(var.name)))
            triples.add((var_uri, EX.hasType, Literal(var.type)))
            triples.add((var_uri, EX.hasVisibility, Literal(var.visibility)))

        # Iterate through events
        for event in contract.events:
            event_uri = URIRef(EX[event.name])
            triples.add((contract_uri, EX.hasEvent, event_uri))
            triples.add((event_uri, RDF.type, EX.Event))
            triples.add((event_uri, EX.hasName, Literal(event.name)))

            # Add parameters of the event
            for param in event.elems:
                param_uri = URIRef(EX[param.name])
                triples.add((event_uri, EX.hasParameter, param_uri))
                triples.add((param_uri, RDF.type, EX.Parameter))
                triples.add((param_uri, EX.hasName, Literal(param.name)))
                triples.add((param_uri, EX.hasType, Literal(param.type)))

        # Iterate through modifiers
        for modifier in contract.modifiers:
            modifier_uri = URIRef(EX[modifier.name])
            triples.add((contract_uri, EX.hasModifier, modifier_uri))
            triples.add((modifier_uri, RDF.type, EX.Modifier))
            triples.add((modifier_uri, EX.hasName, Literal(modifier.name)))

        # Iterate through structs
        for struct in contract.structures:
            struct_uri = URIRef(EX[struct.name])
            triples.add((contract_uri, EX.hasStruct, struct_uri))
            triples.add((struct_uri, RDF.type, EX.Struct))
            triples.add((struct_uri, EX.hasName, Literal(struct.name)))

            # Add members of the struct
            for name, elem in struct.elems.items():
                member_uri = URIRef(EX[name])
                triples.add((struct_uri, EX.hasMember, member_uri))
                triples.add((member_uri, RDF.type, EX.Member))
                triples.add((member_uri, EX.hasName, Literal(name)))
                triples.add((member_uri, EX.hasType, Literal(elem.type.name)))

    return triples


@click.command()
@click.argument("filename")
def main(filename):
    print(f"converting {filename} to turtle syntax")
    out = Path(filename).with_suffix(".ttl")
    triples = contract_to_triples(Slither(filename))
    triples.serialize(destination=out, format="turtle")
    print(f"✅ File {out} was created")


if __name__ == "__main__":
    main()
