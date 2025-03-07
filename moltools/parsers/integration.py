"""
Integration module for connecting the validation module with parsers.
Provides functions to validate files before parsing and handle validation errors.
"""

import logging
import os
from typing import Tuple, Dict, List, Any, Optional, Union
from moltools.models.molecule import Molecule

from moltools.validation import (
    validate_mdf_file, 
    validate_car_file, 
    validate_pdb_file,
    check_file_type,
    validate_file
)
from moltools.parsers.mdf_parser import parse_mdf, mdf_to_molecules
from moltools.parsers.car_parser import parse_car, car_blocks_to_molecules

logger = logging.getLogger(__name__)

def validate_before_parse(filename: str) -> Tuple[bool, List[str], str]:
    """
    Validate a molecular file before parsing.
    
    Args:
        filename (str): Path to the file to validate.
        
    Returns:
        tuple: (is_valid, errors, file_type), where is_valid is a boolean indicating 
               if the file is valid, errors is a list of error messages if any,
               and file_type is the detected file type.
    """
    return validate_file(filename)

def handle_validation_errors(errors: List[str], file_type: str) -> str:
    """
    Provide detailed error messages and suggestions for common validation issues.
    
    Args:
        errors (list): List of error messages from validation.
        file_type (str): Type of file ('mdf', 'car', 'pdb', or 'unknown').
        
    Returns:
        str: A detailed error message with suggestions for fixing the issues.
    """
    if not errors:
        return "No validation errors."
    
    common_issues = {
        'mdf': {
            'no column definitions': 
                "MDF files require @column definitions. Make sure the file has proper column headers.",
            'no @molecule': 
                "MDF files require @molecule declarations. Check if molecule section is missing.",
            'invalid atom identifier': 
                "Atom identifiers should be in 'residue:atom' format. Check atom names in the file.",
            'invalid charge': 
                "Charge values should be valid numbers. Check for non-numeric values in charge fields."
        },
        'car': {
            'no pbc status': 
                "CAR files require PBC status (PBC=ON/OFF). Make sure it's specified in the header.",
            'no molecule content': 
                "No atom data found in the file. The file may be empty or malformed.",
            'invalid coordinates': 
                "Coordinate values should be valid numbers. Check for non-numeric values in coordinate fields.",
            'line too short': 
                "CAR files use fixed-width format. Check if lines are truncated or improperly formatted."
        },
        'pdb': {
            'no atom records': 
                "No ATOM or HETATM records found. Check if the file contains atom coordinates.",
            'invalid coordinate format': 
                "Coordinate values should be valid numbers. Check for non-numeric values in coordinate fields."
        }
    }
    
    detailed_message = f"Validation failed for {file_type.upper()} file:\n"
    
    for error in errors:
        detailed_message += f"- {error}\n"
        
        # Add suggestions for common issues
        if file_type in common_issues:
            for issue_key, suggestion in common_issues[file_type].items():
                if issue_key.lower() in error.lower():
                    detailed_message += f"  Suggestion: {suggestion}\n"
    
    return detailed_message

def combine_mdf_car_data(mdf_data: Dict[Tuple[str, str], Dict[str, Any]], 
                      molecules: List[List[Dict[str, Any]]]) -> List[Molecule]:
    """
    Combines MDF force-field data with CAR coordinate data to create Molecule objects
    with complete information including connections.
    
    Args:
        mdf_data (dict): Force-field data from MDF parsing.
        molecules (list): List of molecule blocks from CAR parsing.
        
    Returns:
        list: List of Molecule objects with complete data.
    """
    # First convert CAR data to molecules
    car_molecules = car_blocks_to_molecules(molecules)
    
    # For each molecule and atom, add connection information from MDF data
    for molecule in car_molecules:
        for atom in molecule.atoms:
            # Look up this atom in the MDF data
            key = (atom.residue_name, atom.atom_name.upper())
            ff_data = mdf_data.get(key)
            
            if ff_data and 'connections' in ff_data:
                # Add connection information to the atom
                atom.connections = ff_data['connections'].copy() if ff_data['connections'] else []
    
    return car_molecules

def safe_parse_mdf(filename: str) -> Tuple[bool, Union[Tuple[List[str], Dict[Tuple[str, str], Dict[str, Any]]], None], Optional[str]]:
    """
    Safely parse an MDF file with validation.
    
    Args:
        filename (str): Path to the MDF file.
        
    Returns:
        tuple: (success, data, error_message), where success is a boolean indicating if the parsing was successful,
               data is a tuple containing the parsing results or None if validation failed, and
               error_message is a detailed error message if there were validation issues.
    """
    # Validate the file first
    is_valid, errors, file_type = validate_before_parse(filename)
    
    if not is_valid:
        error_message = handle_validation_errors(errors, file_type)
        return False, None, error_message
    
    if file_type != 'mdf':
        return False, None, f"Expected MDF file, but got {file_type.upper()} file."
    
    try:
        # Parse the file
        headers, mdf_data = parse_mdf(filename)
        return True, (headers, mdf_data), None
    except Exception as e:
        return False, None, f"Error parsing MDF file: {str(e)}"

def safe_parse_car(filename: str) -> Tuple[bool, Union[Tuple[List[str], List[Dict[str, Any]], Optional[Any]], None], Optional[str]]:
    """
    Safely parse a CAR file with validation.
    
    Args:
        filename (str): Path to the CAR file.
        
    Returns:
        tuple: (success, data, error_message), where success is a boolean indicating if the parsing was successful,
               data is a tuple containing the parsing results or None if validation failed, and
               error_message is a detailed error message if there were validation issues.
    """
    # Validate the file first
    is_valid, errors, file_type = validate_before_parse(filename)
    
    if not is_valid:
        error_message = handle_validation_errors(errors, file_type)
        return False, None, error_message
    
    if file_type != 'car':
        return False, None, f"Expected CAR file, but got {file_type.upper()} file."
    
    try:
        # Parse the file
        header_lines, molecules, pbc_coords = parse_car(filename)
        return True, (header_lines, molecules, pbc_coords), None
    except Exception as e:
        return False, None, f"Error parsing CAR file: {str(e)}"

def process_mdf_car_pair(mdf_file: str, car_file: str) -> Tuple[bool, Optional[Any], Optional[str]]:
    """
    Process a pair of MDF and CAR files together, combining their data.
    
    Args:
        mdf_file (str): Path to the MDF file.
        car_file (str): Path to the CAR file.
        
    Returns:
        tuple: (success, data, error_message), where success is a boolean indicating 
               if the processing was successful, data is a tuple containing the System object 
               or None if it failed, and error_message is a detailed error message if there were issues.
    """
    # Parse MDF file
    mdf_success, mdf_result, mdf_error = safe_parse_mdf(mdf_file)
    if not mdf_success:
        return False, None, f"Error processing MDF file: {mdf_error}"
    
    # Parse CAR file
    car_success, car_result, car_error = safe_parse_car(car_file)
    if not car_success:
        return False, None, f"Error processing CAR file: {car_error}"
    
    # Extract data
    headers, mdf_data = mdf_result
    car_headers, molecule_blocks, pbc_coords = car_result
    
    try:
        # Combine MDF and CAR data
        molecules = combine_mdf_car_data(mdf_data, molecule_blocks)
        
        # Create a System object (will need to import System class)
        # This is a placeholder - actual System creation would depend on your implementation
        # system = System(mdf_data)
        # system.molecules = molecules
        # system.pbc = pbc_coords
        
        return True, (molecules, mdf_data, pbc_coords), None
    except Exception as e:
        return False, None, f"Error combining MDF and CAR data: {str(e)}"

def detect_and_process_file(filename: str) -> Tuple[bool, Optional[Any], Optional[str], str]:
    """
    Detect the file type and process it with the appropriate parser.
    
    Args:
        filename (str): Path to the file to process.
        
    Returns:
        tuple: (success, data, error_message, file_type), where success is a boolean indicating 
               if the processing was successful, data is the result of parsing or None if it failed,
               error_message is a detailed error message if there were issues, and file_type is the
               detected file type.
    """
    # Check if file exists
    if not os.path.exists(filename):
        return False, None, f"File does not exist: {filename}", "unknown"
    
    # Detect file type
    file_type = check_file_type(filename)
    
    if file_type == "unknown":
        return False, None, "Unknown file type. Cannot process.", file_type
    
    # Process according to file type
    if file_type == "mdf":
        success, data, error = safe_parse_mdf(filename)
        return success, data, error, file_type
    elif file_type == "car":
        success, data, error = safe_parse_car(filename)
        return success, data, error, file_type
    elif file_type == "pdb":
        # Implement PDB processing if available
        return False, None, "PDB processing not implemented in this example.", file_type
    else:
        return False, None, f"Processing for {file_type} files not implemented.", file_type


# Example usage in a script:
"""
from moltools.parsers.integration import safe_parse_mdf, safe_parse_car, detect_and_process_file

# Example 1: Process MDF file with validation
success, data, error = safe_parse_mdf("example.mdf")
if success:
    headers, mdf_data = data
    print(f"Successfully parsed MDF file with {len(mdf_data)} atoms")
else:
    print(error)

# Example 2: Process CAR file with validation
success, data, error = safe_parse_car("example.car")
if success:
    header_lines, molecules, pbc_coords = data
    print(f"Successfully parsed CAR file with {len(molecules)} molecules")
else:
    print(error)

# Example 3: Detect and process any supported file type
success, data, error, file_type = detect_and_process_file("unknown_file")
if success:
    print(f"Successfully processed {file_type.upper()} file")
    if file_type == "mdf":
        headers, mdf_data = data
        print(f"Found {len(mdf_data)} atoms")
    elif file_type == "car":
        header_lines, molecules, pbc_coords = data
        print(f"Found {len(molecules)} molecules")
else:
    print(f"Error processing file: {error}")
"""