"""
Validation module for molecular file formats.
Provides functions to check file format integrity.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

def validate_car_file(filename):
    """
    Validate a CAR file format.
    
    Args:
        filename (str): Path to the CAR file to validate.
        
    Returns:
        tuple: (is_valid, errors), where is_valid is a boolean indicating if the file is valid
               and errors is a list of error messages if any.
    """
    errors = []
    is_valid = True
    
    # Check if file exists and is accessible
    if not os.path.exists(filename):
        errors.append(f"File {filename} does not exist")
        return False, errors
    
    if not os.path.isfile(filename):
        errors.append(f"Path {filename} is not a file")
        return False, errors
    
    # Check content
    try:
        with open(filename, 'r') as f:
            first_line = f.readline().strip()
            if not first_line.startswith("!BIOSYM archive"):
                errors.append(f"File does not appear to be a valid CAR file: first line should start with '!BIOSYM archive'")
                is_valid = False
            
            # Check for PBC status
            f.seek(0)
            pbc_status_found = False
            pbc_coords_found = False
            molecule_found = False
            end_found = False
            atom_lines = []
            
            for i, line in enumerate(f):
                line_strip = line.strip()
                if line_strip == "PBC=ON" or line_strip == "PBC=OFF":
                    pbc_status_found = True
                elif line_strip.startswith("PBC "):
                    pbc_coords_found = True
                elif i > 5:  # After header, look for molecule content
                    # Check if there are atom entries (non-header, non-empty lines)
                    if line_strip and not line_strip.startswith(("!", "#", "@", "PBC")):
                        if line_strip.lower() != "end":  # Not the end marker
                            molecule_found = True
                            atom_lines.append(line_strip)
                    # Check for end marker
                    if line_strip.lower() == "end":
                        end_found = True
            
            if not pbc_status_found:
                errors.append("No PBC status (PBC=ON/OFF) found")
                is_valid = False
            
            if not molecule_found:
                errors.append("No molecule content found")
                is_valid = False
            
            if not end_found:
                errors.append("No 'end' marker found to terminate molecule block")
                is_valid = False
                
            # Validate atom lines format (more detailed checks)
            if atom_lines:
                for i, line in enumerate(atom_lines):
                    # Check line length
                    if len(line) < 74:
                        errors.append(f"Line {i+1} is too short (should be at least 74 chars): '{line}'")
                        is_valid = False
                        continue
                        
                    # Check coordinate format
                    try:
                        x = float(line[6:20].strip())
                        y = float(line[20:35].strip())
                        z = float(line[35:50].strip())
                    except ValueError:
                        errors.append(f"Line {i+1} has invalid coordinates: '{line}'")
                        is_valid = False
                    
                    # Check residue number format
                    try:
                        residue_number = int(line[55:62].strip())
                    except ValueError:
                        errors.append(f"Line {i+1} has invalid residue number: '{line}'")
                        is_valid = False
                    
                    # Check atom name exists
                    atom_name = line[0:6].strip()
                    if not atom_name:
                        errors.append(f"Line {i+1} is missing atom name: '{line}'")
                        is_valid = False
    
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")
        is_valid = False
    
    return is_valid, errors

def validate_mdf_file(filename):
    """
    Validate an MDF file format.
    
    Args:
        filename (str): Path to the MDF file to validate.
        
    Returns:
        tuple: (is_valid, errors), where is_valid is a boolean indicating if the file is valid
               and errors is a list of error messages if any.
    """
    errors = []
    is_valid = True
    
    # Check if file exists and is accessible
    if not os.path.exists(filename):
        errors.append(f"File {filename} does not exist")
        return False, errors
    
    if not os.path.isfile(filename):
        errors.append(f"Path {filename} is not a file")
        return False, errors
    
    # Check content
    try:
        with open(filename, 'r') as f:
            first_line = f.readline().strip()
            if not first_line.startswith("!BIOSYM molecular_data"):
                errors.append(f"File does not appear to be a valid MDF file: first line should start with '!BIOSYM molecular_data'")
                is_valid = False
            
            # Check for column definitions and molecule blocks
            f.seek(0)
            columns_found = False
            molecule_found = False
            atom_data_found = False
            end_found = False
            atom_lines = []
            current_residue = None
            
            for i, line in enumerate(f):
                line_strip = line.strip()
                if line_strip.startswith("@column"):
                    columns_found = True
                elif line_strip.startswith("@molecule"):
                    molecule_found = True
                    # Extract molecule name
                    parts = line_strip.split()
                    if len(parts) > 1:
                        current_residue = parts[1]
                    else:
                        errors.append(f"Line {i+1}: @molecule declaration without name: '{line_strip}'")
                        is_valid = False
                elif ":" in line_strip and len(line_strip.split()) >= 12:
                    atom_data_found = True
                    atom_lines.append((i+1, line_strip))  # Store line number with content
                elif line_strip == "#end":
                    end_found = True
            
            if not columns_found:
                errors.append("No column definitions found")
                is_valid = False
            
            if not molecule_found:
                errors.append("No @molecule declaration found")
                is_valid = False
            
            if not atom_data_found:
                errors.append("No atom data found")
                is_valid = False
            
            if not end_found:
                errors.append("No '#end' marker found")
                is_valid = False
                
            # Validate atom data format more thoroughly
            if atom_lines:
                for line_num, line in atom_lines:
                    parts = line.split()
                    
                    # Check atom identifier format (should be residue_name:atom_name)
                    if ':' not in parts[0]:
                        errors.append(f"Line {line_num}: Invalid atom identifier format (should be residue:atom): '{parts[0]}'")
                        is_valid = False
                    
                    # Check for numeric fields
                    try:
                        # Check charge format (field 6)
                        if len(parts) > 6:
                            charge = float(parts[6])
                            if charge < -10 or charge > 10:
                                errors.append(f"Line {line_num}: Charge value seems unrealistic: {charge}")
                                # Don't fail validation for this warning
                    except ValueError:
                        errors.append(f"Line {line_num}: Invalid charge value: '{parts[6] if len(parts) > 6 else 'missing'}'")
                        is_valid = False
                        
                    # Check element field format (should be element symbol)
                    if len(parts) > 1:
                        element = parts[1]
                        if not re.match(r'^[A-Za-z]{1,2}$', element):
                            errors.append(f"Line {line_num}: Invalid element symbol: '{element}'")
                            is_valid = False
    
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")
        is_valid = False
    
    return is_valid, errors

def validate_pdb_file(filename):
    """
    Validate a PDB file format.
    
    Args:
        filename (str): Path to the PDB file to validate.
        
    Returns:
        tuple: (is_valid, errors), where is_valid is a boolean indicating if the file is valid
               and errors is a list of error messages if any.
    """
    errors = []
    is_valid = True
    
    # Check if file exists and is accessible
    if not os.path.exists(filename):
        errors.append(f"File {filename} does not exist")
        return False, errors
    
    if not os.path.isfile(filename):
        errors.append(f"Path {filename} is not a file")
        return False, errors
    
    # Check content
    try:
        with open(filename, 'r') as f:
            atom_records_found = False
            coordinate_errors = False
            
            for i, line in enumerate(f):
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    atom_records_found = True
                    
                    # Check if line has the correct length
                    if len(line) < 54:  # Minimum length to contain coordinates
                        errors.append(f"Line {i+1}: ATOM/HETATM record too short: '{line.strip()}'")
                        is_valid = False
                        continue
                    
                    # Check if coordinates are valid floats
                    try:
                        x = float(line[30:38].strip())
                        y = float(line[38:46].strip())
                        z = float(line[46:54].strip())
                    except ValueError:
                        if not coordinate_errors:  # Only report the first error to avoid overwhelming
                            errors.append(f"Line {i+1}: Invalid coordinate format: '{line.strip()}'")
                            coordinate_errors = True
                        is_valid = False
                
            if not atom_records_found:
                errors.append("No ATOM or HETATM records found")
                is_valid = False
                
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")
        is_valid = False
    
    return is_valid, errors

def check_file_type(filename):
    """
    Check what type of molecular file the given file is (MDF, CAR, PDB).
    
    Args:
        filename (str): Path to the file to check.
        
    Returns:
        str: File type ('mdf', 'car', 'pdb', or 'unknown').
    """
    if not os.path.exists(filename) or not os.path.isfile(filename):
        return 'unknown'
    
    # Check file extension
    ext = os.path.splitext(filename)[1].lower()
    if ext in ('.mdf', '.car', '.pdb'):
        return ext[1:]  # Return without the dot
    
    # Check file content if extension doesn't match
    try:
        with open(filename, 'r') as f:
            first_line = f.readline().strip()
            if first_line.startswith("!BIOSYM molecular_data"):
                return 'mdf'
            elif first_line.startswith("!BIOSYM archive"):
                return 'car'
            elif first_line.startswith("REMARK") or first_line.startswith("HEADER") or first_line.startswith("ATOM"):
                return 'pdb'
    except:
        pass
    
    return 'unknown'

def validate_file(filename):
    """
    Validate any molecular file by detecting its type and applying the appropriate validation.
    
    Args:
        filename (str): Path to the file to validate.
        
    Returns:
        tuple: (is_valid, errors, file_type), where is_valid is a boolean indicating if the file is valid,
               errors is a list of error messages if any, and file_type is the detected file type.
    """
    file_type = check_file_type(filename)
    
    if file_type == 'unknown':
        return False, ["Unknown file type, cannot validate"], file_type
    
    if file_type == 'mdf':
        is_valid, errors = validate_mdf_file(filename)
    elif file_type == 'car':
        is_valid, errors = validate_car_file(filename)
    elif file_type == 'pdb':
        is_valid, errors = validate_pdb_file(filename)
    else:
        return False, [f"Validation not supported for file type: {file_type}"], file_type
    
    return is_valid, errors, file_type