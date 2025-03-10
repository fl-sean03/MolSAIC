# Migrating from File-Based to Object-Based API

This guide provides information and examples to help you migrate your code from the deprecated file-based API to the recommended object-based pipeline API.

## Why Migrate?

The file-based API in MolSAIC is **deprecated** and will be removed in version 2.0.0. Here's why you should migrate:

- **Better Performance**: The object-based API eliminates intermediate file I/O for chained operations
- **More Features**: New features like external tools integration are only available in the object-based API
- **Cleaner Code**: The pipeline architecture leads to more readable and maintainable code
- **Debug Support**: Get intermediate output files for debugging without manual steps
- **Better Error Handling**: More detailed error messages and consistent error handling

## Migration Examples

### Grid Generation

**Old (deprecated):**
```python
from src.transformers.legacy.grid import generate_grid_files

generate_grid_files(
    car_file="input.car",
    mdf_file="input.mdf",
    output_car="grid_box.car",
    output_mdf="grid_box.mdf",
    grid_dims=(8, 8, 8),
    gap=2.0,
    base_name="MOL"
)
```

**New (recommended):**
```python
from src.pipeline import MolecularPipeline

pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf") \
        .generate_grid(grid_dims=(8, 8, 8), gap=2.0) \
        .save("grid_box.car", "grid_box.mdf", "MOL")
```

### Force-Field Type Updates

**Old (deprecated):**
```python
from src.transformers.legacy.update_ff import update_ff_types

update_ff_types(
    car_file="input.car",
    mdf_file="input.mdf",
    output_car="updated.car",
    output_mdf="updated.mdf",
    mapping_file="mappings/charge_to_ff.json"
)
```

**New (recommended):**
```python
from src.pipeline import MolecularPipeline

pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf") \
        .update_ff_types("mappings/charge_to_ff.json") \
        .save("updated.car", "updated.mdf")
```

### Charge Updates

**Old (deprecated):**
```python
from src.transformers.legacy.update_charges import update_charges

update_charges(
    car_file="input.car",
    mdf_file="input.mdf",
    output_car="updated.car",
    output_mdf="updated.mdf",
    mapping_file="mappings/ff_to_charge.json"
)
```

**New (recommended):**
```python
from src.pipeline import MolecularPipeline

pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf") \
        .update_charges("mappings/ff_to_charge.json") \
        .save("updated.car", "updated.mdf")
```

### Chaining Multiple Operations

**Old (deprecated):**
```python
from src.transformers.legacy.update_ff import update_ff_types
from src.transformers.legacy.update_charges import update_charges
from src.transformers.legacy.grid import generate_grid_files

# Multiple file operations with intermediate files
update_ff_types(
    car_file="input.car",
    mdf_file="input.mdf",
    output_car="temp1.car",
    output_mdf="temp1.mdf",
    mapping_file="mappings/charge_to_ff.json"
)

update_charges(
    car_file="temp1.car",
    mdf_file="temp1.mdf",
    output_car="temp2.car",
    output_mdf="temp2.mdf",
    mapping_file="mappings/ff_to_charge.json"
)

generate_grid_files(
    car_file="temp2.car",
    mdf_file="temp2.mdf", 
    output_car="final.car",
    output_mdf="final.mdf",
    grid_dims=(8, 8, 8),
    gap=2.0
)
```

**New (recommended):**
```python
from src.pipeline import MolecularPipeline

# All operations chained without intermediate files
pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf") \
        .update_ff_types("mappings/charge_to_ff.json") \
        .update_charges("mappings/ff_to_charge.json") \
        .generate_grid(grid_dims=(8, 8, 8), gap=2.0) \
        .save("final.car", "final.mdf")
```

## Command Line Migration

### Grid Generation

**Old (deprecated):**
```bash
python -m src.cli grid --file-mode --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output-mdf grid_box.mdf --output-car grid_box.car
```

**New (recommended):**
```bash
python -m src.cli grid --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output-mdf grid_box.mdf --output-car grid_box.car
```

Simply remove the `--file-mode` flag to use the object-based pipeline by default.

### Force-Field Type Updates

**Old (deprecated):**
```bash
python -m src.cli update-ff --file-mode --mdf input.mdf --car input.car --output-mdf updated.mdf --output-car updated.car --mapping mapping.json
```

**New (recommended):**
```bash
python -m src.cli update-ff --mdf input.mdf --car input.car --output-mdf updated.mdf --output-car updated.car --mapping mapping.json
```

### Charge Updates

**Old (deprecated):**
```bash
python -m src.cli update-charges --file-mode --mdf input.mdf --car input.car --output-mdf updated.mdf --output-car updated.car --mapping mapping.json
```

**New (recommended):**
```bash
python -m src.cli update-charges --mdf input.mdf --car input.car --output-mdf updated.mdf --output-car updated.car --mapping mapping.json
```

## Advanced Pipeline Features

The object-based pipeline provides several advanced features not available in the file-based API:

### Debugging

Generate debug output files for each step:

```python
pipeline = MolecularPipeline(debug=True, debug_prefix="debug_")
pipeline.load("input.car", "input.mdf")
pipeline.update_ff_types("mappings/charge_to_ff.json")  # Creates debug_1_*.car/mdf
pipeline.update_charges("mappings/ff_to_charge.json")   # Creates debug_2_*.car/mdf
pipeline.save("output.car", "output.mdf")
```

### System Access

Access the System object directly for custom operations:

```python
pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf")

# Get the system object
system = pipeline.get_system()

# Perform custom operations
atom_count = sum(len(mol.atoms) for mol in system.molecules)
print(f"Total atoms: {atom_count}")

# Continue the pipeline
pipeline.save("output.car", "output.mdf")
```

### Checkpointing

Save and load pipeline state:

```python
pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf")
pipeline.update_ff_types("mappings/charge_to_ff.json")
pipeline.save_checkpoint("checkpoint.pkl")

# Later, or in another script
from src.pipeline import MolecularPipeline
pipeline = MolecularPipeline.load_checkpoint("checkpoint.pkl")
pipeline.update_charges("mappings/ff_to_charge.json")
pipeline.save("output.car", "output.mdf")
```

### Validation

Validate the system at any point:

```python
pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf")
pipeline.update_ff_types("mappings/charge_to_ff.json")

# Validate the system
validation_results = pipeline.validate()
if not validation_results["valid"]:
    print("Validation failed:", validation_results["issues"])
else:
    pipeline.save("output.car", "output.mdf")
```

### Using External Tools

Convert files to NAMD format (only available in object-based API):

```python
pipeline = MolecularPipeline()
pipeline.load("input.car", "input.mdf")
pipeline.convert_to_namd(
    output_dir="namd_output",
    residue_name="MOL",
    parameter_file="params.prm"
)
```

## Need Help?

If you encounter issues migrating your code, please open an issue on GitHub or refer to the examples in the `examples/` directory for more guidance.