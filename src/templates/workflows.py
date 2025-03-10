"""
Templates and factory functions for common MolSAIC workflows.
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Union, Any

from ..pipeline import MolecularPipeline

logger = logging.getLogger(__name__)

def create_grid_pipeline(
    input_car: str,
    input_mdf: str,
    output_car: str,
    output_mdf: str,
    grid_dims: Tuple[int, int, int] = (8, 8, 8),
    gap: float = 2.0,
    debug: bool = False,
    debug_prefix: str = "debug_"
) -> MolecularPipeline:
    """
    Create a pipeline for grid replication.
    
    Args:
        input_car (str): Path to input CAR file.
        input_mdf (str): Path to input MDF file.
        output_car (str): Path to output CAR file.
        output_mdf (str): Path to output MDF file.
        grid_dims (tuple): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
        gap (float): Gap between molecules in Angstroms. Default is 2.0.
        debug (bool): Enable debug mode. Default is False.
        debug_prefix (str): Prefix for debug files. Default is "debug_".
        
    Returns:
        MolecularPipeline: A configured pipeline.
    """
    pipeline = MolecularPipeline(debug=debug, debug_prefix=debug_prefix)
    
    # Chain operations
    pipeline.load(input_car, input_mdf) \
            .generate_grid(grid_dims=grid_dims, gap=gap) \
            .save(output_car, output_mdf)
    
    return pipeline

def create_ff_update_pipeline(
    input_car: str,
    input_mdf: str,
    output_car: str,
    output_mdf: str,
    mapping_file: str,
    debug: bool = False,
    debug_prefix: str = "debug_"
) -> MolecularPipeline:
    """
    Create a pipeline for force-field updates.
    
    Args:
        input_car (str): Path to input CAR file.
        input_mdf (str): Path to input MDF file.
        output_car (str): Path to output CAR file.
        output_mdf (str): Path to output MDF file.
        mapping_file (str): Path to the mapping file.
        debug (bool): Enable debug mode. Default is False.
        debug_prefix (str): Prefix for debug files. Default is "debug_".
        
    Returns:
        MolecularPipeline: A configured pipeline.
    """
    pipeline = MolecularPipeline(debug=debug, debug_prefix=debug_prefix)
    
    # Chain operations
    pipeline.load(input_car, input_mdf) \
            .update_ff_types(mapping_file) \
            .save(output_car, output_mdf)
    
    return pipeline

def create_charge_update_pipeline(
    input_car: str,
    input_mdf: str,
    output_car: str,
    output_mdf: str,
    mapping_file: str,
    debug: bool = False,
    debug_prefix: str = "debug_"
) -> MolecularPipeline:
    """
    Create a pipeline for charge updates.
    
    Args:
        input_car (str): Path to input CAR file.
        input_mdf (str): Path to input MDF file.
        output_car (str): Path to output CAR file.
        output_mdf (str): Path to output MDF file.
        mapping_file (str): Path to the mapping file.
        debug (bool): Enable debug mode. Default is False.
        debug_prefix (str): Prefix for debug files. Default is "debug_".
        
    Returns:
        MolecularPipeline: A configured pipeline.
    """
    pipeline = MolecularPipeline(debug=debug, debug_prefix=debug_prefix)
    
    # Chain operations
    pipeline.load(input_car, input_mdf) \
            .update_charges(mapping_file) \
            .save(output_car, output_mdf)
    
    return pipeline

def create_complete_transformation_pipeline(
    input_car: str,
    input_mdf: str,
    output_car: str,
    output_mdf: str,
    ff_mapping_file: str,
    charge_mapping_file: str,
    grid_dims: Tuple[int, int, int] = (8, 8, 8),
    gap: float = 2.0,
    debug: bool = False,
    debug_prefix: str = "debug_",
    checkpoint_file: Optional[str] = None,
    validate_steps: bool = True
) -> MolecularPipeline:
    """
    Create a complete transformation pipeline with all steps.
    
    Args:
        input_car (str): Path to input CAR file.
        input_mdf (str): Path to input MDF file.
        output_car (str): Path to output CAR file.
        output_mdf (str): Path to output MDF file.
        ff_mapping_file (str): Path to the force-field mapping file.
        charge_mapping_file (str): Path to the charge mapping file.
        grid_dims (tuple): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
        gap (float): Gap between molecules in Angstroms. Default is 2.0.
        debug (bool): Enable debug mode. Default is False.
        debug_prefix (str): Prefix for debug files. Default is "debug_".
        checkpoint_file (str, optional): Path to save checkpoint after each step.
        
    Returns:
        MolecularPipeline: A configured pipeline.
    """
    pipeline = MolecularPipeline(debug=debug, debug_prefix=debug_prefix)
    
    # Load data
    pipeline.load(input_car, input_mdf)
    
    if validate_steps:
        logger.info("Validating initial system...")
        validation_results = pipeline.validate()
        if not validation_results["valid"]:
            logger.warning("Initial validation found issues - proceeding anyway")
    
    if checkpoint_file:
        pipeline.save_checkpoint(f"{checkpoint_file}.step1")
    
    # Update force-field types
    pipeline.update_ff_types(ff_mapping_file)
    
    if validate_steps:
        logger.info("Validating system after force-field update...")
        validation_results = pipeline.validate()
        if not validation_results["valid"]:
            logger.warning("Force-field update validation found issues - proceeding anyway")
    
    if checkpoint_file:
        pipeline.save_checkpoint(f"{checkpoint_file}.step2")
    
    # Update charges
    pipeline.update_charges(charge_mapping_file)
    
    if validate_steps:
        logger.info("Validating system after charge update...")
        validation_results = pipeline.validate()
        if not validation_results["valid"]:
            logger.warning("Charge update validation found issues - proceeding anyway")
    
    if checkpoint_file:
        pipeline.save_checkpoint(f"{checkpoint_file}.step3")
    
    # Generate grid
    pipeline.generate_grid(grid_dims=grid_dims, gap=gap)
    
    if validate_steps:
        logger.info("Validating system after grid generation...")
        validation_results = pipeline.validate()
        if not validation_results["valid"]:
            logger.warning("Grid generation validation found issues - proceeding anyway")
    
    if checkpoint_file:
        pipeline.save_checkpoint(f"{checkpoint_file}.step4")
    
    # Final validation before saving
    if validate_steps:
        logger.info("Performing final validation...")
        validation_results = pipeline.validate()
        # Print statistics
        stats = validation_results["statistics"]
        logger.info(f"Final system: {stats['molecules']} molecules, {stats['total_atoms']} atoms")
        logger.info(f"Unique elements: {stats['unique_elements']}, atom types: {stats['unique_atom_types']}")
    
    # Save final output
    pipeline.save(output_car, output_mdf)
    
    return pipeline