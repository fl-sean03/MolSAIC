"""
Module for grid replication of molecules.
Supports both object-based and file-based approaches.
"""

import logging
from typing import Dict, List, Tuple, Optional, Union

from ..models.molecule import Molecule
from ..models.system import System
from .legacy.grid import grid_from_files as legacy_grid_from_files
from .legacy.grid import generate_grid_files as legacy_generate_grid_files

logger = logging.getLogger(__name__)

def generate_grid_obj(system: System, template_molecule: Molecule,
                     grid_dims: Tuple[int, int, int] = (8, 8, 8),
                     gap: float = 2.0) -> int:
    """
    Generate a grid replication of a template molecule directly in a System object.
    
    Args:
        system (System): The molecular system to update.
        template_molecule (Molecule): The template molecule to replicate.
        grid_dims (tuple): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
        gap (float): Gap between molecules in Angstroms. Default is 2.0.
        
    Returns:
        int: Number of molecules in the grid.
        
    Raises:
        ValueError: If the system or template_molecule is invalid.
    """
    if system is None:
        raise ValueError("System object cannot be None")
    
    if not isinstance(template_molecule, Molecule):
        raise ValueError("template_molecule must be a Molecule instance")
    
    # Generate the grid
    system.generate_grid(template_molecule, grid_dims, gap)
    
    return len(system.molecules)

def generate_grid_files(car_file: str, mdf_file: str, 
                       output_car: str, output_mdf: str, 
                       grid_dims: Tuple[int, int, int] = (8, 8, 8), 
                       gap: float = 2.0, 
                       base_name: str = "MOL",
                       object_mode: bool = False) -> Dict:
    """
    Generates grid files (CAR and MDF) from template files.
    Supports both file-based and object-based approaches.
    
    Args:
        car_file (str): Path to the input CAR file.
        mdf_file (str): Path to the input MDF file.
        output_car (str): Path to the output CAR file.
        output_mdf (str): Path to the output MDF file.
        grid_dims (tuple): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
        gap (float): Gap between molecules in Angstroms. Default is 2.0.
        base_name (str): Base name for molecules in the output files. Default is "MOL".
        object_mode (bool, optional): Use object-based approach. Default is False.
        
    Returns:
        dict: Dictionary with operation results.
    """
    results = {}
    
    try:
        if object_mode:
            # Object-based approach
            logger.info("Using object-based approach for grid generation")
            
            # Create a system from files
            system = System.system_from_files(car_file, mdf_file)
            
            # Use the first molecule as template
            if not system.molecules:
                raise ValueError(f"No molecules found in input files")
            
            template_molecule = system.molecules[0]
            logger.info(f"Using template molecule with {len(template_molecule.atoms)} atoms")
            
            # Generate grid
            system = System(system.mdf_data)  # Create a new system with the same MDF data
            system.generate_grid(template_molecule, grid_dims, gap)
            
            # Save results
            system.to_files(output_car, output_mdf, base_name)
            
            # Add results
            results['molecule_count'] = len(system.molecules)
            results['system'] = system
        else:
            # Legacy file-based approach
            logger.info("Using file-based approach for grid generation")
            legacy_generate_grid_files(
                car_file, mdf_file, output_car, output_mdf, 
                grid_dims, gap, base_name
            )
            
            # Load the resulting system to get the molecule count
            system = legacy_grid_from_files(car_file, mdf_file, grid_dims, gap)
            results['molecule_count'] = len(system.molecules)
        
        total_molecules = grid_dims[0] * grid_dims[1] * grid_dims[2]
        logger.info(f"Grid generation complete: {grid_dims[0]}x{grid_dims[1]}x{grid_dims[2]} = {total_molecules} molecules")
        logger.info(f"Output files: {output_car}, {output_mdf}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error generating grid files: {str(e)}")
        raise

def grid_from_files(car_file: str, mdf_file: str, 
                   grid_dims: Tuple[int, int, int] = (8, 8, 8),
                   gap: float = 2.0,
                   object_mode: bool = False) -> System:
    """
    Creates a grid System from CAR and MDF files.
    
    Args:
        car_file (str): Path to the CAR file with molecule geometry.
        mdf_file (str): Path to the MDF file with force-field data.
        grid_dims (tuple): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
        gap (float): Gap between molecules in Angstroms. Default is 2.0.
        object_mode (bool, optional): Use object-based approach. Default is False.
        
    Returns:
        System: A new System object containing the replicated molecules.
        
    Raises:
        FileNotFoundError: If CAR or MDF file does not exist.
        ValueError: If file parsing fails.
    """
    if object_mode:
        # Object-based approach
        logger.info("Using object-based approach for grid generation")
        
        # Load system from files
        system = System.system_from_files(car_file, mdf_file)
        
        if not system.molecules:
            raise ValueError(f"No molecules found in input files")
        
        # Use the first molecule as template
        template_molecule = system.molecules[0]
        logger.info(f"Using template molecule with {len(template_molecule.atoms)} atoms")
        
        # Create a new system with the template's MDF data
        result_system = System(system.mdf_data)
        
        # Generate grid
        result_system.generate_grid(template_molecule, grid_dims, gap)
        
        return result_system
    else:
        # Legacy file-based approach
        logger.info("Using file-based approach for grid generation")
        return legacy_grid_from_files(car_file, mdf_file, grid_dims, gap)