from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal

g = Graph()
g.parse("triples_output.ttl", format="turtle")  # Ενημέρωσε διαδρομή αν άλλαξε

# Ορισμός βασικών namespaces
EX = Namespace("http://example.org/smartlease#")
EX1 = Namespace("http://example.org/ontology#")
g.bind("ex", EX)
g.bind("ex1", EX1)
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)
g.bind("owl", OWL)

# Οντολογικές κλάσεις
g.add((EX1.SmartContract, RDF.type, OWL.Class))
g.add((EX1.Function, RDF.type, OWL.Class))
g.add((EX1.Variable, RDF.type, OWL.Class))
g.add((EX1.LegalInstrument, RDF.type, OWL.Class))
g.add((EX1.LegalEntity, RDF.type, OWL.Class))
g.add((EX1.Tenant, RDFS.subClassOf, EX1.LegalEntity))
g.add((EX1.Landlord, RDFS.subClassOf, EX1.LegalEntity))
g.add((EX1.LeaseAgreement, RDF.type, OWL.Class))
g.add((EX1.SecurityDeposit, RDF.type, OWL.Class))
g.add((EX1.Signature, RDF.type, OWL.Class))
g.add((EX1.Assignment, RDF.type, OWL.Class))
g.add((EX.IPFSDocument, RDF.type, OWL.Class))




# Ιδιότητες
g.add((EX1.hasFunction, RDF.type, OWL.ObjectProperty))
g.add((EX1.hasFunction, RDFS.domain, EX1.SmartContract))
g.add((EX1.hasFunction, RDFS.range, EX1.Function))

g.add((EX1.hasVariable, RDF.type, OWL.ObjectProperty))
g.add((EX1.hasVariable, RDFS.domain, EX1.SmartContract))
g.add((EX1.hasVariable, RDFS.range, EX1.Variable))

g.add((EX1.hasParty, RDF.type, OWL.ObjectProperty))
g.add((EX1.hasParty, RDFS.domain, EX1.LegalInstrument))
g.add((EX1.hasParty, RDFS.range, EX1.LegalEntity))

g.add((EX1.hasSecurityDeposit, RDF.type, OWL.ObjectProperty))
g.add((EX1.hasSecurityDeposit, RDFS.domain, EX1.LeaseAgreement))
g.add((EX1.hasSecurityDeposit, RDFS.range, EX1.SecurityDeposit))

g.add((EX1.hasSignature, RDF.type, OWL.ObjectProperty))
g.add((EX1.hasSignature, RDFS.domain, EX1.LeaseAgreement))
g.add((EX1.hasSignature, RDFS.range, EX1.Signature))

g.add((EX1.assigns, RDF.type, OWL.ObjectProperty))
g.add((EX1.assigns, RDFS.domain, EX1.Landlord))
g.add((EX1.assigns, RDFS.range, EX1.Assignment))

g.add((EX1.isAssignedTo, RDF.type, OWL.ObjectProperty))
g.add((EX1.isAssignedTo, RDFS.domain, EX1.Assignment))
g.add((EX1.isAssignedTo, RDFS.range, EX1.Tenant))

g.add((EX1.relatesToAgreement, RDF.type, OWL.ObjectProperty))
g.add((EX1.relatesToAgreement, RDFS.domain, EX1.Assignment))
g.add((EX1.relatesToAgreement, RDFS.range, EX1.LeaseAgreement))

g.add((EX.hasWrittenAgreement, RDF.type, OWL.ObjectProperty))
g.add((EX.hasWrittenAgreement, RDFS.domain, EX.LeaseAgreement))
g.add((EX.hasWrittenAgreement, RDFS.range, EX.IPFSDocument))


# Περιγραφές (με άρθρα ΑΚ)
g.add((EX1.LegalInstrument, RDFS.comment, Literal("Νομικό μέσο με δεσμευτική ισχύ, όπως ένα smart contract. Βλ. άρθρο 361 ΑΚ για τη σύμβαση ως συμφωνία.")))
g.add((EX1.LeaseAgreement, RDFS.comment, Literal("Σύμβαση μίσθωσης σύμφωνα με τα άρθρα 574 επ. ΑΚ.")))
g.add((EX1.SecurityDeposit, RDFS.comment, Literal("Εγγύηση από τον μισθωτή για την εξασφάλιση υποχρεώσεων. Βλ. άρθρα 361, 625 ΑΚ.")))
g.add((EX1.Signature, RDFS.comment, Literal("Δήλωση αποδοχής σύμβασης. Άρθρο 361 ΑΚ.")))
g.add((EX1.Assignment, RDFS.comment, Literal("Ανάθεση σύμβασης μίσθωσης. Βλ. άρθρο 593 ΑΚ.")))
g.add((EX.IPFSDocument, RDFS.comment, Literal("Ψηφιακό έγγραφο συμβολαίου αποθηκευμένο στο IPFS. Χρησιμοποιείται ως το πλήρες κείμενο της συμφωνίας. Συνδέεται με το άρθρο 361 ΑΚ (σύμβαση) και άρθρο 159 ΑΚ (έγγραφη μορφή).")))

# Αποθήκευση
g.serialize("annotated_triples.ttl", format="turtle")
print("✅ RDF εμπλουτισμένο αρχείο αποθηκεύτηκε ως annotated_triples.ttl")
