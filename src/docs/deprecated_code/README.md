# Deprecated Code

This directory contains deprecated code that has been preserved for reference purposes. These implementations have been superseded by newer, more modular approaches in the main codebase.

## Included Files

### CLI Implementation

- **cli.py**: The monolithic CLI implementation that was replaced by the modular command-based architecture in `src/cli/`

### External Tools

- **packmol_cli.py**: Standalone CLI for Packmol, replaced by the modular implementation in `src/cli/commands/packmol_command.py`

### Legacy Transformers

- **legacy/grid.py**: File-based grid transformation implementation, replaced by the object-based approach in `src/transformers/grid.py`
- **legacy/update_charges.py**: File-based charge updating implementation, replaced by the object-based approach in `src/transformers/update_charges.py`
- **legacy/update_ff.py**: File-based force field updating implementation, replaced by the object-based approach in `src/transformers/update_ff.py`

## Deprecation Notice

All code in this directory is scheduled for removal in version 2.0.0 of the MolSAIC package. It is preserved here for:

1. **Reference**: To help understand the evolution of the codebase
2. **Backwards Compatibility**: To support users still using the deprecated approaches
3. **Migration Assistance**: To aid in migrating custom code that may depend on these implementations

## Migration

If you're using any of these deprecated implementations, please refer to the migration guides:

- For CLI usage migration: See `src/cli/MIGRATION.md`
- For API usage migration: See `resources/examples/tutorials/docs/migration_guide.md`

The object-based pipeline approach offers better performance, modularity, and extensibility compared to the file-based approach.