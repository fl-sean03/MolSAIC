"""
Legacy module for updating force-field types based on charge and element mapping.
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
        
        # Process keys to handle tuple format if needed
        processed_mapping = {}
        for key, value in mapping.items():
            if key.startswith('(') and key.endswith(')'):
                # Convert string representation of tuple to actual tuple
                # Format: "(charge, element)" -> (charge, element)
                try:
                    parts = key.strip('()').split(',')
                    if len(parts) == 2:
                        charge = float(parts[0].strip())
                        element = parts[1].strip().strip('"\'')
                        processed_mapping[(charge, element)] = value
                    else:
                        processed_mapping[key] = value
                except ValueError:
                    # If conversion fails, keep the original key
                    processed_mapping[key] = value
            else:
                processed_mapping[key] = value
        
        return processed_mapping
    except FileNotFoundError:
        logger.error(f"Mapping file not found: {mapping_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in mapping file: {mapping_file} - {str(e)}")
        raise ValueError(f"Invalid JSON format in mapping file: {str(e)}")

def update_car_ff_types(input_car, output_car, charge_to_fftype):
    """
    Updates the force-field types in a CAR file based on a charge-to-FF mapping.
    
    Args:
        input_car (str): Path to the input CAR file.
        output_car (str): Path to the output CAR file.
        charge_to_fftype (dict): Dictionary mapping (charge, element) to force-field types.
        
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
                    charge = float(parts[-1])
                    element = parts[-2]  # Extract element symbol
                    key = (charge, element)
                    
                    if key in charge_to_fftype:
                        old_fftype = parts[-3]
                        new_fftype = charge_to_fftype[key]
                        
                        # Reconstruct the line with fixed-width formatting
                        updated_line = (
                            f"{parts[0]:<6}"
                            f"{float(parts[1]): 14.9f}"
                            f"{float(parts[2]): 15.9f}"
                            f"{float(parts[3]): 15.9f} "
                            f"{parts[4]:<5}"
                            f"{parts[5]:<7}"
                            f"{new_fftype:<8}"
                            f"{element:<4}"
                            f"{charge:<6}"
                        )
                        
                        logger.debug(f"Updated {parts[0]} ({element}): {old_fftype} -> {new_fftype}")
                        updated_lines.append(updated_line + "\n")
                        update_count += 1
                        continue  # Skip default append to keep format
                except ValueError:
                    pass  # Skip header or invalid lines
            
            updated_lines.append(original_line + "\n")
        
        # Write the updated file
        with open(output_car, 'w') as file:
            file.writelines(updated_lines)
        
        logger.info(f"Updated {update_count} atoms in CAR file: {output_car}")
        return update_count
    
    except FileNotFoundError:
        logger.error(f"CAR file not found: {input_car}")
        raise
    except Exception as e:
        logger.error(f"Error updating CAR file: {str(e)}")
        raise

def update_mdf_ff_types(input_mdf, output_mdf, charge_to_fftype):
    """
    Updates the force-field types in an MDF file based on a charge-to-FF mapping.
    
    Args:
        input_mdf (str): Path to the input MDF file.
        output_mdf (str): Path to the output MDF file.
        charge_to_fftype (dict): Dictionary mapping (charge, element) to force-field types.
        
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
                    charge = float(parts[6])
                    element = parts[1]  # Extract element symbol from MDF format
                    key = (charge, element)
                    
                    if key in charge_to_fftype:
                        old_fftype = parts[2]
                        new_fftype = charge_to_fftype[key]
                        
                        # Reconstruct the MDF line with proper spacing
                        updated_line = (
                            f"{parts[0]:<12} {element:<2} {new_fftype:<7} "
                            f"{parts[3]:<5} {parts[4]:<2} {parts[5]:<5} {charge:<6} "
                            f"{parts[7]:<1} {parts[8]:<1} {parts[9]:<1} "
                            f"{parts[10]:<7} {parts[11]:<6}"
                        )
                        
                        if len(parts) > 12:
                            updated_line += " " + " ".join(parts[12:])
                        
                        logger.debug(f"Updated {parts[0]} ({element}): {old_fftype} -> {new_fftype}")
                        updated_lines.append(updated_line + "\n")
                        update_count += 1
                        continue  # Skip default append to keep format
                except ValueError:
                    pass  # Skip header or invalid lines
            
            updated_lines.append(original_line + "\n")
        
        # Write the updated file
        with open(output_mdf, 'w') as file:
            file.writelines(updated_lines)
        
        logger.info(f"Updated {update_count} atoms in MDF file: {output_mdf}")
        return update_count
    
    except FileNotFoundError:
        logger.error(f"MDF file not found: {input_mdf}")
        raise
    except Exception as e:
        logger.error(f"Error updating MDF file: {str(e)}")
        raise

def update_ff_types(car_file=None, mdf_file=None, output_car=None, output_mdf=None, mapping_file=None):
    """
    Updates force-field types in CAR and/or MDF files based on a mapping.
    
    DEPRECATED: This function is deprecated and will be removed in version 
    {version}. Please use the object-based pipeline instead:
    
    pipeline = MolecularPipeline()
    pipeline.load(car_file, mdf_file)
        .update_ff_types(mapping_file)
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
            car_updates = update_car_ff_types(car_file, output_car, mapping)
            result['car_updates'] = car_updates
        except Exception as e:
            logger.error(f"Failed to update CAR file: {str(e)}")
            raise
    
    # Update MDF file if requested
    if mdf_file is not None:
        try:
            mdf_updates = update_mdf_ff_types(mdf_file, output_mdf, mapping)
            result['mdf_updates'] = mdf_updates
        except Exception as e:
            logger.error(f"Failed to update MDF file: {str(e)}")
            raise
    
    return result