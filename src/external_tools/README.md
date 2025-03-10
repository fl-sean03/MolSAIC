# External Tools Integration

This module provides integration with external computational chemistry tools for the MolSAIC framework. It includes a standardized interface for integrating with various command-line tools used in molecular modeling workflows.

## Architecture

External tool integration follows a consistent pattern:

1. **BaseExternalTool Class**: All tools inherit from this base class which provides:
   - Workspace management
   - Process execution and monitoring
   - Input/output file handling
   - Cleanup logic

2. **Tool-Specific Implementation**: Each tool implements:
   - Input validation
   - Input file preparation 
   - Command building
   - Output processing

## Current Tools

- **Packmol**: Molecular packing tool for generating initial configurations
- **MSI2NAMD**: Conversion tool to translate MSI format files to NAMD formats

## Usage Guidelines

### Output Directory Standardization

All external tools follow these standards for output file management:

1. **Default Output Directory**:
   - Each tool has a default output directory name (e.g., `packmol_output`, `namd_output`)
   - Output directories are automatically enumerated if they already exist 
   - Example: `packmol_output`, `packmol_output_1`, `packmol_output_2`, etc.

2. **File Naming Conventions**:
   - Successful outputs: Preserved with original name
   - Partial outputs (from timeouts): `[filename]_partial.[ext]`
   - Outputs with errors: `[filename]_error.[ext]`

3. **CLI Parameters**:
   - `--output-dir`: Override the default output directory
   - `--timeout`: Set maximum execution time (in seconds)
   - `--continue-on-timeout`: Continue execution with partial results
   - `--continue-on-error`: Continue execution despite errors

### Timeout Handling

External tools support graceful timeout handling:

1. **Default Timeouts**:
   - Default timeout varies by tool (e.g., 900 seconds for Packmol)
   - Can be customized with `--timeout [seconds]`

2. **Partial Results**:
   - If a tool times out, it attempts to capture partial results
   - Partial results are copied to output directory with `_partial` suffix
   - Use `--continue-on-timeout` to continue processing with partial results

### Error Handling

Error handling provides robust recovery options:

1. **Error Reports**:
   - Detailed error messages in logs
   - Error context (stdout/stderr) preserved
   
2. **Recovery Options**:
   - `--continue-on-error`: Continue processing despite errors
   - Error outputs preserved with `_error` suffix

## Adding New Tools

To add a new external tool integration:

1. Create a new class inheriting from `BaseExternalTool`
2. Implement required abstract methods:
   - `_get_tool_name()`
   - `validate_inputs()`
   - `prepare_inputs()`
   - `build_command()`
   - `process_output()`
3. Update config.py with default parameters for the tool
4. Create CLI integration in cli/commands directory

## Environment Variables

Tool paths can be configured using environment variables:

- `MOLSAIC_PACKMOL_PATH`: Path to Packmol executable
- `MOLSAIC_MSI2NAMD_PATH`: Path to MSI2NAMD executable

If not set, executables are searched in the system PATH.