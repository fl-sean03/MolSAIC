"""
Legacy module for grid replication of molecules.
This module contains the original file-based transformation functions,
maintained for backward compatibility.

DEPRECATED: This file-based approach is deprecated and will be removed in 
version {version}. Please use the object-based pipeline instead.
"""

import logging
from ... import config
from moltools.models.molecule import Molecule
from moltools.models.system import System
from moltools.parsers.car_parser import parse_car, car_blocks_to_molecules
from moltools.parsers.mdf_parser import parse_mdf
from moltools.parsers.integration import combine_mdf_car_data
from moltools.writers.car_writer import write_car_file
from moltools.writers.mdf_writer import write_mdf_file

logger = logging.getLogger(__name__)

# Fix the docstring
__doc__ = __doc__.format(version=config.FILE_MODE_REMOVAL_VERSION)

def generate_grid(template_molecule, grid_dims=(8, 8, 8), gap=2.0):
    """
    Creates a new System with the template molecule replicated in a 3D grid.
    
    Args:
        template_molecule (Molecule): The template molecule to replicate.
        grid_dims (tuple): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
        gap (float): Gap between molecules in Angstroms. Default is 2.0.
        
    Returns:
        System: A new System object containing the replicated molecules.
        
    Raises:
        ValueError: If template_molecule is not a Molecule instance.
    """
    if not isinstance(template_molecule, Molecule):
        raise ValueError("template_molecule must be a Molecule instance")
    
    # Create a new System
    system = System()
    
    # Generate the grid of molecules
    system.generate_grid(template_molecule, grid_dims, gap)
    
    return system

def grid_from_files(car_file, mdf_file, grid_dims=(8, 8, 8), gap=2.0):
    """
    Creates a grid System from CAR and MDF files.
    
    Args:
        car_file (str): Path to the CAR file with molecule geometry.
        mdf_file (str): Path to the MDF file with force-field data.
        grid_dims (tuple): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
        gap (float): Gap between molecules in Angstroms. Default is 2.0.
        
    Returns:
        System: A new System object containing the replicated molecules.
        
    Raises:
        FileNotFoundError: If CAR or MDF file does not exist.
        ValueError: If file parsing fails.
    """
    # Parse the CAR file and convert to Molecule objects
    _, molecule_blocks, _ = parse_car(car_file)
    if not molecule_blocks:
        raise ValueError(f"No molecule blocks found in CAR file: {car_file}")
    
    # Parse the MDF file to get force-field data
    _, mdf_data = parse_mdf(mdf_file)
    
    # Combine CAR and MDF data to create molecules with connection information
    molecules = combine_mdf_car_data(mdf_data, molecule_blocks)
    if not molecules:
        raise ValueError(f"Failed to create molecules from CAR file: {car_file}")
    
    template_molecule = molecules[0]
    logger.info(f"Using template molecule with {len(template_molecule.atoms)} atoms")
    
    # Create a System with the force-field data
    system = System(mdf_data)
    
    # Generate the grid of molecules
    logger.info(f"Generating {grid_dims[0]}x{grid_dims[1]}x{grid_dims[2]} grid with {gap}Å gap...")
    system.generate_grid(template_molecule, grid_dims, gap)
    logger.info(f"Grid generation complete with {len(system.molecules)} molecules")
    
    return system

def generate_grid_files(car_file, mdf_file, output_car, output_mdf, 
                    grid_dims=(8, 8, 8), gap=2.0, base_name="MOL"):
    """
    Generates grid files (CAR and MDF) from template files.
    
    DEPRECATED: This function is deprecated and will be removed in version 
    {version}. Please use the object-based pipeline instead:
    
    pipeline = MolecularPipeline()
    pipeline.load(car_file, mdf_file)
        .generate_grid(grid_dims, gap)
        .save(output_car, output_mdf, base_name)
    
    Args:
        car_file (str): Path to the input CAR file.
        mdf_file (str): Path to the input MDF file.
        output_car (str): Path to the output CAR file.
        output_mdf (str): Path to the output MDF file.
        grid_dims (tuple): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
        gap (float): Gap between molecules in Angstroms. Default is 2.0.
        base_name (str): Base name for molecules in the output files. Default is "MOL".
        
    Returns:
        bool: True if successful, False otherwise.
    """.format(version=config.FILE_MODE_REMOVAL_VERSION)
    # Show deprecation warning
    config.show_file_mode_deprecation_warning(logger)
    
    try:
        # Create a grid System from the input files
        system = grid_from_files(car_file, mdf_file, grid_dims, gap)
        
        # Generate MDF file
        mdf_header = system.build_mdf_header()
        mdf_molecule_lines = system.generate_mdf_lines(base_name)
        mdf_footer = system.build_mdf_footer()
        mdf_lines = mdf_header + mdf_molecule_lines + mdf_footer
        
        # Generate CAR file
        car_header = system.build_car_header()
        car_molecule_lines = system.generate_car_lines()
        car_lines = car_header + car_molecule_lines
        
        # Write output files
        write_mdf_file(output_mdf, mdf_lines)
        write_car_file(output_car, car_lines)
        
        logger.info(f"Grid generation complete: {len(system.molecules)} molecules.")
        logger.info(f"Output MDF file: {output_mdf}")
        logger.info(f"Output CAR file: {output_car}")
        
        return True
    except Exception as e:
        logger.error(f"Error generating grid files: {str(e)}")
        raise