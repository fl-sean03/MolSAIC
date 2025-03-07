"""
Module for updating force-field types based on charge and element mapping.
Supports both object-based and file-based approaches.
"""

import logging
from typing import Dict, Union, Optional, Tuple

from ..models.system import System
from .legacy.update_ff import update_car_ff_types as legacy_update_car
from .legacy.update_ff import update_mdf_ff_types as legacy_update_mdf
from .legacy.update_ff import load_mapping

logger = logging.getLogger(__name__)

def update_ff_types_obj(system: System, mapping: Union[Dict, str]) -> int:
    """
    Update force-field types in a System object based on a mapping.
    
    Args:
        system (System): The molecular system to update.
        mapping (dict or str): Mapping dictionary or path to mapping file.
        
    Returns:
        int: Number of atoms updated.
        
    Raises:
        ValueError: If the system is invalid or mapping cannot be loaded.
    """
    if system is None:
        raise ValueError("System object cannot be None")
    
    return system.update_ff_types(mapping)

def update_ff_types(car_file: Optional[str] = None, 
                   mdf_file: Optional[str] = None, 
                   output_car: Optional[str] = None, 
                   output_mdf: Optional[str] = None, 
                   mapping_file: Optional[str] = None, 
                   mapping_dict: Optional[Dict] = None,
                   object_mode: bool = False,
                   system: Optional[System] = None) -> Dict:
    """
    Updates force-field types in CAR and/or MDF files or in a System object.
    
    This function supports both the legacy file-based approach and the new
    object-based approach. When using object_mode=True, the system parameter
    must be provided or both car_file and mdf_file must be provided to create
    a new System object.
    
    Args:
        car_file (str, optional): Path to the input CAR file.
        mdf_file (str, optional): Path to the input MDF file.
        output_car (str, optional): Path to the output CAR file.
        output_mdf (str, optional): Path to the output MDF file.
        mapping_file (str, optional): Path to the JSON mapping file.
        mapping_dict (dict, optional): Dictionary of mappings, as an alternative to mapping_file.
        object_mode (bool, optional): Use object-based approach. Default is False.
        system (System, optional): System object for object-based approach.
        
    Returns:
        dict: Dictionary with update counts and/or updated system.
        
    Raises:
        ValueError: If neither mapping_file nor mapping_dict is provided,
                  or if required files are not provided.
    """
    if not mapping_file and not mapping_dict:
        raise ValueError("Either mapping_file or mapping_dict must be provided")
    
    # Determine the mapping to use
    if mapping_file:
        mapping = load_mapping(mapping_file)
    else:
        mapping = mapping_dict
    
    results = {}
    
    # Object-based approach
    if object_mode:
        # Use provided system or create one from files
        if system is None:
            if not car_file or not mdf_file:
                raise ValueError("For object mode without a system, both car_file and mdf_file must be provided")
            
            logger.info(f"Creating system from files: {car_file}, {mdf_file}")
            system = System.system_from_files(car_file, mdf_file)
        
        # Update the system
        update_count = update_ff_types_obj(system, mapping)
        results['update_count'] = update_count
        results['system'] = system
        
        # Write output files if specified
        if output_car or output_mdf:
            base_name = "MOL"  # Default base name
            if output_car and output_mdf:
                logger.info(f"Writing updated system to files: {output_car}, {output_mdf}")
                system.to_files(output_car, output_mdf, base_name)
            elif output_car:
                logger.warning("Only CAR output specified, MDF will not be written")
                system.to_files(output_car, None, base_name)
            elif output_mdf:
                logger.warning("Only MDF output specified, CAR will not be written")
                system.to_files(None, output_mdf, base_name)
    
    # Legacy file-based approach
    else:
        if not car_file and not mdf_file:
            raise ValueError("Either car_file or mdf_file must be provided")
        
        # Update CAR file if provided
        if car_file and output_car:
            logger.info(f"Updating force-field types in CAR file: {car_file}")
            car_updates = legacy_update_car(car_file, output_car, mapping)
            results['car_updates'] = car_updates
            logger.info(f"Updated {car_updates} force-field types in CAR file: {output_car}")
        
        # Update MDF file if provided
        if mdf_file and output_mdf:
            logger.info(f"Updating force-field types in MDF file: {mdf_file}")
            mdf_updates = legacy_update_mdf(mdf_file, output_mdf, mapping)
            results['mdf_updates'] = mdf_updates
            logger.info(f"Updated {mdf_updates} force-field types in MDF file: {output_mdf}")
    
    return results