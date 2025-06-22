# legal-smart-contracts-ontology

Create an RDF ontology using Turtle syntax from a smart contract written in
Solidity.

## Usage

Install `uv` from https://docs.astral.sh/uv/getting-started/installation/. For
example, on Windows, you can install it with:

```
pipx install uv
```

Then, install the project and its dependencies:

```
uv sync
```

The rest of the commands assume you're running on the virtual environment for
the project (e.g., with `uv run`).

Install version 0.5.0 of the Solidity compiler, and set it as the default
version globally:

```
solc-select install 0.5.0
solc-select use 0.5.0
```

Run the `extract_entities.py` script and verify that it works:

```
python extract_entities.py
```
