# Packmol Tool API

The `PackmolTool` class provides integration with the [Packmol](https://m3g.github.io/packmol) software, which is used for generating initial configurations for molecular dynamics simulations by packing molecules in defined regions of space.

## Overview

This tool allows you to:

1. Parse existing Packmol input files into structured dictionaries
2. Update configurations programmatically
3. Generate new Packmol input files from configurations
4. Execute Packmol directly from Python

## Command Line Usage

MONET provides a command-line interface for interacting with Packmol through the integrated tool:

```bash
# Parse and print Packmol configuration as JSON
moltools packmol --input-file system.inp --print-json

# Generate a new input file with updates from a JSON file
moltools packmol --input-file system.inp --update-file updates.json --output-file modified.inp

# Execute Packmol with an input file
moltools packmol --input-file system.inp --execute

# Generate a new input file with updates and execute Packmol
moltools packmol --input-file system.inp --update-file updates.json --output-file modified.inp --execute
```

Example JSON update file (updates.json):
```json
{
  "global": {
    "tolerance": ["3.0"],
    "output": ["updated_output.pdb"]
  },
  "structures": [
    {
      "properties": {
        "number": ["50"]
      }
    }
  ]
}
```

## Python API Usage

### Basic Usage

```python
from moltools.external_tools import PackmolTool

# Initialize the tool
packmol = PackmolTool()

# Parse an existing input file
config = packmol.parse_packmol_file("input.inp")

# Update the configuration
config["global"]["tolerance"] = ["2.5"]  # Update tolerance
config["structures"][0]["properties"]["number"] = ["20"]  # Change number of molecules

# Generate a new input file
packmol.generate_packmol_file(config, "updated.inp")

# Execute Packmol with the new input file
result = packmol.execute(input_file="updated.inp")

# Get the output file
output_file = result.get("output_file")
```

### With Configuration Updates

```python
# Define updates to apply
updates = {
    "global": {
        "tolerance": ["3.0"],
        "output": ["new_output.pdb"]
    },
    "structures": [
        {
            "properties": {
                "number": ["50"]  # Update first structure
            }
        }
    ]
}

# Execute with updates
result = packmol.execute(
    input_file="input.inp",
    update_dict=updates,
    output_file="updated.inp"
)
```

## API Reference

### Class: `PackmolTool`

Inherits from: `BaseExternalTool`

#### Constructor

```python
PackmolTool(executable_path=None, workspace_manager=None, timeout=None)
```

- `executable_path` (str, optional): Path to the Packmol executable. If None, will search PATH or use the value specified in environment variable `MOLTOOLS_PACKMOL_PATH`.
- `workspace_manager` (WorkspaceManager, optional): Workspace manager to use. If None, a new one will be created.
- `timeout` (int, optional): Default timeout for tool execution in seconds.

#### Methods

##### `parse_packmol_file(file_path)`

Parses a Packmol input file into a structured dictionary.

- `file_path` (str): Path to the Packmol input file to parse.

Returns: A dictionary with two keys:
- `global`: A dictionary mapping global keywords to lists of tokens.
- `structures`: A list of structure blocks, each represented as a dictionary.

##### `generate_packmol_file(config, output_file)`

Generates a Packmol input file from a configuration dictionary.

- `config` (dict): The configuration dictionary.
- `output_file` (str): Path where the generated input file will be written.

##### `update_dict(orig, updates)`

Recursively updates dictionary `orig` with values from `updates`.

- `orig` (dict): The original dictionary.
- `updates` (dict): The updates to merge into `orig`.

Returns: The updated dictionary.

##### `execute(input_file=None, output_file=None, config_dict=None, update_dict=None, **kwargs)`

Executes Packmol using the specified inputs.

- `input_file` (str, optional): Path to an existing Packmol input file.
- `output_file` (str, optional): Path where a generated input file will be written.
- `config_dict` (dict, optional): Configuration dictionary to use for generating input file.
- `update_dict` (dict, optional): Updates to apply to the configuration.
- `**kwargs`: Additional parameters such as `timeout`, `cleanup`, etc.

Returns: A dictionary with execution results, including:
- `return_code`: The process return code.
- `stdout`: Standard output from the process.
- `stderr`: Standard error from the process.
- `output_files`: List of output files produced.
- `output_file`: Path to the main output file.
- `config`: The configuration used for execution.

## Configuration Format

The configuration dictionary has the following structure:

```python
{
    "global": {
        "keyword1": ["value1", "value2"],
        "keyword2": ["value"]
    },
    "structures": [
        {
            "structure_file": "file1.pdb",
            "properties": {
                "number": ["10"],
                "fixed": ["1.0", "2.0", "3.0", "0.0", "0.0", "0.0"]
            },
            "constraints": [
                {
                    "keyword": "inside",
                    "block": "box",
                    "params": ["0.0", "0.0", "0.0", "30.0", "30.0", "30.0"]
                }
            ],
            "others": []
        }
    ]
}
```

## Examples

See the example scripts in `resources/examples/advanced/packmol_example.py` for more detailed usage examples.