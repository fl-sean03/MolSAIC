"""
Module for parsing MDF (Materials Studio Molecular Data Format) files.
"""

import logging
import os
from typing import Tuple, Dict, List, Any, Optional, Set

from moltools.models.atom import Atom
from moltools.models.molecule import Molecule

logger = logging.getLogger(__name__)

def mdf_to_molecules(mdf_data: Dict[Tuple[str, str], Dict[str, Any]]) -> Dict[str, Molecule]:
    """
    Converts MDF data dictionary to Molecule objects.
    
    Args:
        mdf_data (dict): Dictionary of MDF force-field data keyed by (residue, atom_name).
        
    Returns:
        dict: Dictionary of Molecule objects keyed by residue name.
    """
    # Group atoms by residue
    residues = {}
    for (residue_name, atom_name), data in mdf_data.items():
        if residue_name not in residues:
            residues[residue_name] = {}
        
        # Store atom data with connections
        atom_data = {
            'name': atom_name,
            'element': data['element'],
            'atom_type': data['atom_type'],
            'charge': data['charge'],
            'connections': data.get('connections', [])
        }
        residues[residue_name][atom_name] = atom_data
    
    # Create Molecule objects
    molecules = {}
    for residue_name, atoms_dict in residues.items():
        # For now, we can't create full molecules without coordinates
        # This function serves as a placeholder for future implementation
        # where coordinates might be added from CAR files
        molecules[residue_name] = None
    
    return molecules

def parse_mdf(filename: str, validate: bool = True) -> Tuple[List[str], Dict[Tuple[str, str], Dict[str, Any]]]:
    """
    Parses an MDF file and returns header information and a force-field data dictionary.
    
    The MDF format includes columns for: element, atom_type, charge_group, isotope,
    formal_charge, charge, switching_atom, oop_flag, chirality_flag, occupancy,
    xray_temp_factor, and connections.
    
    Args:
        filename (str): Path to the MDF file.
        validate (bool, optional): Whether to validate the file before parsing. Defaults to True.
        
    Returns:
        tuple: A tuple containing:
            - headers (list): List of header lines.
            - mdf_data (dict): Dictionary keyed by (residue, atom_name) containing force-field data.
            
    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file format is invalid.
    """
    mdf_data = {}
    headers = []
    current_residue = None
    header_seen = False  # To include header lines only once
    
    # Validate input
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    if not isinstance(filename, (str, bytes)):
        raise TypeError(f"Expected string or bytes for filename, got {type(filename).__name__}")
    
    # Verify the file exists
    if not os.path.exists(filename):
        raise FileNotFoundError(f"MDF file not found: {filename}")
    
    # Verify it's a file not a directory
    if not os.path.isfile(filename):
        raise ValueError(f"Path is not a file: {filename}")
    
    # Perform validation if requested
    if validate:
        try:
            from moltools.validation import validate_mdf_file
            is_valid, errors = validate_mdf_file(filename)
            if not is_valid:
                error_msg = "\n".join(errors)
                raise ValueError(f"MDF file validation failed:\n{error_msg}")
        except ImportError:
            logger.warning("Validation module not available. Skipping validation.")
    
    # Read and parse the file
    try:
        with open(filename, 'r') as file:
            first_line = file.readline().strip()
            # Verify it looks like an MDF file
            if not first_line.startswith("!BIOSYM molecular_data"):
                logger.warning(f"File does not appear to be a valid MDF file: {filename}")
            
            # Go back to beginning of file
            file.seek(0)
            
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                
                # Gather header lines
                if line.startswith(('!', '#', '@column')):
                    if not header_seen:
                        headers.append(line)
                    continue
                
                if line.startswith('#end'):
                    header_seen = True
                    continue
                
                # Check for molecule definition lines
                if line.startswith('@molecule'):
                    parts = line.split()
                    if len(parts) > 1:
                        current_residue = parts[1]
                        logger.debug(f"Found molecule: {current_residue}")
                    else:
                        logger.warning(f"Line {line_num}: Malformed @molecule line with no name: {line}")
                    continue
                
                if not line:
                    continue
                
                # Parse atom data lines
                parts = line.split()
                if len(parts) < 12:
                    logger.debug(f"Line {line_num}: Skipping line with insufficient parts: {line}")
                    continue
                    
                if ':' not in parts[0]:
                    logger.debug(f"Line {line_num}: Skipping line without atom identifier: {line}")
                    continue
                
                # Extract atom name from the "XXXX_1:ATOMNAME" format
                try:
                    residue_atom = parts[0]
                    _, atom = residue_atom.split(':')
                    atom = atom.upper()  # Standardize to uppercase
                    
                    if current_residue is None:
                        logger.warning(f"Line {line_num}: Found atom data before any @molecule definition: {line}")
                        continue
                    
                    key = (current_residue, atom)
                    
                    # Validate numeric fields
                    try:
                        charge = float(parts[6])
                    except ValueError:
                        logger.warning(f"Line {line_num}: Invalid charge value '{parts[6]}'. Using 0.0 instead.")
                        parts[6] = "0.0"
                    
                    # Store force-field data for this atom
                    # Preserve connection information precisely
                    connections = []
                    if len(parts) > 12:
                        # Extract the raw connection strings, which may include bond orders
                        connections = parts[12:]
                        
                    mdf_data[key] = {
                        'element': parts[1],
                        'atom_type': parts[2],
                        'charge_group': parts[3],
                        'isotope': parts[4],
                        'formal_charge': parts[5],
                        'charge': parts[6],
                        'switching_atom': parts[7],
                        'oop_flag': parts[8],
                        'chirality_flag': parts[9],
                        'occupancy': parts[10],
                        'xray_temp_factor': parts[11],
                        'connections': connections,
                        'line_number': line_num  # Store the line number for reference
                    }
                except (IndexError, ValueError) as e:
                    logger.warning(f"Line {line_num}: Error parsing line: {line} - {str(e)}")
                    continue
                    
        # Validation of parsed data
        if not mdf_data:
            logger.warning(f"No valid atom data found in MDF file: {filename}")
            
        if not headers:
            logger.warning(f"No header lines found in MDF file: {filename}")
        
        molecule_count = len(set([key[0] for key in mdf_data.keys()]))
        logger.info(f"Parsed {len(mdf_data)} atoms across {molecule_count} molecules from {filename}")
            
        return headers, mdf_data
        
    except FileNotFoundError:
        logger.error(f"MDF file not found: {filename}")
        raise
    except Exception as e:
        logger.error(f"Error parsing MDF file: {filename} - {str(e)}")
        raise ValueError(f"Invalid MDF file format: {str(e)}")