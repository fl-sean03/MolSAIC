# MolSAIC (Molecular Structure Analysis and Integration Console)

MolSAIC is a comprehensive molecular toolkit for processing molecular data files (MDF, CAR, PDB) that supports tasks such as grid replication, force-field updates, and charge corrections.

## Features

- Parse and write MDF (Materials Studio Molecular Data Format) and CAR (Coordinate Archive) files
- Generate grid replications of molecules with customizable spacing
- Update force-field types based on charge and element mapping
- Update atomic charges based on force-field type mapping
- Convert to NAMD format (PDB/PSF) using external tools integration
- Process PDB files (experimental)
- Object-oriented design with Atom, Molecule, and System classes
- Pipeline architecture for chaining multiple transformations
- Object-based API approach (default) with legacy file-based support (deprecated)
- Command-line interface for common operations
- External tools integration framework for third-party executables

## Installation

```bash
# Clone the repository
git clone https://github.com/molsim-lab/molsaic.git

# Navigate to the directory
cd molsaic

# Install the package
pip install -e .
```

## Usage

### Command Line Interface

MolSAIC provides a CLI with several subcommands using a modern, modular architecture:

#### Grid Replication

Replicate a template molecule in a 3D grid:

```bash
python -m src.cli grid --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output-mdf grid_box.mdf --output-car grid_box.car
```

This creates an 8×8×8 grid of molecules with a 2.0 Å gap between them.

#### Force-Field Type Updates

Update force-field types based on a mapping file:

```bash
python -m src.cli update-ff --mdf input.mdf --car input.car --output-mdf updated.mdf --output-car updated.car --mapping mapping.json
```

The mapping file should be a JSON file with keys in the format `"(charge, element)"` and values as the new force-field type:

```json
{
  "(-0.27, C)": "CT3",
  "(0.09, H)": "HA3"
}
```

#### Charge Updates

Update atomic charges based on a force-field type mapping:

```bash
python -m src.cli update-charges --mdf input.mdf --car input.car --output-mdf updated.mdf --output-car updated.car --mapping charge_mapping.json
```

The mapping file should be a JSON file mapping force-field types to charges:

```json
{
  "CT3": -0.27,
  "HA3": 0.09
}
```

#### MSI2NAMD Conversion

Convert Material Studio files to NAMD format (PDB/PSF) using the MSI2NAMD external tool:

```bash
python -m src.cli msi2namd --mdf input.mdf --car input.car --output-dir namd_output --residue-name MOL --parameter-file params.prm
```

**Note**: The `--parameter-file` option is required for MSI2NAMD conversion.

#### Packmol Integration

Work with Packmol input files for molecular packing:

```bash
# Parse and print Packmol configuration as JSON
python -m src.cli packmol --input-file system.inp --print-json

# Generate a new input file with updates from a JSON file
python -m src.cli packmol --input-file system.inp --update-file updates.json --output-file modified.inp

# Execute Packmol with an input file
python -m src.cli packmol --input-file system.inp --execute

# Generate a new input file with updates and execute Packmol
python -m src.cli packmol --input-file system.inp --update-file updates.json --output-file modified.inp --execute
```

Additional Packmol options:
- `--timeout`: Timeout in seconds for Packmol execution (default: 900 seconds)
- `--continue-on-timeout`: Continue execution if timeout occurs and use partial results if available
- `--continue-on-error`: Continue execution even if Packmol fails

Global options for all commands:
- `--keep`: Keep all artifacts after completion (logs and workspaces)
- `--keep-logs`: Keep only logs after completion (cleanup workspaces)
- `--charge-groups`: Include charge groups in conversion (for MSI2NAMD)

#### Processing Modes

MolSAIC uses the object-based pipeline architecture by default. This approach has several advantages:
- No intermediate files required for chained operations
- Better memory efficiency
- Debug mode for intermediate outputs

For example:
```bash
python -m src.cli grid --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output-mdf grid_box.mdf --output-car grid_box.car
```

You can enable debug output for intermediate steps with the `--debug-output` flag:

```bash
python -m src.cli update-ff --debug-output --debug-prefix "debug_" --mdf input.mdf --car input.car --output-mdf output.mdf --output-car output.car --mapping mapping.json
```

**Note**: The object-based mode requires both `--mdf` and `--car` parameters when loading data.

### Python API

#### Object-Based Pipeline API (Default)

The recommended pipeline API allows chaining multiple transformations:

```python
from src.pipeline import MolecularPipeline

# Chain all operations in a fluent API
(MolecularPipeline()
    .load('molecule.car', 'molecule.mdf')
    .update_ff_types('ff_mapping.json')
    .update_charges('charge_mapping.json')
    .generate_grid(grid_dims=(8, 8, 8), gap=2.0)
    .save('output.car', 'output.mdf', 'MOL'))

# Convert to NAMD format using MSI2NAMD
(MolecularPipeline()
    .load('molecule.car', 'molecule.mdf')
    .msi2namd(
        output_dir='namd_output',
        residue_name='MOL',
        parameter_file='params.prm',  # Required
        charge_groups=False,
        cleanup_workspace=True
    ))
```

#### External Tools API

The external tools API provides programmatic access to external tools like Packmol:

```python
from src.external_tools import PackmolTool

# Initialize Packmol tool
packmol = PackmolTool()

# Parse existing Packmol input file
config = packmol.parse_packmol_file("input.inp")

# Update configuration
config["global"]["tolerance"] = ["2.5"]  # Change tolerance
config["structures"][0]["properties"]["number"] = ["50"]  # Change molecule count

# Generate new input file
packmol.generate_packmol_file(config, "updated.inp")

# Execute Packmol
result = packmol.execute(input_file="updated.inp")
output_file = result.get("output_file")  # Get path to output file

# Or use with configuration updates in one step
updates = {
    "global": {"tolerance": ["3.0"]},
    "structures": [{"properties": {"number": ["100"]}}]
}
result = packmol.execute(
    input_file="input.inp",
    update_dict=updates,
    output_file="modified.inp"
)
```
```

For debugging intermediate steps:

```python
# Enable debug mode with prefix
pipeline = MolecularPipeline(debug=True, debug_prefix="debug_")

# Each step saves intermediate files with the debug prefix
pipeline.load('molecule.car', 'molecule.mdf')
pipeline.update_ff_types('ff_mapping.json')  # Creates debug_1_*.car/mdf
pipeline.update_charges('charge_mapping.json')  # Creates debug_2_*.car/mdf
pipeline.generate_grid(grid_dims=(8, 8, 8), gap=2.0)  # Creates debug_3_*.car/mdf
pipeline.save('output.car', 'output.mdf')
```

#### Migration Guide

A detailed guide for migrating from the deprecated file-based API to the recommended object-based API is available in the [Migration Guide](docs/tutorials/migration_guide.md).

Quick example:
```python
# OLD (deprecated):
from src.transformers.legacy.grid import generate_grid_files
generate_grid_files(car_file="in.car", mdf_file="in.mdf", output_car="out.car", output_mdf="out.mdf")

# NEW (recommended):
from src.pipeline import MolecularPipeline
pipeline = MolecularPipeline()
pipeline.load("in.car", "in.mdf").generate_grid().save("out.car", "out.mdf")
```

## File Format Support

MolSAIC supports the following file formats:

- **MDF** (Materials Studio Molecular Data Format): Contains force-field information and connectivity data
- **CAR** (Materials Studio Coordinate Archive): Contains atomic coordinates and molecule structure
- **PDB** (Protein Data Bank): Contains protein structure data (experimental support)

## Repository Structure

```
molsaic/
├── resources/                   # Resources, testing and examples
│   ├── architecture/            # Architecture documentation
│   ├── benchmarks/              # Performance benchmarking scripts
│   │   └── profiles/            # Profiling scripts
│   ├── data/                    # Test data files
│   │   ├── molecules/           # Molecular structure files
│   │   │   ├── 1NEC/            # Single molecule test data
│   │   │   └── 3NEC/            # Multi-molecule test data
│   │   └── mappings/            # Mapping files for testing
│   ├── examples/                # Example scripts
│   │   ├── advanced/            # Advanced usage examples
│   │   ├── basic/               # Basic usage examples
│   │   ├── docs/                # Example documentation
│   │   ├── legacy/              # Legacy approach examples
│   │   └── tutorials/           # Tutorial code and documentation
│   │       └── docs/            # Tutorial guides
│   ├── tests/                   # Test suite
│   │   ├── unit/                # Unit tests
│   │   ├── integration/         # Integration tests
│   │   └── standalone/          # Standalone test scripts
│   └── usage/                   # Usage guides and quick start
├── src/                         # Main package
│   ├── docs/                    # API documentation
│   │   └── api/                 # API reference
│   ├── models/                  # Data models
│   ├── parsers/                 # File parsers
│   ├── writers/                 # File writers
│   ├── transformers/            # Transformations
│   │   └── legacy/              # Legacy implementations
│   ├── external_tools/          # External tool integrations
│   └── templates/               # Pipeline templates
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

### Development Setup

1. Clone the repository
```bash
git clone https://github.com/molsim-lab/molsaic.git
cd molsaic
```

2. Install in development mode
```bash
pip install -e .
```

3. Run the tests
```bash
python run_tests.py
```

4. Set up the pre-commit hook
```bash
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Acknowledgments

- This package was developed to support research in computational chemistry and materials science.
