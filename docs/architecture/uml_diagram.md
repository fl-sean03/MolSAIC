# Object-Based Architecture: UML Diagram

```mermaid
classDiagram
    class System {
        +List~Molecule~ molecules
        +Dict mdf_data
        +Tuple pbc
        +update_ff_types(mapping)
        +update_charges(mapping)
        +generate_grid(template_molecule, grid_dims, gap)
        +to_files(output_car, output_mdf)
        +generate_mdf_lines(base_name, residue_mapping)
        +generate_car_lines()
    }
    
    class Molecule {
        +List~Atom~ atoms
        +compute_bbox()
        +replicate(offset, center)
    }
    
    class Atom {
        +String atom_name
        +float x
        +float y
        +float z
        +String residue_name
        +int residue_number
        +String atom_type
        +String element
        +float charge
        +List~String~ connections
        +copy()
        +as_dict()
    }
    
    class MolecularPipeline {
        -System system
        -bool debug
        -String debug_prefix
        +load(car_file, mdf_file)
        +update_ff_types(mapping_file)
        +update_charges(mapping_file)
        +generate_grid(grid_dims, gap)
        +save(output_car, output_mdf)
    }
    
    class SystemFactory {
        <<static>>
        +system_from_files(car_file, mdf_file)
    }

    System "1" *-- "many" Molecule
    Molecule "1" *-- "many" Atom
    MolecularPipeline --> System : manages
    SystemFactory --> System : creates
```

## Class Responsibilities

### System
- Central model representing a complete molecular system
- Stores metadata, molecules, and boundary conditions
- Provides transformation methods directly on the system
- Handles file input/output generation

### Molecule
- Represents a single molecule within the system
- Contains a collection of atoms
- Handles bounding box calculation and replication

### Atom 
- Represents a single atom with coordinates and properties
- Stores chemical information (element, charge, connections)

### MolecularPipeline
- Provides a fluent API for chaining multiple transformations
- Loads/saves files at beginning/end of pipeline
- Supports debug output for intermediate steps
- Delegates transformations to System methods

### SystemFactory
- Static factory methods for creating System objects
- Simplifies loading from different file formats