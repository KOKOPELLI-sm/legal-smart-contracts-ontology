from rdflib import Graph, Namespace, URIRef, Literal, RDF
triples = [
    ('SmartLeaseContract', 'hasFunction', 'assignTenant'),
    ('SmartLeaseContract', 'hasFunction', 'constructor'),
    ('SmartLeaseContract', 'hasFunction', 'isSameString'),
    ('SmartLeaseContract', 'hasFunction', 'payDeposit'),
    ('SmartLeaseContract', 'hasFunction', 'proposeWrittenContract'),
    ('SmartLeaseContract', 'hasFunction', 'signContract'),
    ('SmartLeaseContract', 'hasFunction', 'slitherConstructorVariables'),
    ('SmartLeaseContract', 'hasVariable', 'TENANT_CAPACITY'),
    ('SmartLeaseContract', 'hasVariable', 'addressToTenant'),
    ('SmartLeaseContract', 'hasVariable', 'deposit'),
    ('SmartLeaseContract', 'hasVariable', 'landlordAddress'),
    ('SmartLeaseContract', 'hasVariable', 'tenantOccupancy'),
    ('SmartLeaseContract', 'hasVariable', 'tenants'),
    ('SmartLeaseRegistry', 'hasFunction', 'createLease'),
    ('SmartLeaseRegistry', 'hasFunction', 'getLeases'),
    ('SmartLeaseRegistry', 'hasFunction', 'getNumLeases'),
    ('SmartLeaseRegistry', 'hasVariable', 'contracts'),
    ('SmartLeaseRegistry', 'rdf:type', 'SmartContract')]
EX= Namespace("http://example.org/smartlease#")
g= Graph ()
g.bind ("ex", EX)
g.bind ("rdf",RDF)

for subj, pred, obj in triples:
    subject_uri = EX[subj]
    predicate_uri= EX[pred] if not pred.startswith("rdf:")else RDF.type 
    object_value = EX [obj] if pred != "rdf:type" else EX[obj]
    g.add ((subject_uri, predicate_uri, object_value))

g.serialize (destination="triples_output.ttl", format="turtle")
print("✅ Το αρχείο triples_output.ttl δημιουργήθηκε.")

