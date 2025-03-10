# MSI2NAMD Tool API

The MSI2NAMD tool provides integration with the external MSI2NAMD software to convert Material Studio files (CAR/MDF) to NAMD format (PSF/PDB). This allows seamless transformation of molecular systems into a format suitable for use with the NAMD molecular dynamics package.

## Overview

The MSI2NAMD tool is implemented through two main components:

1. **MSI2NAMDTool** in `molsaic.external_tools.msi2namd`: The external tool class that handles the direct interaction with the MSI2NAMD executable
2. **msi2namd** method in `molsaic.pipeline.MolecularPipeline`: The pipeline method that provides a user-friendly interface for converting a loaded molecular system

## MSI2NAMDTool Class

The `MSI2NAMDTool` class inherits from `BaseExternalTool` and provides specialized functionality for MSI2NAMD conversions.

```python
from molsaic.external_tools import MSI2NAMDTool

# Create tool instance
msi2namd_tool = MSI2NAMDTool()

# Execute the tool directly
result = msi2namd_tool.execute(
    car_file="path/to/input.car",
    mdf_file="path/to/input.mdf",
    parameter_file="path/to/parameters.prm",
    residue_name="MOL",
    charge_groups=False
)

# Access output files
pdb_file = result['pdb_file']
psf_file = result['psf_file']
```

### Key Parameters

- **system**: The molecular system to convert (alternative to providing car/mdf files)
- **car_file**: Path to CAR file (if system not provided)
- **mdf_file**: Path to MDF file (if system not provided)
- **parameter_file**: Path to parameter file (REQUIRED for MSI2NAMD)
- **residue_name**: Residue name for the output PDB file (max 4 characters)
- **charge_groups**: Whether to include charge groups in conversion
- **output_dir**: Directory to store output files
- **cleanup**: Whether to clean up the workspace after execution

### Return Value

The `execute` method returns a dictionary containing:

- **return_code**: Process return code
- **stdout**: Process standard output
- **stderr**: Process standard error
- **output_files**: List of all generated output files
- **pdb_file**: Path to the generated PDB file
- **psf_file**: Path to the generated PSF file
- **namd_file**: Path to any generated NAMD configuration file
- **param_file**: Path to any generated parameter file

## Pipeline Integration

The `MolecularPipeline` class provides a streamlined way to use MSI2NAMD with a loaded molecular system.

```python
from molsaic.pipeline import MolecularPipeline

# Create pipeline and load system
pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf")

# Convert to NAMD format
pipeline.msi2namd(
    output_dir="namd_output",
    residue_name="MOL",
    parameter_file="path/to/parameters.prm",
    charge_groups=False
)

# Access output files through pipeline.namd_files dictionary
print(pipeline.namd_files['pdb_file'])
print(pipeline.namd_files['psf_file'])
```

### Pipeline Method Parameters

- **output_dir**: Directory to store output files (default: current directory)
- **residue_name**: Residue name for the output PDB file (max 4 characters)
- **parameter_file**: Path to parameter file (REQUIRED)
- **charge_groups**: Whether to include charge groups (default: False)
- **cleanup_workspace**: Whether to clean up the workspace (default: True)

## Command Line Usage

MolSAIC provides a CLI command to perform MSI2NAMD conversions:

```bash
molsaic msi2namd --car input.car --mdf input.mdf --parameter-file params.prm --output-dir namd_output --residue-name MOL
```

### CLI Arguments

- **--car**: Input CAR file (REQUIRED)
- **--mdf**: Input MDF file (REQUIRED)
- **--parameter-file**: Parameter file for MSI2NAMD conversion (REQUIRED)
- **--output-dir**: Output directory for NAMD files (default: "namd_output")
- **--residue-name**: Residue name for NAMD files (max 4 characters)
- **--charge-groups**: Include charge groups in conversion

## Implementation Notes

- MSI2NAMD requires that input CAR and MDF files have the same base name
- The residue name is truncated to 4 characters if longer (PDB format limitation)
- The tool attempts to find output files even if the expected naming pattern doesn't match
- All conversion is performed in a temporary workspace directory
- Output files are automatically copied to the specified output directory