# API Reference

This section contains detailed API documentation for MONET (MOlecular NEtwork Toolkit).

## Main Classes

### Core Components
- [System](system.md) - The central data model representing a molecular system
- [Molecule](molecule.md) - Represents a molecule within a system
- [Atom](atom.md) - Represents an individual atom with properties
- [MolecularPipeline](pipeline.md) - Fluent API for chaining operations

### Parsers & Writers
- [CARParser](car_parser.md) - Parser for CAR (Coordinate Archive) files
- [MDFParser](mdf_parser.md) - Parser for MDF (Material Data Format) files
- [PDBParser](pdb_parser.md) - Parser for PDB (Protein Data Bank) files
- [Writers](writers.md) - Classes for writing molecular data to files

### Transformers
- [GridTransformer](grid_transformer.md) - Replicates molecules in a 3D grid
- [FFUpdater](ff_updater.md) - Updates force field types
- [ChargeUpdater](charge_updater.md) - Updates atomic charges
- [Legacy Transformers](legacy_transformers.md) - Deprecated file-based transformers

### External Tools
- [ExternalTool](external_tool.md) - Base class for external tool integration
- [MSI2NAMD](msi2namd.md) - Interface for MSI2NAMD conversion tool
- [Packmol](packmol.md) - Interface for Packmol molecular packing tool

## Command Line Interface

MONET provides a command-line interface for common operations. Use `moltools --help` to see all available commands.

### Available Commands

- `grid`: Generate a grid of replicated molecules
- `update-ff`: Update force-field types based on a mapping
- `update-charges`: Update atomic charges based on a mapping
- `convert-to-namd`: Convert files to NAMD format using MSI2NAMD
- `packmol`: Work with Packmol input files

### Examples

#### Grid Replication

```bash
moltools grid --mdf input.mdf --car input.car --grid 3 --output-mdf grid.mdf --output-car grid.car
```

#### Packmol Integration

```bash
# Parse and print Packmol configuration
moltools packmol --input-file system.inp --print-json

# Generate a new Packmol input file with updates
moltools packmol --input-file system.inp --update-file updates.json --output-file modified.inp

# Execute Packmol
moltools packmol --input-file system.inp --execute
```
