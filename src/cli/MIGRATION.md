# CLI Migration Roadmap

This document outlines the migration plan for transitioning from the monolithic CLI implementation in `src/cli.py` to the more modular, object-oriented approach in the `src/cli/` directory.

## Current Commands

The current CLI implementation includes the following commands:

### 1. `grid` Command

**Purpose**: Generate a grid of replicated molecules

**Parameters**:
- `--mdf`: Input MDF file (required)
- `--car`: Input CAR file (required)
- `--output-mdf`: Output MDF file (default: "grid_box.mdf")
- `--output-car`: Output CAR file (default: "grid_box.car")
- `--grid`: Grid dimension along each axis (default: from config.DEFAULT_GRID_SIZE)
- `--gap`: Gap (in Angstroms) between molecules (default: from config.DEFAULT_GAP)
- `--base-name`: Base molecule name for output molecules (default: "MOL")

**Implementation Notes**:
- Supports both object-based and legacy file-based modes
- Uses MolecularPipeline for object-based mode
- Uses grid.generate_grid_files for legacy file-based mode

### 2. `update-ff` Command

**Purpose**: Update force-field types based on a mapping

**Parameters**:
- `--mdf`: Input MDF file (conditionally required)
- `--car`: Input CAR file (conditionally required)
- `--output-mdf`: Output MDF file (conditionally required)
- `--output-car`: Output CAR file (conditionally required)
- `--mapping`: JSON mapping file (required)

**Implementation Notes**:
- In object-based mode, both `--mdf` and `--car` are required
- In file-based mode, at least one of `--mdf` or `--car` is required
- Output requirements differ between modes

### 3. `update-charges` Command

**Purpose**: Update atomic charges based on a mapping

**Parameters**:
- `--mdf`: Input MDF file (conditionally required)
- `--car`: Input CAR file (conditionally required)
- `--output-mdf`: Output MDF file (conditionally required)
- `--output-car`: Output CAR file (conditionally required)
- `--mapping`: JSON mapping file (required)

**Implementation Notes**:
- In object-based mode, both `--mdf` and `--car` are required
- In file-based mode, at least one of `--mdf` or `--car` is required
- Output requirements differ between modes

### 4. `msi2namd` Command

**Purpose**: Convert files to NAMD format (PDB/PSF) using MSI2NAMD

**Parameters**:
- `--mdf`: Input MDF file (required)
- `--car`: Input CAR file (required)
- `--output-dir`: Output directory for NAMD files (default: "namd_output")
- `--residue-name`: Residue name for NAMD files
- `--parameter-file`: Parameter file for MSI2NAMD conversion (required)
- `--charge-groups`: Include charge groups in conversion (flag)

**Implementation Notes**:
- Only available in object-based mode
- Automatically creates and manages an output directory
- Uses MolecularPipeline.msi2namd method
- Tracks and reports generated files

### 5. `packmol` Command

**Purpose**: Work with Packmol input files for molecular packing

**Parameters**:
- `--input-file`: Path to an existing Packmol input file (required)
- `--output-file`: Path to write the generated Packmol input file
- `--update-file`: Path to a JSON file with updates to apply
- `--execute`: Execute Packmol after processing (flag)
- `--print-json`: Print configuration as JSON and exit (flag)
- `--output-dir`: Directory to store the output files (default: "packmol_output")
- `--timeout`: Timeout in seconds for Packmol execution (default: 900)
- `--continue-on-timeout`: Continue execution if timeout occurs (flag)
- `--continue-on-error`: Continue execution even if Packmol fails (flag)

**Implementation Notes**:
- Already implemented in the modular structure as `src/cli/commands/packmol_command.py`
- Uses PackmolTool from external_tools
- Supports multiple operations: parsing, updating, generating, and executing

## Global Options

All commands support the following global options:

- `--log-level`: Set logging level (choices: DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--file-mode`: Use legacy file-based approach instead of object-based pipeline (deprecated)
- `--debug-output`: Generate intermediate files for debugging (only in object-based mode)
- `--debug-prefix`: Prefix for debug output files (only with --debug-output, default: "debug_")
- `--keep`: Keep all artifacts after completion (logs and workspaces)
- `--keep-logs`: Keep only logs after completion (cleanup workspaces)

## Common Patterns

1. **Pipeline Creation Pattern**:
   ```python
   pipeline = MolecularPipeline(
       debug=args.debug_output,
       debug_prefix=args.debug_prefix,
       keep_workspace=config.keep_all_workspaces
   )
   ```

2. **Mode Detection Pattern**:
   ```python
   use_object_mode = not args.file_mode
   ```

3. **File Mode Deprecation Warning**:
   ```python
   if args.file_mode and config.FILE_MODE_DEPRECATED:
       config.show_file_mode_deprecation_warning(logger)
   ```

4. **Error Handling Pattern**:
   ```python
   try:
       # Command implementation
   except Exception as e:
       logger.error(f"Command failed: {str(e)}")
       # Keep workspace on error
       config.keep_session_workspace = True
       logger.info(f"Logs available in workspace: {config.session_workspace.current_workspace}")
       return 1
   ```

5. **Workspace Directory Management Pattern**:
   ```python
   base_output_dir = args.output_dir
   if not os.path.isabs(base_output_dir):
       base_output_dir = os.path.abspath(base_output_dir)
   
   # If the directory exists, enumerate it
   output_dir = base_output_dir
   counter = 1
   while os.path.exists(output_dir):
       output_dir = f"{base_output_dir}_{counter}"
       counter += 1
   
   os.makedirs(output_dir, exist_ok=True)
   ```

## Migration Strategy

1. **Command Implementation Approach**:
   - Each command will be implemented as a separate class inheriting from `BaseCommand`
   - Each class will have `configure_parser` and `execute` methods
   - Common utilities will be extracted to base class or helper classes

2. **Shared Features**:
   - All commands should support the global options
   - All commands should handle both modes (object-based and file-based) if applicable
   - All commands should use consistent error handling and logging
   - All commands should properly manage workspace directories

3. **Migration Order**:
   1. First, update `BaseCommand` and `PipelineHelper` if needed
   2. Migrate simple commands first: grid, update-ff, update-charges
   3. Migrate more complex commands: msi2namd
   4. Update the main entry point and test all commands
   5. Deprecate the old implementation

## Implementation Plan

1. For each command:
   - Create a new file in `src/cli/commands/`
   - Implement the command class
   - Move argument parsing and execution logic from `src/cli.py`
   - Update `commands/__init__.py` to register the new command
   - Test the command thoroughly

2. After all commands are migrated:
   - Update documentation to reflect the new structure
   - Add deprecation warnings to old implementation
   - Plan for removal in a future version

## Testing Strategy

Each migrated command should be tested for:
1. Correct argument parsing
2. Proper execution in both modes (if applicable)
3. Correct error handling
4. Compatibility with existing examples and workflows