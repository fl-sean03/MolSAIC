# MolSAIC CLI Architecture

This directory contains the modular command-line interface for the MolSAIC package. The architecture follows a command pattern where each subcommand is implemented as a separate class inheriting from a common base class.

## Directory Structure

```
cli/
├── __init__.py           # Main entry point and command dispatch
├── base.py               # Base command class and utilities
├── commands/             # Command implementations
│   ├── __init__.py       # Command registry
│   ├── README.md         # Documentation for command implementation
│   ├── packmol_command.py # Packmol command implementation
│   └── ...               # Other command implementations
└── utils/                # Shared utilities
    ├── __init__.py
    └── workspace.py      # Workspace management utilities
```

## Architecture Overview

### Main Entry Point (`__init__.py`)

The main entry point provides:
- Command-line argument parsing
- Command registration and discovery
- Global configuration setup
- Workspace setup and cleanup
- Command dispatch

### Base Command (`base.py`)

The `BaseCommand` abstract base class defines the interface for all commands:
- `configure_parser`: Configure command-specific arguments
- `execute`: Implement command logic
- `validate_args`: Validate command arguments

### Command Registry (`commands/__init__.py`)

The command registry maps command names to command classes, making it easy to add new commands without modifying the main entry point.

### Utilities (`utils/`)

Shared utilities used by multiple commands, such as workspace management.

## Usage

### From the Command Line

```bash
# Main entry point
molsaic [global options] command [command options]

# Examples
molsaic packmol --input-file system.inp --execute
molsaic grid --mdf input.mdf --car input.car --grid 3
```

### In Code

```python
# Direct command execution for testing or integration
from molsaic.cli.commands.packmol_command import main
main()
```

## Adding a New Command

See [commands/README.md](commands/README.md) for details on adding a new command.

## Benefits of This Architecture

1. **Modularity**: Commands are self-contained and can be developed independently
2. **Extensibility**: New commands can be added without modifying existing code
3. **Maintainability**: Changes to one command don't affect others
4. **Testability**: Commands can be tested in isolation
5. **Consistent Interface**: All commands follow the same pattern
6. **Code Organization**: Clearer organization makes the codebase easier to understand
7. **Documentation**: Self-documenting structure with README files at each level