# MolSAIC Implementation Tasks

## Completed Tasks - Packmol Integration

1. ✅ Create `packmol.py` module in `src/external_tools/` directory
2. ✅ Implement `PackmolTool` class inheriting from `BaseExternalTool`
3. ✅ Implement required abstract methods:
   - ✅ `_get_tool_name()`
   - ✅ `validate_inputs()`
   - ✅ `prepare_inputs()`
   - ✅ `build_command()`
   - ✅ `process_output()`
4. ✅ Add configuration parameters in `src/external_tools/config.py`
5. ✅ Update `__init__.py` to expose the new tool
6. ✅ Create integration tests in `resources/tests/integration/`
7. ✅ Create usage example in `resources/examples/advanced/`
8. ✅ Document the tool API in `src/docs/api/`

## Current Tasks - Package Naming Fix

1. ✅ Fix package naming inconsistency between setup.py and imports
   - ✅ Change package name in setup.py from "monet" to "moltools"
   - ✅ Update entry_points in setup.py
   - ⬜ Reinstall package in development mode for testing (facing installation permission issues)
   - ✅ Create symlink as a workaround: `ln -s src moltools`
   - ⬜ Test CLI functionality with msi2namd command

## Completed Tasks - Project Rebranding to MolSAIC

1. ✅ Update package naming and branding from MONET/moltools to MolSAIC
   - ✅ Update setup.py
     - ✅ Change package name from "moltools" to "molsaic"
     - ✅ Update description to reflect new name
     - ✅ Update URLs and email addresses
     - ✅ Update entry_points from "moltools" to "molsaic"
   - ✅ Update documentation files
     - ✅ Update README.md title and description
     - ✅ Update ARCHITECTURE.md references 
     - ✅ Update IMPLEMENTATION_SUMMARY.md references
     - ✅ Update all other documentation files (READMEs, markdown docs)
   - ✅ Update core source code
     - ✅ Update config.py references (environment variables, workspace paths)
     - ✅ Update CLI description and workspace references
   - ✅ Update all remaining imports and references
     - ✅ Update key imports in msi2namd.py and cli.py
     - ✅ Replace all imports from "moltools" to "molsaic" across codebase
     - ✅ Replace "MolTools" or "MONET" with "MolSAIC" in all docstrings and READMEs
   - ✅ Create symlink from src to molsaic
   - ✅ Comprehensive rebranding verification
     - ✅ Verified all source code imports and references are updated
     - ✅ Confirmed all documentation references have been updated
     - ✅ Updated all environment variable references
     - ✅ Replaced all CLI command examples
     - ✅ Double-checked for any remaining references to old names

## Future Task Ideas

| Priority | Task | Description |
|----------|------|-------------|
| High | External Tool Integrations | Implement interfaces for PDB2PQR, Reduce, OpenMM, and Gaussian |
| High | Parallel Processing | Add support for multi-threading/processing for large molecular systems |
| Medium | Visualization | Integrate with common molecular visualization tools (VMD, PyMol, NGLView) |
| Medium | History Tracking | Implement undo/redo functionality and transformation history |
| Low | Batch Processing | Add capability to process multiple systems in batch mode |
| Low | Cloud Integration | Support for remote computation and storage options |

## Release Planning

* **v0.3.0**: Parallel processing and external tool expansion
* **v0.4.0**: Visualization integrations
* **v0.5.0**: History tracking and undo functionality
* **v1.0.0**: Feature complete with batch processing and cloud options