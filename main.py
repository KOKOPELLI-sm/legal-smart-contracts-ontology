import click
from rdflib import Graph, Namespace, URIRef, Literal, RDF
from slither.slither import Slither

@click.command()
@click.argument("filename")
def main(filename):
    print(f"converting {filename} to turtle syntax")
    slither = Slither(filename)
    triples = set()
    for contract in slither.contracts:
        triples.add((contract.name, "rdf:type", "SmartContract"))
        for function in contract.functions_declared:
            triples.add((contract.name, "hasFunction", function.name))
        for var in contract.state_variables:
            triples.add((contract.name, "hasVariable", var.name))
    print("creating triples from solidity contract")
    
    for triple in sorted(triples):
        print(triple)

    #with open("triples_output.txt", "w", encoding="utf-8") as f:
    #    for triple in sorted(triples):
    #        f.write(f"{triple}\n")


    EX= Namespace("http://example.org/smartcontracts")
    g= Graph ()
    g.bind ("ex", EX)
    g.bind ("rdf",RDF)

    for subj, pred, obj in triples:
        subject_uri = EX[subj]
        predicate_uri= EX[pred] if not pred.startswith("rdf:")else RDF.type 
        object_value = EX [obj] if pred != "rdf:type" else EX[obj]
        g.add ((subject_uri, predicate_uri, object_value))

    g.serialize (destination=f"{filename}.ttl", format="turtle")
    print(f"✅ File {filename}.ttl was created")

if __name__ == "__main__":
    main()
