# MolTools Architecture Evolution: From File-Based to Object-Based Transformations

This document outlines the architectural evolution of the MolTools package from a file-based transformation approach to an object-based pipeline architecture. It serves as a guide for developers working on implementing Tasks 17-25.

## Current Architecture (File-Based)

In the current architecture, each transformer operates directly on files:

```
Input Files → Parser → Transform → Writer → Output Files
```

### Advantages
- Simple, straightforward flow
- Each transformation is independent
- Low memory overhead (only loads what's needed)
- Easy to understand for basic use cases

### Limitations
- Multiple transformations require intermediate files
- Repeated parsing/writing for complex workflows
- No object representation throughout the pipeline
- Limited ability to chain transformations efficiently

## Proposed Architecture (Object-Based Pipeline)

The new architecture centers around a System object that represents the complete molecular system in memory:

```
Input Files → System Object → Pipeline Transformations → Output Files 
```

### Key Components

#### 1. System Object Enhancements
The System class will become the central data model with methods for all transformations:
```python
class System:
    def update_ff_types(self, mapping):
        # Transform force-field types directly on the system
        
    def update_charges(self, mapping):
        # Transform charges directly on the system
        
    def to_files(self, output_car, output_mdf):
        # Write current state to files
```

#### 2. MolecularPipeline
A new pipeline class to chain operations with a fluent API:
```python
class MolecularPipeline:
    def load(self, car_file, mdf_file):
        # Load files into a System object
        return self  # for chaining
        
    def update_ff_types(self, mapping):
        # Apply transformation
        return self  # for chaining
        
    def update_charges(self, mapping):
        # Apply transformation
        return self  # for chaining
        
    def generate_grid(self, grid_dims, gap):
        # Apply transformation
        return self  # for chaining
        
    def save(self, car_file, mdf_file):
        # Save final state
        return result
```

### Debugging Features
- Intermediate file output capability
- Progress tracking and logging
- State snapshots for complex workflows

### Backward Compatibility
The file-based approach will be preserved through:
1. Moving existing file-based methods to a legacy/archive package
2. Adding a compatibility layer that provides the same API
3. Updating the CLI to support both approaches with a `--object-mode` flag

## Implementation Strategy

### Phase 1: Core Infrastructure
- Enhance System class with transformation methods
- Create factory methods for System creation
- Implement initial Pipeline class
- Add basic tests for the core functionality

### Phase 2: Transformer Integration
- Refactor existing transformers to use the object model
- Move file-based approaches to legacy package
- Create compatibility layer
- Update documentation

### Phase 3: CLI and Integration
- Update CLI to support both approaches
- Add debug flags and features
- Expand test coverage
- Add example scripts

### Phase 4: Advanced Features
- Add performance optimizations
- Implement parallel processing
- Add visualization integration
- Create plugin system

## Usage Examples

### File-Based Approach (Legacy)
```python
from moltools.transformers.update_ff import update_ff_types
from moltools.transformers.update_charges import update_charges

# Step 1: Update force-field types (creates temp file)
update_ff_types(
    car_file="input.car", 
    mdf_file="input.mdf", 
    output_car="temp.car", 
    output_mdf="temp.mdf",
    mapping_file="ff_mapping.json"
)

# Step 2: Update charges (creates final output)
update_charges(
    car_file="temp.car", 
    mdf_file="temp.mdf", 
    output_car="output.car", 
    output_mdf="output.mdf",
    mapping_file="charge_mapping.json"
)
```

### Object-Based Approach (New)
```python
from moltools.pipeline import MolecularPipeline

# Chain operations without intermediate files
MolecularPipeline().load("input.car", "input.mdf") \
    .update_ff_types(mapping_file="ff_mapping.json") \
    .update_charges(mapping_file="charge_mapping.json") \
    .save("output.car", "output.mdf")
```

### With Debug Output
```python
from moltools.pipeline import MolecularPipeline

# Chain operations with debug files at each step
pipeline = MolecularPipeline(debug=True, debug_prefix="debug_")
pipeline.load("input.car", "input.mdf")
pipeline.update_ff_types(mapping_file="ff_mapping.json")  # Creates debug_1_*.car/mdf
pipeline.update_charges(mapping_file="charge_mapping.json")  # Creates debug_2_*.car/mdf
pipeline.save("output.car", "output.mdf")
```

## Memory Considerations

For very large systems, the pipeline will include options to:
1. Use memory-efficient data structures
2. Support partial loading of systems
3. Implement parallel processing for expensive operations
4. Provide checkpoint capability to save/restore state

## Testing Strategy

The testing strategy will cover:
1. Unit tests for individual components
2. Integration tests for chained operations
3. Performance benchmarks comparing approaches
4. Stress tests with very large systems
5. Compatibility tests with the legacy API

This comprehensive approach ensures the new architecture provides significant benefits while maintaining compatibility with existing code.