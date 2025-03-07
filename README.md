# MONET (MOlecular NEtwork Toolkit)

MONET is a comprehensive molecular toolkit for processing molecular data files (MDF, CAR, PDB) that supports tasks such as grid replication, force-field updates, and charge corrections.

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
git clone https://github.com/molsim-lab/monet.git

# Navigate to the directory
cd monet

# Install the package
pip install -e .
```

## Usage

### Command Line Interface

MONET provides a CLI with several subcommands:

#### Grid Replication

Replicate a template molecule in a 3D grid:

```bash
python -m src.cli grid --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output-mdf grid_box.mdf --output-car grid_box.car
```

This creates an 8×8×8 grid of molecules with a 2.0 Å gap between them.

#### Force-Field Type Updates

Update force-field types based on a mapping file:

```bash
python -m src.cli update-ff --car input.car --output-car updated.car --mapping mapping.json
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
python -m src.cli update-charges --mdf input.mdf --output-mdf updated.mdf --mapping charge_mapping.json
```

The mapping file should be a JSON file mapping force-field types to charges:

```json
{
  "CT3": -0.27,
  "HA3": 0.09
}
```

#### NAMD Conversion

Convert Material Studio files to NAMD format (PDB/PSF) using the MSI2NAMD external tool:

```bash
python -m src.cli convert-to-namd --mdf input.mdf --car input.car --output-dir namd_output --residue-name MOL
```

Additional options:
- `--parameter-file`: Specify a parameter file for conversion
- `--charge-groups`: Include charge groups in conversion
- `--keep-workspace`: Keep the workspace directory after conversion (for debugging)

#### Processing Modes

MONET uses the object-based pipeline architecture by default. This approach has several advantages:
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

If you need to use the legacy file-based approach, you can use the `--file-mode` flag, but note that this mode is deprecated and will be removed in version 2.0.0:

```bash
python -m src.cli grid --file-mode --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output-mdf grid_box.mdf --output-car grid_box.car
```

> **DEPRECATED**: The file-based approach is deprecated and will be removed in version 2.0.0. Please use the object-based pipeline as shown above.

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

# Convert to NAMD format
(MolecularPipeline()
    .load('molecule.car', 'molecule.mdf')
    .convert_to_namd(
        output_dir='namd_output',
        residue_name='MOL',
        parameter_file='params.prm',  # Optional
        charge_groups=False,
        cleanup_workspace=True
    ))
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

#### Legacy File-Based API (Deprecated)

> **DEPRECATED**: The file-based approach is deprecated and will be removed in version 2.0.0.

While it is not recommended, you can still use the legacy file-based API programmatically if absolutely necessary:

```python
from src.transformers.legacy.grid import generate_grid_files

# Generate a grid from input files (deprecated)
generate_grid_files(
    car_file="input.car",
    mdf_file="input.mdf",
    output_car="grid_box.car",
    output_mdf="grid_box.mdf",
    grid_dims=(8, 8, 8),
    gap=2.0
)
```

**Migration Guide**

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

MONET supports the following file formats:

- **MDF** (Materials Studio Molecular Data Format): Contains force-field information and connectivity data
- **CAR** (Materials Studio Coordinate Archive): Contains atomic coordinates and molecule structure
- **PDB** (Protein Data Bank): Contains protein structure data (experimental support)

## Repository Structure

```
monet/
├── docs/                        # Documentation 
│   ├── api/                     # API reference docs
│   ├── tutorials/               # Tutorial markdown files
│   ├── architecture/            # Architecture documentation
│   └── examples/                # Example usage docs
├── research/                    # Research, testing and examples
│   ├── benchmarks/              # Performance benchmarking scripts
│   │   └── profiles/            # Profiling scripts
│   ├── data/                    # Test data files
│   │   ├── molecules/           # Molecular structure files
│   │   │   ├── 1NEC/            # Single molecule test data
│   │   │   └── 3NEC/            # Multi-molecule test data
│   │   └── mappings/            # Mapping files for testing
│   ├── examples/                # Example scripts
│   │   ├── basic/               # Basic usage examples
│   │   ├── advanced/            # Advanced usage examples
│   │   ├── legacy/              # Legacy approach examples
│   │   └── tutorials/           # Tutorial code
│   └── tests/                   # Test suite
│       ├── unit/                # Unit tests
│       ├── integration/         # Integration tests
│       └── standalone/          # Standalone test scripts
├── src/                         # Main package
│   ├── models/                  # Data models
│   ├── parsers/                 # File parsers
│   ├── writers/                 # File writers
│   ├── transformers/            # Transformations
│   │   └── legacy/              # Legacy implementations
│   ├── external_tools/          # External tool integrations
│   ├── templates/               # Pipeline templates
│   └── utils/                   # Utility functions
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

### Development Setup

1. Clone the repository
```bash
git clone https://github.com/molsim-lab/monet.git
cd monet
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

- This package was developed to support research in computational chemistry and materials science.# MONET
