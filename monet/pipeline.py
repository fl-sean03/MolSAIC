"""
MolecularPipeline module providing a fluent API for chaining transformations.
"""

import os
import logging
from typing import Tuple, Optional, Union, Dict, Any, List

from .models.system import System
from .external_tools.msi2namd import MSI2NAMDTool

logger = logging.getLogger(__name__)

class MolecularPipeline:
    """
    A pipeline for processing molecular data with a fluent API.
    
    The MolecularPipeline class provides a convenient way to chain multiple
    transformations on a molecular system without creating intermediate files.
    It supports debugging, progress tracking, and simplified input/output handling.
    
    Attributes:
        system (System): The molecular system being processed.
        debug (bool): Whether to generate intermediate debug files.
        debug_prefix (str): Prefix for debug files.
        transform_count (int): Counter for tracking transformation steps.
    """
    
    def __init__(self, debug: bool = False, debug_prefix: str = "debug_", keep_workspace: bool = False):
        """
        Initialize a new MolecularPipeline.
        
        Args:
            debug (bool, optional): Enable debug mode with intermediate file output. Default is False.
            debug_prefix (str, optional): Prefix for debug files. Default is "debug_".
            keep_workspace (bool, optional): Keep workspaces after processing. Default is False.
        """
        self.system = None
        self.debug = debug
        self.debug_prefix = debug_prefix
        self.transform_count = 0
        self.namd_files = {}  # Store paths to generated NAMD files
        self.keep_workspace = keep_workspace  # Flag to keep workspaces
        
        if debug:
            logger.info(f"Debug mode enabled. Files will be saved with prefix: {debug_prefix}")
        if keep_workspace:
            logger.info("Workspace retention enabled. All intermediate workspaces will be kept.")
    
    def load(self, car_file: str, mdf_file: str) -> 'MolecularPipeline':
        """
        Load molecular data from CAR and MDF files.
        
        Args:
            car_file (str): Path to the CAR file.
            mdf_file (str): Path to the MDF file.
            
        Returns:
            MolecularPipeline: Self reference for method chaining.
            
        Raises:
            FileNotFoundError: If either file does not exist.
            ValueError: If file parsing fails.
        """
        logger.info(f"Loading from files: {car_file}, {mdf_file}")
        
        self.system = System.system_from_files(car_file, mdf_file)
        logger.info(f"System loaded: {len(self.system.molecules)} molecules")
        
        # Reset transformation counter when loading new data
        self.transform_count = 0
        
        return self
    
    def save(self, output_car: str, output_mdf: str, base_name: str = "MOL", 
             residue_mapping: Optional[Dict] = None) -> 'MolecularPipeline':
        """
        Save the current system state to CAR and MDF files.
        
        Args:
            output_car (str): Path to the output CAR file.
            output_mdf (str): Path to the output MDF file.
            base_name (str, optional): Base name for molecules. Default is "MOL".
            residue_mapping (dict, optional): Mapping for residue names. Default is None.
            
        Returns:
            MolecularPipeline: Self reference for method chaining.
            
        Raises:
            ValueError: If no system has been loaded.
            IOError: If writing to files fails.
        """
        if self.system is None:
            raise ValueError("No system has been loaded. Call load() first.")
        
        logger.info(f"Saving to files: {output_car}, {output_mdf}")
        self.system.to_files(output_car, output_mdf, base_name, residue_mapping)
        
        return self
    
    def update_ff_types(self, mapping_file: str) -> 'MolecularPipeline':
        """
        Update force-field types based on a mapping.
        
        Args:
            mapping_file (str): Path to the JSON mapping file.
            
        Returns:
            MolecularPipeline: Self reference for method chaining.
            
        Raises:
            ValueError: If no system has been loaded.
            FileNotFoundError: If the mapping file does not exist.
        """
        if self.system is None:
            raise ValueError("No system has been loaded. Call load() first.")
        
        logger.info(f"Updating force-field types using mapping: {mapping_file}")
        update_count = self.system.update_ff_types(mapping_file)
        logger.info(f"Updated {update_count} force-field types")
        
        self.transform_count += 1
        self._save_debug_files()
        
        return self
    
    def update_charges(self, mapping_file: str) -> 'MolecularPipeline':
        """
        Update atomic charges based on a mapping.
        
        Args:
            mapping_file (str): Path to the JSON mapping file.
            
        Returns:
            MolecularPipeline: Self reference for method chaining.
            
        Raises:
            ValueError: If no system has been loaded.
            FileNotFoundError: If the mapping file does not exist.
        """
        if self.system is None:
            raise ValueError("No system has been loaded. Call load() first.")
        
        logger.info(f"Updating charges using mapping: {mapping_file}")
        update_count = self.system.update_charges(mapping_file)
        logger.info(f"Updated {update_count} charges")
        
        self.transform_count += 1
        self._save_debug_files()
        
        return self
    
    def generate_grid(self, grid_dims: Tuple[int, int, int] = (8, 8, 8), 
                     gap: float = 2.0) -> 'MolecularPipeline':
        """
        Generate a grid replication of the system's first molecule.
        
        Args:
            grid_dims (tuple, optional): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
            gap (float, optional): Gap between molecules in Angstroms. Default is 2.0.
            
        Returns:
            MolecularPipeline: Self reference for method chaining.
            
        Raises:
            ValueError: If no system has been loaded or it has no molecules.
        """
        if self.system is None or not self.system.molecules:
            raise ValueError("No system with molecules has been loaded. Call load() first.")
        
        logger.info(f"Generating grid with dimensions: {grid_dims}, gap: {gap}Å")
        
        # Use the first molecule as template
        template_molecule = self.system.molecules[0]
        
        # Generate grid
        self.system.generate_grid(template_molecule, grid_dims, gap)
        
        self.transform_count += 1
        self._save_debug_files()
        
        return self
    
    def _save_debug_files(self) -> None:
        """
        Save intermediate debug files if debug mode is enabled.
        """
        if not self.debug or self.system is None:
            return
        
        # Create debug file paths with step number
        debug_car = f"{self.debug_prefix}{self.transform_count}_output.car"
        debug_mdf = f"{self.debug_prefix}{self.transform_count}_output.mdf"
        
        # Ensure directory exists
        debug_dir = os.path.dirname(self.debug_prefix)
        if debug_dir and not os.path.exists(debug_dir):
            os.makedirs(debug_dir, exist_ok=True)
        
        logger.info(f"Saving debug files for step {self.transform_count}: {debug_car}, {debug_mdf}")
        self.system.to_files(debug_car, debug_mdf, f"DEBUG_{self.transform_count}")
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate the current state of the system.
        
        This method checks for common issues and inconsistencies in the molecular system.
        
        Returns:
            Dict: Validation results with issues found.
        """
        if self.system is None:
            raise ValueError("No system has been loaded. Call load() first.")
        
        validation_results = {
            "valid": True,
            "issues": [],
            "statistics": {},
            "warnings": []
        }
        
        # Check if system has molecules
        if not self.system.molecules:
            validation_results["valid"] = False
            validation_results["issues"].append("System has no molecules")
            return validation_results
        
        # Collect statistics
        total_atoms = 0
        atom_types = set()
        elements = set()
        charges = set()
        residue_names = set()
        
        # Check each molecule
        for i, molecule in enumerate(self.system.molecules):
            # Check if molecule has atoms
            if not molecule.atoms:
                validation_results["issues"].append(f"Molecule {i} has no atoms")
                validation_results["valid"] = False
                continue
            
            # Check atoms in the molecule
            for atom in molecule.atoms:
                total_atoms += 1
                atom_types.add(atom.atom_type)
                elements.add(atom.element)
                charges.add(atom.charge)
                residue_names.add(atom.residue_name)
                
                # Check for missing critical data
                if not atom.element:
                    validation_results["issues"].append(f"Atom {atom.atom_name} in molecule {i} has no element")
                    validation_results["valid"] = False
                
                if not atom.atom_type:
                    validation_results["warnings"].append(f"Atom {atom.atom_name} in molecule {i} has no atom_type")
        
        # Check PBC
        if not self.system.pbc:
            validation_results["warnings"].append("System has no periodic boundary conditions (PBC)")
        
        # Add statistics
        validation_results["statistics"] = {
            "molecules": len(self.system.molecules),
            "total_atoms": total_atoms,
            "unique_atom_types": len(atom_types),
            "unique_elements": len(elements),
            "unique_charges": len(charges),
            "unique_residues": len(residue_names),
            "pbc": self.system.pbc
        }
        
        # Report validation results
        if validation_results["valid"]:
            logger.info(f"Validation passed: {total_atoms} atoms in {len(self.system.molecules)} molecules")
        else:
            logger.warning(f"Validation failed with {len(validation_results['issues'])} issues")
            for issue in validation_results["issues"]:
                logger.warning(f"  - {issue}")
        
        if validation_results["warnings"]:
            logger.warning(f"Validation passed with {len(validation_results['warnings'])} warnings")
            for warning in validation_results["warnings"]:
                logger.warning(f"  - {warning}")
        
        return validation_results
    
    def get_system(self) -> System:
        """
        Get the current system object.
        
        Returns:
            System: The current molecular system.
            
        Raises:
            ValueError: If no system has been loaded.
        """
        if self.system is None:
            raise ValueError("No system has been loaded. Call load() first.")
        
        return self.system
    
    def convert_to_namd(self, 
                        output_dir: Optional[str] = None, 
                        residue_name: Optional[str] = None,
                        parameter_file: Optional[str] = None,
                        charge_groups: bool = False,
                        cleanup_workspace: bool = True,
                        **kwargs) -> 'MolecularPipeline':
        """
        Convert the current system to NAMD format using MSI2NAMD.
        
        This method converts the current molecular system to NAMD format (PDB/PSF files)
        using the MSI2NAMD external tool. The conversion is performed in a workspace
        directory and output files are copied to the specified output directory.
        
        Args:
            output_dir (str, optional): Directory to store output files. Default is current directory.
            residue_name (str, optional): Residue name to use in the output PDB file.
            parameter_file (str, optional): Path to a parameter file for the conversion.
            charge_groups (bool, optional): Whether to include charge groups. Default is False.
            cleanup_workspace (bool, optional): Whether to clean up the workspace. Default is True.
            **kwargs: Additional parameters to pass to MSI2NAMD.
            
        Returns:
            MolecularPipeline: Self reference for method chaining.
            
        Raises:
            ValueError: If no system has been loaded.
            RuntimeError: If the conversion fails.
        """
        if self.system is None:
            raise ValueError("No system has been loaded. Call load() first.")
            
        if output_dir is None:
            output_dir = os.getcwd()
            
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # Set default residue name if not provided
        if residue_name is None and self.system.molecules:
            # Use the residue name from the first atom of the first molecule
            first_mol = self.system.molecules[0]
            if first_mol.atoms:
                residue_name = first_mol.atoms[0].residue_name
                
        logger.info(f"Converting system to NAMD format (output dir: {output_dir})")
        
        try:
            # Create MSI2NAMD tool instance, respecting the pipeline's keep_workspace setting
            # if self.keep_workspace is True, this overrides the cleanup_workspace parameter
            if self.keep_workspace:
                cleanup_workspace = False
            
            # Use the global session workspace
            from moltools import config as main_config
            workspace_manager = main_config.session_workspace
            self._msi2namd_tool = MSI2NAMDTool(workspace_manager=workspace_manager)
            
            # Execute the conversion
            result = self._msi2namd_tool.execute(
                system=self.system,
                residue_name=residue_name,
                parameter_file=parameter_file,
                charge_groups=charge_groups,
                output_dir=output_dir,
                cleanup=cleanup_workspace,
                **kwargs
            )
            
            # Since we're using the global workspace, don't need to show workspace message here
            
            # Add conversion result information to pipeline state
            self.namd_files = {
                'pdb_file': os.path.join(output_dir, os.path.basename(result.get('pdb_file', ''))),
                'psf_file': os.path.join(output_dir, os.path.basename(result.get('psf_file', ''))),
                'namd_file': os.path.join(output_dir, os.path.basename(result.get('namd_file', ''))),
                'param_file': os.path.join(output_dir, os.path.basename(result.get('param_file', ''))),
            }
            
            # Log success
            file_paths = [path for path in self.namd_files.values() if path and os.path.basename(path)]
            if file_paths:
                logger.info(f"NAMD conversion successful. Files created: {', '.join(os.path.basename(f) for f in file_paths)}")
            else:
                logger.warning("NAMD conversion completed but no output files were found.")
            
        except (ValueError, RuntimeError) as e:
            logger.error(f"NAMD conversion failed: {str(e)}")
            
            # Using the global workspace now, no need for tool-specific messages
            
            raise
            
        # Increment transformation counter
        self.transform_count += 1
        self._save_debug_files()
        
        return self
    
    def save_checkpoint(self, checkpoint_file: str) -> 'MolecularPipeline':
        """
        Save the current state of the pipeline to a checkpoint file.
        
        Args:
            checkpoint_file (str): Path to the checkpoint file.
            
        Returns:
            MolecularPipeline: Self reference for method chaining.
            
        Raises:
            ValueError: If no system has been loaded.
            IOError: If saving the checkpoint fails.
        """
        if self.system is None:
            raise ValueError("No system has been loaded. Call load() first.")
        
        import pickle
        
        # Create checkpoint data
        checkpoint_data = {
            'system': self.system,
            'transform_count': self.transform_count,
            'debug': self.debug,
            'debug_prefix': self.debug_prefix,
            'namd_files': self.namd_files
        }
        
        # Save checkpoint
        try:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            logger.info(f"Checkpoint saved to: {checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {str(e)}")
            raise IOError(f"Failed to save checkpoint: {str(e)}")
        
        return self
    
    @classmethod
    def load_checkpoint(cls, checkpoint_file: str) -> 'MolecularPipeline':
        """
        Load a pipeline state from a checkpoint file.
        
        Args:
            checkpoint_file (str): Path to the checkpoint file.
            
        Returns:
            MolecularPipeline: A new pipeline with the loaded state.
            
        Raises:
            FileNotFoundError: If the checkpoint file does not exist.
            ValueError: If the checkpoint file is invalid.
        """
        import pickle
        
        # Load checkpoint
        try:
            with open(checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_file}")
        except Exception as e:
            raise ValueError(f"Invalid checkpoint file: {str(e)}")
        
        # Verify checkpoint data
        required_keys = ['system', 'transform_count', 'debug', 'debug_prefix']
        for key in required_keys:
            if key not in checkpoint_data:
                raise ValueError(f"Invalid checkpoint data: missing key '{key}'")
        
        # Create a new pipeline with the loaded state
        pipeline = cls(debug=checkpoint_data['debug'], debug_prefix=checkpoint_data['debug_prefix'])
        pipeline.system = checkpoint_data['system']
        pipeline.transform_count = checkpoint_data['transform_count']
        
        # Restore namd_files if available (backwards compatibility with older checkpoints)
        if 'namd_files' in checkpoint_data:
            pipeline.namd_files = checkpoint_data['namd_files']
        
        logger.info(f"Checkpoint loaded from: {checkpoint_file}")
        logger.info(f"Restored pipeline with {len(pipeline.system.molecules)} molecules, "
                   f"transform count: {pipeline.transform_count}")
        
        return pipeline