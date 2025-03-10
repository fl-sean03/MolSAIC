"""
Module for parsing CAR (Materials Studio Coordinate Archive) files.
"""

import logging
import os
from typing import Tuple, Dict, List, Any, Optional, Union
from molsaic.models.atom import Atom
from molsaic.models.molecule import Molecule

logger = logging.getLogger(__name__)

def parse_car(filename: str, validate: bool = True) -> Tuple[List[str], List[List[Dict[str, Any]]], Optional[Tuple]]:
    """
    Parses a CAR file and returns header information, molecule blocks, and PBC.
    
    CAR files use fixed-width formatting with the following fields:
    - Atom name (cols 0-6)
    - x, y, z coordinates (cols 6-20, 20-35, 35-50)
    - residue name (cols 50-55)
    - residue number (cols 55-62)
    - atom type (cols 62-70)
    - element (cols 70-74)
    - charge (cols 74-80)
    
    Args:
        filename (str): Path to the CAR file.
        validate (bool, optional): Whether to validate the file before parsing. Defaults to True.
        
    Returns:
        tuple: A tuple containing:
            - header_lines (list): List of header lines.
            - molecules (list): List of molecule blocks (each a list of atom dictionaries).
            - pbc_coords (tuple or None): Tuple of PBC coordinates if found, or None.
            
    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file format is invalid.
    """
    molecules = []
    header_lines = []
    pbc_coords = None
    
    # Validate input
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    if not isinstance(filename, (str, bytes)):
        raise TypeError(f"Expected string or bytes for filename, got {type(filename).__name__}")
    
    # Verify the file exists
    if not os.path.exists(filename):
        raise FileNotFoundError(f"CAR file not found: {filename}")
    
    # Verify it's a file not a directory
    if not os.path.isfile(filename):
        raise ValueError(f"Path is not a file: {filename}")
    
    # Perform validation if requested
    if validate:
        try:
            from molsaic.validation import validate_car_file
            is_valid, errors = validate_car_file(filename)
            if not is_valid:
                error_msg = "\n".join(errors)
                raise ValueError(f"CAR file validation failed:\n{error_msg}")
        except ImportError:
            logger.warning("Validation module not available. Skipping validation.")
    
    # Read and parse the file
    try:
        with open(filename, 'r') as f:
            first_line = f.readline().strip()
            # Verify it looks like a CAR file
            if not first_line.startswith("!BIOSYM archive"):
                logger.warning(f"File does not appear to be a valid CAR file: {filename}")
            
            # Go back to beginning of file
            f.seek(0)
            lines = f.readlines()
        
        # Identify header lines and look for PBC information
        header_end_index = 0
        found_pbc_status = False
        
        for i, line in enumerate(lines):
            line_strip = line.strip()
            if not line_strip:
                continue
                
            if line_strip.startswith(("!BIOSYM", "PBC", "Materials", "!DATE")):
                header_lines.append(line_strip)
                
                # Check if PBC status is defined
                if line_strip == "PBC=ON" or line_strip == "PBC=OFF":
                    found_pbc_status = True
                
                # Extract PBC coordinates if present
                if line_strip.startswith("PBC") and line_strip not in ["PBC=ON", "PBC=OFF"]:
                    parts = line_strip.split()
                    try:
                        if len(parts) >= 8:
                            dims = [float(x) for x in parts[1:4]]
                            angles = [float(x) for x in parts[4:7]]
                            cell_type = parts[7].strip("()")
                            pbc_coords = tuple(dims + angles + [cell_type])
                            logger.debug(f"Parsed PBC coordinates: {pbc_coords}")
                    except Exception as e:
                        logger.warning(f"Failed to parse PBC line: {line_strip} - {str(e)}")
            else:
                header_end_index = i
                break
        
        if not found_pbc_status:
            logger.warning(f"No PBC status (PBC=ON/OFF) found in CAR file: {filename}")
        
        if not header_lines:
            logger.warning(f"No header lines found in CAR file: {filename}")
        
        # Parse molecule blocks, each ending with "end"
        current_molecule = []
        molecule_count = 0
        atom_count = 0
        
        for line_num, line in enumerate(lines[header_end_index:], header_end_index + 1):
            line = line.rstrip()
            if not line:
                continue
                
            if line.strip().lower() == "end":
                if current_molecule:
                    molecules.append(current_molecule)
                    molecule_count += 1
                    current_molecule = []
            else:
                # Parse fixed-width fields
                try:
                    # Check if the line is of sufficient length for all fields
                    if len(line) < 74:
                        logger.debug(f"Line {line_num}: Line too short to contain all fields: {line}")
                        continue
                    
                    atom_name = line[0:6].strip()
                    
                    # Better error handling for coordinate parsing
                    try:
                        x = float(line[6:20].strip())
                        y = float(line[20:35].strip())
                        z = float(line[35:50].strip())
                    except ValueError:
                        logger.warning(f"Line {line_num}: Invalid coordinate format: {line}")
                        continue
                    
                    residue_name = line[50:55].strip()
                    
                    # Better error handling for residue number parsing
                    try:
                        residue_number = int(line[55:62].strip())
                    except ValueError:
                        logger.warning(f"Line {line_num}: Invalid residue number: {line}")
                        continue
                    
                    atom_type = line[62:70].strip()
                    element = line[70:74].strip()
                    
                    # Handle missing or invalid charge field
                    try:
                        charge = line[74:80].strip() if len(line) >= 80 else "0.0"
                        # Test if it's a valid float
                        float(charge)
                    except ValueError:
                        logger.warning(f"Line {line_num}: Invalid charge value '{charge}'. Using 0.0 instead.")
                        charge = "0.0"
                    
                    # Validate essential fields
                    if not atom_name:
                        logger.warning(f"Line {line_num}: Missing atom name in line: {line}")
                        continue
                    
                    atom = {
                        'atom_name': atom_name,
                        'x': x,
                        'y': y,
                        'z': z,
                        'residue_name': residue_name,
                        'residue_number': residue_number,
                        'atom_type': atom_type,
                        'element': element,
                        'charge': charge,
                        'line_number': line_num  # Store the line number for reference
                    }
                    current_molecule.append(atom)
                    atom_count += 1
                except (ValueError, IndexError) as e:
                    logger.warning(f"Line {line_num}: Error parsing line: {line} - {str(e)}")
                    continue
        
        # Add the last molecule if it wasn't terminated with "end"
        if current_molecule:
            molecules.append(current_molecule)
            molecule_count += 1
            logger.warning("Last molecule block was not terminated with 'end'")
            
        # Final validation
        if not molecules:
            logger.warning(f"No valid molecule blocks found in CAR file: {filename}")
            raise ValueError(f"No valid molecule blocks found in CAR file: {filename}")
        
        logger.info(f"Parsed {atom_count} atoms across {molecule_count} molecules from {filename}")
            
        return header_lines, molecules, pbc_coords
        
    except FileNotFoundError:
        logger.error(f"CAR file not found: {filename}")
        raise
    except Exception as e:
        logger.error(f"Error parsing CAR file: {filename} - {str(e)}")
        raise ValueError(f"Invalid CAR file format: {str(e)}")

def car_blocks_to_molecules(molecule_blocks: List[List[Dict[str, Any]]]) -> List[Molecule]:
    """
    Converts CAR molecule blocks (lists of atom dictionaries) to Molecule objects.
    
    Args:
        molecule_blocks (list): List of molecule blocks from parse_car.
        
    Returns:
        list: List of Molecule objects.
    """
    molecules = []
    
    for block in molecule_blocks:
        atoms = []
        # First pass: Create all atoms (needed for connections mapping later)
        for atom_dict in block:
            atom = Atom(
                atom_name=atom_dict['atom_name'],
                x=atom_dict['x'],
                y=atom_dict['y'],
                z=atom_dict['z'],
                residue_name=atom_dict['residue_name'],
                residue_number=atom_dict['residue_number'],
                atom_type=atom_dict['atom_type'],
                element=atom_dict['element'],
                charge=atom_dict['charge'],
                # Connections will be set later if available in MDF data
                connections=[]
            )
            atoms.append(atom)
        
        molecules.append(Molecule(atoms))
    
    return molecules