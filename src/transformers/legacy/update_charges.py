"""
Legacy module for updating atomic charges based on force-field type mapping.
This module contains the original file-based transformation functions,
maintained for backward compatibility.

DEPRECATED: This file-based approach is deprecated and will be removed in 
version {version}. Please use the object-based pipeline instead.
"""

import logging
import json
from ... import config

logger = logging.getLogger(__name__)

# Fix the docstring
__doc__ = __doc__.format(version=config.FILE_MODE_REMOVAL_VERSION)

def load_mapping(mapping_file):
    """
    Loads a mapping from a JSON file.
    
    Args:
        mapping_file (str): Path to the JSON mapping file.
        
    Returns:
        dict: The mapping dictionary.
        
    Raises:
        FileNotFoundError: If the mapping file does not exist.
        ValueError: If the file is not a valid JSON.
    """
    try:
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        return mapping
    except FileNotFoundError:
        logger.error(f"Mapping file not found: {mapping_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in mapping file: {mapping_file} - {str(e)}")
        raise ValueError(f"Invalid JSON format in mapping file: {str(e)}")

def update_car_charges(input_car, output_car, ff_to_charge):
    """
    Updates charges in a CAR file based on force-field type mapping.
    
    Args:
        input_car (str): Path to the input CAR file.
        output_car (str): Path to the output CAR file.
        ff_to_charge (dict): Dictionary mapping force-field types to charges.
        
    Returns:
        int: Number of atoms updated.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        IOError: If there's an error writing to the output file.
    """
    try:
        with open(input_car, 'r') as file:
            lines = file.readlines()
        
        updated_lines = []
        update_count = 0
        
        for line in lines:
            original_line = line.rstrip("\n")  # Keep original formatting
            parts = original_line.split()
            
            if len(parts) >= 7:
                try:
                    ff_type = parts[-3]  # Extract force-field type
                    
                    if ff_type in ff_to_charge:
                        old_charge = parts[-1]
                        new_charge = ff_to_charge[ff_type]
                        
                        # Reconstruct line with updated charge
                        updated_line = (
                            f"{parts[0]:<6}"
                            f"{float(parts[1]): 14.9f}"
                            f"{float(parts[2]): 15.9f}"
                            f"{float(parts[3]): 15.9f} "
                            f"{parts[4]:<5}"
                            f"{parts[5]:<7}"
                            f"{ff_type:<8}"
                            f"{parts[-2]:<4}"
                            f"{float(new_charge):<6.3f}"
                        )
                        
                        logger.debug(f"Updated {parts[0]} ({ff_type}): Charge {old_charge} -> {new_charge}")
                        updated_lines.append(updated_line + "\n")
                        update_count += 1
                        continue  # Skip default append to keep format
                except (ValueError, IndexError):
                    pass  # Skip header or invalid lines
            
            updated_lines.append(original_line + "\n")
        
        # Write the updated file
        with open(output_car, 'w') as file:
            file.writelines(updated_lines)
        
        logger.info(f"Updated {update_count} atom charges in CAR file: {output_car}")
        return update_count
    
    except FileNotFoundError:
        logger.error(f"CAR file not found: {input_car}")
        raise
    except Exception as e:
        logger.error(f"Error updating CAR file charges: {str(e)}")
        raise

def update_mdf_charges(input_mdf, output_mdf, ff_to_charge):
    """
    Updates charges in an MDF file based on force-field type mapping.
    
    Args:
        input_mdf (str): Path to the input MDF file.
        output_mdf (str): Path to the output MDF file.
        ff_to_charge (dict): Dictionary mapping force-field types to charges.
        
    Returns:
        int: Number of atoms updated.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        IOError: If there's an error writing to the output file.
    """
    try:
        with open(input_mdf, 'r') as file:
            lines = file.readlines()
        
        updated_lines = []
        update_count = 0
        parsing_atoms = False
        
        for line in lines:
            original_line = line.rstrip("\n")  # Keep original formatting
            parts = original_line.split()
            
            if "@molecule" in line:
                parsing_atoms = True
            
            if parsing_atoms and len(parts) >= 12 and ":" in parts[0]:
                try:
                    ff_type = parts[2]  # Extract force-field type
                    
                    if ff_type in ff_to_charge:
                        old_charge = parts[6]
                        new_charge = ff_to_charge[ff_type]
                        
                        # Reconstruct MDF line with updated charge
                        updated_line = (
                            f"{parts[0]:<12} {parts[1]:<2} {ff_type:<7} "
                            f"{parts[3]:<5} {parts[4]:<2} {parts[5]:<5} {float(new_charge):<6.3f} "
                            f"{parts[7]:<1} {parts[8]:<1} {parts[9]:<1} "
                            f"{parts[10]:<7} {parts[11]:<6}"
                        )
                        
                        if len(parts) > 12:
                            updated_line += " " + " ".join(parts[12:])
                        
                        logger.debug(f"Updated {parts[0]} ({ff_type}): Charge {old_charge} -> {new_charge}")
                        updated_lines.append(updated_line + "\n")
                        update_count += 1
                        continue  # Skip default append to keep format
                except (ValueError, IndexError):
                    pass  # Skip header or invalid lines
            
            updated_lines.append(original_line + "\n")
        
        # Write the updated file
        with open(output_mdf, 'w') as file:
            file.writelines(updated_lines)
        
        logger.info(f"Updated {update_count} atom charges in MDF file: {output_mdf}")
        return update_count
    
    except FileNotFoundError:
        logger.error(f"MDF file not found: {input_mdf}")
        raise
    except Exception as e:
        logger.error(f"Error updating MDF file charges: {str(e)}")
        raise

def update_charges(car_file=None, mdf_file=None, output_car=None, output_mdf=None, mapping_file=None):
    """
    Updates atomic charges in CAR and/or MDF files based on a force-field type mapping.
    
    DEPRECATED: This function is deprecated and will be removed in version 
    {version}. Please use the object-based pipeline instead:
    
    pipeline = MolecularPipeline()
    pipeline.load(car_file, mdf_file)
        .update_charges(mapping_file)
        .save(output_car, output_mdf)
    
    Args:
        car_file (str, optional): Path to the input CAR file.
        mdf_file (str, optional): Path to the input MDF file.
        output_car (str, optional): Path to the output CAR file.
        output_mdf (str, optional): Path to the output MDF file.
        mapping_file (str, required): Path to the JSON mapping file.
        
    Returns:
        dict: Dictionary with update counts.
        
    Raises:
        ValueError: If inputs are invalid.
        FileNotFoundError: If input files don't exist.
    """.format(version=config.FILE_MODE_REMOVAL_VERSION)
    # Show deprecation warning
    config.show_file_mode_deprecation_warning(logger)
    
    # Validate inputs
    if mapping_file is None:
        raise ValueError("mapping_file is required")
    
    if car_file is None and mdf_file is None:
        raise ValueError("At least one of car_file or mdf_file must be provided")
    
    if car_file is not None and output_car is None:
        raise ValueError("output_car is required when car_file is provided")
    
    if mdf_file is not None and output_mdf is None:
        raise ValueError("output_mdf is required when mdf_file is provided")
    
    # Load the mapping
    try:
        mapping = load_mapping(mapping_file)
    except Exception as e:
        logger.error(f"Failed to load mapping file: {str(e)}")
        raise
    
    result = {}
    
    # Update CAR file if requested
    if car_file is not None:
        try:
            car_updates = update_car_charges(car_file, output_car, mapping)
            result['car_updates'] = car_updates
        except Exception as e:
            logger.error(f"Failed to update CAR file: {str(e)}")
            raise
    
    # Update MDF file if requested
    if mdf_file is not None:
        try:
            mdf_updates = update_mdf_charges(mdf_file, output_mdf, mapping)
            result['mdf_updates'] = mdf_updates
        except Exception as e:
            logger.error(f"Failed to update MDF file: {str(e)}")
            raise
    
    return result