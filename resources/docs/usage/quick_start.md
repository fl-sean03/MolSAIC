# Quick Start Guide

This guide helps you quickly get started with MONET, covering the essential functionality for molecular data manipulation.

## Installation

```bash
# From PyPI (recommended)
pip install monet-toolkit

# From source
git clone https://github.com/molsim-lab/monet.git
cd monet
pip install -e .
```

## Basic Usage

### Loading and Parsing Files

```python
from src.parsers.car_parser import CARParser
from src.parsers.mdf_parser import MDFParser

# Parse files
car_parser = CARParser("path/to/molecule.car")
mdf_parser = MDFParser("path/to/molecule.mdf")

car_data = car_parser.parse()
mdf_data = mdf_parser.parse()

# Create system from parsed data
from src.models.system import MolecularSystem
system = MolecularSystem.from_parsed_data(car_data, mdf_data)

# Print basic information
print(f"System name: {system.name}")
print(f"Number of molecules: {len(system.molecules)}")
print(f"Number of atoms: {sum(len(mol.atoms) for mol in system.molecules)}")
```

### Using the Pipeline API

The recommended way to use MONET is through the pipeline API, which provides a clean, chainable interface:

```python
from src.pipeline import MolecularPipeline

# Create a pipeline and chain operations
(MolecularPipeline()
    .load("path/to/molecule.car", "path/to/molecule.mdf")
    .update_ff_types("path/to/mapping.json")
    .update_charges("path/to/charge_mapping.json")
    .generate_grid(grid_dims=(2, 2, 2), gap=2.0)
    .save("output.car", "output.mdf", "MOL"))
```

### Command Line Interface

MONET also provides a command-line interface for common operations:

```bash
# Grid replication
python -m src.cli grid --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output-mdf grid_box.mdf --output-car grid_box.car

# Force-field update
python -m src.cli update-ff --car input.car --output-car updated.car --mapping mapping.json

# Charge update
python -m src.cli update-charges --mdf input.mdf --output-mdf updated.mdf --mapping charge_mapping.json
```

## Next Steps

- Check the [examples](../../examples/) directory for more detailed examples
- Read the [API documentation](../api/index.md) for full reference
- See the [tutorials](../tutorials/) for step-by-step guides
