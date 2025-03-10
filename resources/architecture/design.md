Below is a comprehensive design document that you can share with your development team. It describes the overall architecture, modules, data flow, and the detailed responsibilities of each component. You can use this document to guide development and future collaboration.

---

# MolSAIC: Molecular Data Processing Tools

## 1. Introduction

### 1.1 Purpose
The MolSAIC package is designed to provide a robust, modular, and extensible suite of tools for processing molecular data files. The package will support tasks such as:
- Parsing and writing MDF (Materials Studio Molecular Data Format) files
- Parsing and writing CAR (Materials Studio Coordinate Archive) files
- Grid replication of molecules
- Updating force-field types and charges based on mapping dictionaries
- Integrating with other workflows (e.g., PDB processing)

### 1.2 Scope
The package will serve researchers in computational chemistry and materials science who need to manipulate and transform molecular structures in various file formats. It aims to provide:
- A clean command-line interface (CLI) with subcommands for different tasks
- Object-oriented design for core molecular representations
- Easy integration with additional transformations and file formats
- A test suite and documentation to support open-source collaboration

### 1.3 Intended Audience
This document is intended for developers, maintainers, and contributors. It assumes familiarity with Python programming, file I/O, and basic object-oriented design principles.

---

## 2. System Overview

### 2.1 Problem Statement
Researchers often work with multiple file formats (MDF, CAR, PDB) that describe both the geometry and force-field parameters of molecular systems. These files need to be transformed (e.g., grid replication, force-field updates) while preserving consistency between the geometry and metadata. The goal is to build a unified, modular package that can perform these tasks reliably and be extended in the future.

### 2.2 Use Cases
- **Grid Replication:**  
  Create a 3D grid (e.g., 8×8×8) of replicated molecules by reading a template molecule from CAR/MDF files and outputting updated files with new periodic boundary conditions (PBC).

- **Force-Field Updates:**  
  Update force-field type fields in MDF/CAR files based on a charge-to-FF type mapping provided by the user.

- **Charge Updates:**  
  Update atomic charges in MDF/CAR files using a mapping from force-field types to corrected charges.

- **Format Conversions & Validation:**  
  Validate and convert between different molecular file formats, ensuring consistency in atom numbering, residue naming, and connectivity.

---

## 3. Architecture Overview

### 3.1 High-Level Architecture
The MolSAIC package is organized into distinct modules, each responsible for one aspect of the ETL (Extract, Transform, Load) workflow:
- **Parsers:** Extract data from input files (MDF, CAR, PDB).
- **Models:** Represent molecular entities using object-oriented classes (Atom, Molecule, System).
- **Transformers:** Perform various data transformations (e.g., grid replication, updating force-field types/charges).
- **Writers:** Write transformed data back to file formats (MDF, CAR).
- **CLI & Configuration:** Provide a unified command-line interface and configuration management.

### 3.2 Package Directory Structure
```
molsaic/
├── __init__.py
├── cli.py              # Main command-line interface entry point
├── config.py           # Configuration defaults and logging setup
├── models/
│   ├── __init__.py
│   ├── atom.py         # Atom class definition
│   ├── molecule.py     # Molecule class definition (includes bbox, replication methods)
│   └── system.py       # System class definition (holds Molecule objects, overall PBC, grid generation)
├── parsers/
│   ├── __init__.py
│   ├── mdf_parser.py   # Functions/classes to parse MDF files
│   ├── car_parser.py   # Functions/classes to parse CAR files
│   └── pdb_parser.py   # Functions/classes to parse PDB files (if needed)
├── writers/
│   ├── __init__.py
│   ├── mdf_writer.py   # Functions to write MDF files
│   └── car_writer.py   # Functions to write CAR files
├── transformers/
│   ├── __init__.py
│   ├── grid.py         # Grid replication functions (using Molecule and System)
│   ├── update_ff.py    # Updates for force-field type fields (charge-to-FF mapping)
│   └── update_charges.py  # Updates for atomic charges (FF-to-charge mapping)
└── tests/
    ├── __init__.py
    ├── test_parsers.py # Unit tests for parsers
    ├── test_models.py  # Unit tests for Atom, Molecule, System
    └── test_transformers.py  # Unit tests for grid replication and update functions
```

---

## 4. Module Breakdown

### 4.1 Parsers Module
- **mdf_parser.py:**  
  - **Responsibility:** Read MDF files, extract headers, and build a dictionary of force-field data.
  - **Key Functions:**  
    - `parse_mdf(filename)`: Returns header information and a dictionary keyed by (residue, atom_name).

- **car_parser.py:**  
  - **Responsibility:** Read CAR files using fixed-width formatting, extract atom coordinates, and group atoms into molecule blocks.
  - **Key Functions:**  
    - `parse_car(filename)`: Returns the header lines, a list of molecule blocks (each block is a list of atom dictionaries), and PBC coordinates if available.

- **pdb_parser.py (optional):**  
  - **Responsibility:** Parse PDB files to extract atom data and create dictionary representations for use in transformations.
  - **Key Functions:**  
    - `parse_pdb(pdb_file)`: Returns a list of atom dictionaries.

### 4.2 Models Module
- **atom.py:**  
  - **Atom Class:**  
    - **Attributes:** `atom_name`, `x`, `y`, `z`, `residue_name`, `residue_number`, `atom_type`, `element`, `charge`
    - **Key Methods:**  
      - `copy()`: Return a deep copy of the atom.
      - `as_dict()`: Serialize atom data to a dictionary.

- **molecule.py:**  
  - **Molecule Class:**  
    - **Attributes:** `atoms` (list of Atom objects)
    - **Key Methods:**  
      - `compute_bbox()`: Compute the bounding box, center, and size.
      - `replicate(offset, center)`: Create a new Molecule instance by translating all atoms by a given offset (based on center).

- **system.py:**  
  - **System Class:**  
    - **Attributes:**  
      - `mdf_data`: Force-field dictionary from MDF parsing.
      - `molecules`: List of Molecule objects (e.g., replicated grid).
      - `pbc`: Periodic boundary conditions (tuple: dimensions, angles, cell type).
    - **Key Methods:**  
      - `generate_grid(template_molecule, grid_dims, gap)`: Replicates the template molecule into a grid and sets the PBC.
      - `build_mdf_header()` / `build_mdf_footer()`: Create header/footer for MDF output.
      - `build_car_header()`: Create header for CAR output.
      - `generate_mdf_lines(base_name, residue_mapping=None)`: Format MDF lines for each molecule.
      - `generate_car_lines()`: Format CAR lines for each molecule.

### 4.3 Transformers Module
- **grid.py:**  
  - **Responsibility:** Use the Molecule and System classes to replicate molecules in a grid.
  - **Functionality:**  
    - Calculate spacing from bounding box and gap.
    - Translate the template molecule to each grid cell center.
    - Update overall system PBC.

- **update_ff.py:**  
  - **Responsibility:** Update force-field type fields in MDF and CAR files.
  - **Functionality:**  
    - Accept a mapping (charge, element) → force-field type.
    - Parse file lines, update fields, and reformat with fixed-width output.

- **update_charges.py:**  
  - **Responsibility:** Update atomic charges in MDF and CAR files.
  - **Functionality:**  
    - Accept a mapping from force-field type to corrected charges.
    - Modify file lines and ensure proper spacing/formatting.

### 4.4 Writers Module
- **mdf_writer.py:**  
  - **Responsibility:** Write MDF file output from formatted lines.
  - **Key Function:**  
    - `write_mdf_file(output_filename, mdf_lines)`

- **car_writer.py:**  
  - **Responsibility:** Write CAR file output from formatted lines.
  - **Key Function:**  
    - `write_car_file(output_filename, car_lines)`

### 4.5 CLI and Configuration
- **cli.py:**  
  - **Responsibility:** Serve as the entry point for command-line operations.
  - **Design:**  
    - Use Python’s `argparse` to support subcommands (e.g., `grid`, `update-ff`, `update-charges`).
    - Each subcommand will call the relevant modules (parsers, transformers, writers) to execute the desired task.
  
- **config.py:**  
  - **Responsibility:** Provide default parameters, logging configuration, and possibly load user configuration (e.g., JSON/YAML files).

---

## 5. Data Flow (ETL)

1. **Extract:**  
   - Use the parsers to read input files:
     - MDF files → force-field data dictionary.
     - CAR files → list of molecule blocks (atoms as dictionaries).
     - PDB files (if used) → atom dictionaries.
   
2. **Transform:**  
   - Convert parsed atom dictionaries to Atom objects.
   - Build Molecule objects from lists of Atoms.
   - Create a System object using the MDF force-field data.
   - Use the System’s `generate_grid()` method to replicate the template Molecule into a grid.
   - Optionally, apply force-field or charge update transformations using mapping dictionaries.
   
3. **Load:**  
   - Generate output lines (MDF and CAR) using the System’s generation methods.
   - Write output files with the writers.

---

## 6. Command-Line Interface (CLI) Usage Examples

- **Grid Replication Example:**
  ```bash
  python -m molsaic.cli grid --mdf input.mdf --car input.car --grid 8 --gap 2.0 --output_mdf grid_box.mdf --output_car grid_box.car
  ```

- **Force-Field Update Example:**
  ```bash
  python -m molsaic.cli update-ff --car input.car --output updated.car --mapping mapping.json
  ```

- **Charge Update Example:**
  ```bash
  python -m molsaic.cli update-charges --mdf input.mdf --output updated.mdf --mapping charge_mapping.json
  ```

Each subcommand should provide help text (using argparse’s built-in help) explaining the required arguments and options.

---

## 7. Testing & Documentation

### 7.1 Testing
- **Unit Tests:**  
  Write unit tests for each module in the `tests/` directory.
  - **Parsers Tests:** Validate that sample MDF/CAR/PDB files are correctly parsed.
  - **Models Tests:** Verify Atom, Molecule, and System methods (e.g., bounding box calculation, replication).
  - **Transformers Tests:** Ensure that force-field and charge updates correctly modify sample data.
  
- **Continuous Integration:**  
  Set up CI (e.g., GitHub Actions) to run tests on each commit or pull request.

### 7.2 Documentation
- **Docstrings:**  
  Provide detailed docstrings for all functions and classes.
- **README:**  
  Create a README.md that explains the purpose of the package, usage examples, installation instructions, and contribution guidelines.
- **API Documentation:**  
  Optionally, use tools such as Sphinx to generate API documentation from the docstrings.

---

## 8. Future Extensions and Considerations

- **Additional File Formats:**  
  Extend support to other file formats (e.g., CIF, XYZ) by adding new parser and writer modules.
  
- **Visualization:**  
  Integrate with visualization tools (e.g., PyMOL, VMD) to preview structures.
  
- **Advanced Transformations:**  
  Add features for energy minimization, molecular dynamics simulation preparation, or structure validation.

- **Community Contributions:**  
  Host the project on GitHub with clear contribution guidelines, an issue tracker, and a roadmap for future features.

---

## 9. Appendix

### 9.1 Sample Mapping Files
- **Force-Field Type Mapping (charge_to_fftype):**
  ```json
  {
    "(-0.27, C)": "CT3",
    "(-0.08, C)": "CT2",
    "(0.0, N)": "NR3",
    "(0.4, C)": "CA",
    "(0.25, C)": "CA",
    "(0.3, C)": "CA",
    "(0.09, H)": "HA3",
    "(0.089, H)": "HA2",
    "(0.05, H)": "hiff",
    "(-0.15, H)": "cge"
  }
  ```

- **Charge Mapping (ff_to_charge):**
  ```json
  {
    "HA2": 0.09,
    "CT3": -0.27,
    "CT2": -0.08
  }
  ```

### 9.2 Logging & Debugging
- Configure logging centrally in `config.py` so that all modules use a consistent logging format.
- Include options for verbose/debug mode via CLI flags.

---

# Conclusion

This design document outlines a modular, extensible system for processing molecular data files. The clear separation of concerns (parsing, modeling, transformation, writing, and CLI) ensures that the system is scalable and maintainable. The package will support a variety of tasks now (grid replication, force-field updates, charge updates) and be flexible enough to incorporate future enhancements.

Developers should use this document as a blueprint for implementation and further extension, ensuring that each module is well tested and documented before integration into the public GitHub repository for collaborative development.

---

This document, along with the sample code snippets and directory structure, should provide your development team with all the necessary information to start building and integrating the MolSAIC package.
