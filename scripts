from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal

# Φορτώνουμε τις RDF τριάδες από το προηγούμενο στάδιο
g = Graph()
g.parse("triples_output.ttl", format="ttl")

# Ορισμός βασικών namespaces
EX = Namespace("https://github.com/KOKOPELLI-sm/legal-smart-contracts-ontology.git")
g.bind("ex", EX)
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)
g.bind("owl", OWL)

# --- ΟΝΤΟΛΟΓΙΚΗ ΔΟΜΗ ---

# Κλάσεις

# Smart Contracts
g.add((EX.SmartContract, RDF.type, OWL.Class))
g.add((EX.SmartContract, RDFS.subClassOf, EX.LegalInstrument))
g.add((EX.LegalInstrument, RDF.type, OWL.Class))
g.add((EX.LegalInstrument, RDFS.comment, Literal("Νομικό μέσο με δεσμευτική ισχύ, όπως ένα smart contract. Βλ. άρθρο 361 ΑΚ για τη σύμβαση ως συμφωνία.")))

# Συμβαλλόμενα μέρη
g.add((EX.LegalEntity, RDF.type, OWL.Class))
g.add((EX.Landlord, RDFS.subClassOf, EX.LegalEntity))
g.add((EX.Tenant, RDFS.subClassOf, EX.LegalEntity))

# Αρχείο IPFS
g.add((EX.IPFSDocument, RDF.type, OWL.Class))
g.add((EX.IPFSDocument, RDFS.comment, Literal(
    "Ψηφιακό έγγραφο συμβολαίου αποθηκευμένο στο IPFS. Χρησιμοποιείται ως το πλήρες κείμενο της συμφωνίας. Συνδέεται με το άρθρο 361 ΑΚ (σύμβαση) και άρθρο 159 ΑΚ (έγγραφη μορφή)."
)))


# Χαρακτηριστικά

g.add((EX.Function, RDF.type, OWL.Class))
g.add((EX.Variable, RDF.type, OWL.Class))

# Ιδιότητες (ObjectProperties)

g.add((EX.hasFunction, RDF.type, OWL.ObjectProperty))
g.add((EX.hasFunction, RDFS.domain, EX.SmartContract))
g.add((EX.hasFunction, RDFS.range, EX.Function))

g.add((EX.hasVariable, RDF.type, OWL.ObjectProperty))
g.add((EX.hasVariable, RDFS.domain, EX.SmartContract))
g.add((EX.hasVariable, RDFS.range, EX.Variable))

g.add((EX.hasParty, RDF.type, OWL.ObjectProperty))
g.add((EX.hasParty, RDFS.domain, EX.LegalInstrument))
g.add((EX.hasParty, RDFS.range, EX.LegalEntity))

g.add((EX.hasWrittenAgreement, RDF.type, OWL.ObjectProperty))
g.add((EX.hasWrittenAgreement, RDFS.domain, EX.LeaseAgreement))
g.add((EX.hasWrittenAgreement, RDFS.range, EX.IPFSDocument))


# Συγκεκριμένοι νομικοί όροι

# Σύμβαση μίσθωσης

g.add((EX.LeaseAgreement, RDF.type, OWL.Class))
g.add((EX.LeaseAgreement, RDFS.comment, Literal("Σύμβαση μίσθωσης σύμφωνα με τα άρθρα 574 επ. ΑΚ. Ορίζει τις υποχρεώσεις εκμισθωτή και μισθωτή.")))

# Εγγύηση

g.add((EX.SecurityDeposit, RDF.type, OWL.Class))
g.add((EX.hasSecurityDeposit, RDF.type, OWL.ObjectProperty))
g.add((EX.hasSecurityDeposit, RDFS.domain, EX.LeaseAgreement))
g.add((EX.hasSecurityDeposit, RDFS.range, EX.SecurityDeposit))
g.add((EX.SecurityDeposit, RDFS.comment, Literal("Εγγύηση καταβαλλόμενη από τον μισθωτή, τυπικά βάσει ελεύθερης συμφωνίας, για την εξασφάλιση υποχρεώσεων. Βλ. άρθρα 361, 625 ΑΚ.")))

# Υπογραφή

g.add((EX.Signature, RDF.type, OWL.Class))
g.add((EX.hasSignature, RDF.type, OWL.ObjectProperty))
g.add((EX.hasSignature, RDFS.domain, EX.LeaseAgreement))
g.add((EX.hasSignature, RDFS.range, EX.Signature))
g.add((EX.Signature, RDFS.comment, Literal("Η δήλωση βούλησης αποδοχής της σύμβασης από ένα μέρος. Σχετίζεται με το άρθρο 361 ΑΚ περί σύναψης της σύμβασης.")))

# Ανάθεση (assignment)
g.add((EX.Assignment, RDF.type, OWL.Class))
g.add((EX.Assignment, RDFS.label, Literal("Assignment of lease agreement to tenant")))
g.add((EX.Assignment, RDFS.comment, Literal("Η ανάθεση σύμβασης μίσθωσης αποτελεί δήλωση αποδοχής από τον εκμισθωτή (άρθρο 593 ΑΚ), με την οποία συνάπτεται το μισθωτικό δικαίωμα στον επιλεγμένο μισθωτή.")))

g.add((EX.assigns, RDF.type, OWL.ObjectProperty))
g.add((EX.assigns, RDFS.domain, EX.Landlord))
g.add((EX.assigns, RDFS.range, EX.Assignment))

g.add((EX.isAssignedTo, RDF.type, OWL.ObjectProperty))
g.add((EX.isAssignedTo, RDFS.domain, EX.Assignment))
g.add((EX.isAssignedTo, RDFS.range, EX.Tenant))

g.add((EX.relatesToAgreement, RDF.type, OWL.ObjectProperty))
g.add((EX.relatesToAgreement, RDFS.domain, EX.Assignment))
g.add((EX.relatesToAgreement, RDFS.range, EX.LeaseAgreement))

# Αποθήκευση

g.serialize("annotated_triples.ttl", format="turtle")
print("✅ RDF αρχείο εμπλουτίστηκε και αποθηκεύτηκε ως annotated_triples.ttl")
