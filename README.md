# legal-smart-contracts-ontology

Create an RDF ontology using Turtle syntax from a smart contract written in
Solidity.

## Usage

Install `uv` from https://docs.astral.sh/uv/getting-started/installation/. Then,
install the project and its dependencies:

```
uv sync
```

Install version 0.5.0 of the Solidity compiler, and set it as the default
version globally:

```
uv run solc-select install 0.5.0
uv run solc-select use 0.5.0
```

Run the `extract_entities.py` script and verify that it works:

```
uv run python extract_entities.py
```
