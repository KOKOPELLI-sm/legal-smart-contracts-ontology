from slither.slither import Slither
slither=Slither("SmartLease_Full_Compact.sol")
triples=set()
for contract in slither.contracts: 
    triples.add((contract.name, "rdf:type", "SmartContract"))
    for function in contract.functions_declared: 
        triples.add ((contract.name,"hasFunction", function.name))
    for var in contract.state_variables:
            triples.add((contract.name,"hasVariable", var.name))
    
for triple in sorted (triples):
        print (triple)

with open("triples_output.txt","w",encoding="utf-8") as f:
      for triple in sorted (triples):
             f.write(f"{triple}\n")