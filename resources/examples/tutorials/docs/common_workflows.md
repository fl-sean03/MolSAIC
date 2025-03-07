# MolTools: Common Workflows Tutorial

This tutorial covers common workflows using both the file-based and object-based approaches in MolTools.

## Table of Contents

1. [Installation](#installation)
2. [Grid Replication](#grid-replication)
3. [Force-Field Type Updates](#force-field-type-updates)
4. [Charge Updates](#charge-updates)
5. [Combining Transformations](#combining-transformations)
6. [Performance Considerations](#performance-considerations)
7. [Debug and Troubleshooting](#debug-and-troubleshooting)

## Installation

Before using MolTools, you need to install it:

```bash
# Clone the repository
git clone https://github.com/yourusername/moltools.git

# Navigate to the directory
cd moltools

# Install in development mode
pip install -e .
```

## Grid Replication

Grid replication creates a 3D grid of replicated molecules, useful for creating periodic systems.

### File-Based Approach (CLI)

```bash
python -m moltools.cli grid --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output-mdf grid_box.mdf --output-car grid_box.car
```

### Object-Based Approach (CLI)

```bash
python -m moltools.cli grid --object-mode --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output-mdf grid_box.mdf --output-car grid_box.car
```

### File-Based Approach (Python)

```python
from moltools.transformers.grid import generate_grid_files

generate_grid_files(
    car_file="input.car",
    mdf_file="input.mdf",
    output_car="grid_box.car",
    output_mdf="grid_box.mdf",
    grid_dims=(8, 8, 8),
    gap=2.0
)
```

### Object-Based Approach (Python)

```python
from moltools.pipeline import MolecularPipeline

pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf") \
        .generate_grid(grid_dims=(8, 8, 8), gap=2.0) \
        .save("grid_box.car", "grid_box.mdf")
```

## Force-Field Type Updates

Update force-field types based on charge and element mapping.

### File-Based Approach (CLI)

```bash
python -m moltools.cli update-ff --car input.car --mdf input.mdf --output-car updated.car --output-mdf updated.mdf --mapping mapping.json
```

### Object-Based Approach (CLI)

```bash
python -m moltools.cli update-ff --object-mode --car input.car --mdf input.mdf --output-car updated.car --output-mdf updated.mdf --mapping mapping.json
```

### File-Based Approach (Python)

```python
from moltools.transformers.update_ff import update_ff_types

update_ff_types(
    car_file="input.car",
    mdf_file="input.mdf",
    output_car="updated.car",
    output_mdf="updated.mdf",
    mapping_file="mapping.json"
)
```

### Object-Based Approach (Python)

```python
from moltools.pipeline import MolecularPipeline

pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf") \
        .update_ff_types("mapping.json") \
        .save("updated.car", "updated.mdf")
```

## Charge Updates

Update atomic charges based on force-field type mapping.

### File-Based Approach (CLI)

```bash
python -m moltools.cli update-charges --car input.car --mdf input.mdf --output-car updated.car --output-mdf updated.mdf --mapping charge_mapping.json
```

### Object-Based Approach (CLI)

```bash
python -m moltools.cli update-charges --object-mode --car input.car --mdf input.mdf --output-car updated.car --output-mdf updated.mdf --mapping charge_mapping.json
```

### File-Based Approach (Python)

```python
from moltools.transformers.update_charges import update_charges

update_charges(
    car_file="input.car",
    mdf_file="input.mdf",
    output_car="updated.car",
    output_mdf="updated.mdf",
    mapping_file="charge_mapping.json"
)
```

### Object-Based Approach (Python)

```python
from moltools.pipeline import MolecularPipeline

pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf") \
        .update_charges("charge_mapping.json") \
        .save("updated.car", "updated.mdf")
```

## Combining Transformations

Combining multiple transformations is where the object-based approach really shines.

### File-Based Approach (with intermediate files)

```python
from moltools.transformers.update_ff import update_ff_types
from moltools.transformers.update_charges import update_charges
from moltools.transformers.grid import generate_grid_files

# Step 1: Update force-field types
update_ff_types(
    car_file="input.car",
    mdf_file="input.mdf",
    output_car="temp1.car",
    output_mdf="temp1.mdf",
    mapping_file="ff_mapping.json"
)

# Step 2: Update charges
update_charges(
    car_file="temp1.car",
    mdf_file="temp1.mdf",
    output_car="temp2.car",
    output_mdf="temp2.mdf",
    mapping_file="charge_mapping.json"
)

# Step 3: Generate grid
generate_grid_files(
    car_file="temp2.car",
    mdf_file="temp2.mdf",
    output_car="final.car",
    output_mdf="final.mdf",
    grid_dims=(8, 8, 8),
    gap=2.0
)

# Clean up intermediate files
import os
for file in ["temp1.car", "temp1.mdf", "temp2.car", "temp2.mdf"]:
    os.remove(file)
```

### Object-Based Approach (chained operations)

```python
from moltools.pipeline import MolecularPipeline

# Chain all operations in a single pipeline
(MolecularPipeline()
    .load("input.car", "input.mdf")
    .update_ff_types("ff_mapping.json")
    .update_charges("charge_mapping.json")
    .generate_grid(grid_dims=(8, 8, 8), gap=2.0)
    .save("final.car", "final.mdf"))
```

## Performance Considerations

### Large Molecules

For large molecular systems, the object-based approach generally provides better performance:

- **Memory efficiency**: The object-based approach keeps the molecular system in memory, avoiding repeated parsing and writing for intermediate steps.
- **I/O reduction**: The file-based approach requires reading and writing files for each transformation, which can be slow for large systems.

### Many Transformations

When chaining multiple transformations, the object-based approach significantly outperforms the file-based approach:

- **Linear vs. Constant I/O**: For N transformations, the file-based approach requires 2N file operations, while the object-based approach requires only 2 (initial load and final save).
- **Performance Gap**: The performance gap widens as the number of transformations increases.

## Debug and Troubleshooting

### Debug Mode in Object-Based Approach

The object-based approach supports a debug mode that generates intermediate files:

```python
pipeline = MolecularPipeline(debug=True, debug_prefix="debug_")
pipeline.load("input.car", "input.mdf")
pipeline.update_ff_types("ff_mapping.json")  # Creates debug_1_*.car/mdf
pipeline.update_charges("charge_mapping.json")  # Creates debug_2_*.car/mdf
pipeline.generate_grid(grid_dims=(8, 8, 8), gap=2.0)  # Creates debug_3_*.car/mdf
pipeline.save("final.car", "final.mdf")
```

This is also available in the CLI:

```bash
python -m moltools.cli update-ff --object-mode --debug-output --debug-prefix "debug_" --car input.car --mdf input.mdf --output-car updated.car --output-mdf updated.mdf --mapping mapping.json
```

### Verifying Results

To verify the results:

1. **Check Atom Counts**: Count the number of atoms in input and output files
2. **Validate Force-Field Types**: Check that the force-field types match the mapping
3. **Validate Charges**: Check that the charges match the mapping
4. **Validate Grid Dimensions**: For grid replication, verify the PBC dimensions

### Common Issues

#### Missing Connections

If connections are missing in the output MDF file:

- Ensure you're using both CAR and MDF files as input
- Check that the input MDF file contains connection information
- Verify that the molecule names match between CAR and MDF files

#### Force-Field Mapping Not Applied

If force-field type updates aren't applied:

- Check the mapping format in the JSON file
- Verify that the charge values match exactly (floating-point precision matters)
- Check that the element symbols match exactly (case-sensitive)

#### Grid Dimensions Issues

If the grid dimensions seem incorrect:

- Check that the grid_dims parameter is specified as expected
- Verify that the gap parameter is appropriate for your molecule size
- Ensure the PBC settings are enabled in the output files