# Repository Organization Plan

This document outlines the plan for reorganizing the MolTools repository to follow best practices for Python projects.

## Current Structure Issues

The current repository structure has several issues:
- Test files are scattered (both in moltools/tests and tests/)
- Example scripts are mixed with test scripts in the root directory
- Documentation is not well organized
- Benchmarks are not separated from examples
- No proper packaging configuration

## Proposed Directory Structure

```
moltools/
├── .github/                     # GitHub workflows and templates
│   └── workflows/               # CI/CD configuration
├── docs/                        # Documentation 
│   ├── api/                     # API reference docs
│   ├── tutorials/               # Tutorial markdown files
│   ├── architecture/            # Architecture documentation
│   └── examples/                # Example usage docs
├── examples/                    # Example scripts
│   ├── basic/                   # Basic usage examples
│   ├── advanced/                # Advanced usage examples
│   └── tutorials/               # Code for tutorials
├── benchmarks/                  # Performance benchmarking scripts
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── data/                    # Test data files
├── moltools/                    # Main package
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── pipeline.py
│   ├── models/                  # Data models
│   ├── parsers/                 # File parsers
│   ├── writers/                 # File writers
│   ├── transformers/            # Transformations
│   │   └── legacy/              # Legacy implementations
│   ├── templates/               # Pipeline templates
│   └── utils/                   # Utility functions
├── samplefiles/                 # Sample data files for examples/tests
│   ├── 1NEC/
│   └── 3NEC/ 
├── mappings/                    # Mapping files
├── .gitignore
├── LICENSE
├── MANIFEST.in                  # List of files to include in package
├── pyproject.toml               # Build system requirements
├── README.md
├── setup.py                     # Package setup script
└── setup.cfg                    # Package metadata and options
```

## Implementation Plan

### 1. Create Directory Structure

- Create any missing directories from the structure above
- Move files to their appropriate locations

### 2. Update Setup and Package Files

- Update setup.py with proper package metadata
- Create setup.cfg and pyproject.toml for modern packaging
- Create MANIFEST.in for package data

### 3. Move and Organize Test Files

- Move all test files to tests/ directory
- Organize into unit/ and integration/ subdirectories
- Move test data to tests/data/

### 4. Organize Examples

- Move all example scripts to examples/ directory
- Organize into basic/ and advanced/ subdirectories
- Create tutorial examples

### 5. Organize Documentation

- Move all documentation to docs/ directory
- Organize API reference, tutorials, and architecture docs
- Create index files for each section

### 6. Update Imports

- Update import statements in all files to reflect new structure
- Ensure relative imports are used correctly within package

### 7. Add Package Configuration

- Create .gitignore with standard Python patterns
- Add linting configuration
- Add CI/CD configuration (if using GitHub)

### 8. Update README

- Update README.md with new structure information
- Add section about project organization

## Migration Steps

1. Create backup of current state
2. Create new directory structure 
3. Move files one section at a time, ensuring tests pass after each section
4. Update imports and ensure tests still pass
5. Create new configuration files
6. Verify all functionality works in new structure
7. Update documentation to reflect new structure

## Benefits

- Better organization makes the codebase easier to navigate
- Separation of concerns improves maintainability
- Standard structure makes the project more approachable for new contributors
- Proper packaging configuration makes installation easier
- Organizing tests improves test maintainability