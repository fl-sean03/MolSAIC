"""
Module for parsing PDB (Protein Data Bank) files.
"""

import logging
import re
from moltools.models.atom import Atom
from moltools.models.molecule import Molecule

logger = logging.getLogger(__name__)

def parse_pdb(filename):
    """
    Parses a PDB file and returns header information, a list of atom records, and PBC information if present.
    
    The PDB file is assumed to use fixed-width formatting with the following standard fields:
      - Record name (columns 1-6)
      - Atom serial number (columns 7-11)
      - Atom name (columns 13-16)
      - Residue name (columns 18-20)
      - Chain identifier (column 22)
      - Residue sequence number (columns 23-26)
      - X, Y, Z coordinates (columns 31-38, 39-46, 47-54)
      - Occupancy (columns 55-60)
      - Temperature factor (columns 61-66)
      - Element symbol (columns 77-78)
    
    Additionally, if present, the CRYST1 record provides periodic boundary condition (PBC)
    data with the following fields:
      - a, b, c (columns 7-15, 16-24, 25-33)
      - alpha, beta, gamma (columns 34-40, 41-47, 48-54)
      - Space group (columns 56-66)
    
    Args:
        filename (str): Path to the PDB file.
        
    Returns:
        tuple: A tuple containing:
            - header_lines (list): List of header lines (e.g. HEADER, TITLE, REMARK).
            - atoms (list): List of atom dictionaries. Each dictionary contains:
                  'atom_name': str, 
                  'x': float, 'y': float, 'z': float,
                  'residue_name': str,
                  'residue_number': int,
                  'atom_type': str, 
                  'element': str,
                  'charge': str,
                  'chain_id': str,
                  'occupancy': float,
                  'temperature_factor': float
            - pbc (tuple or None): A tuple of the form (a, b, c, alpha, beta, gamma, space_group)
              extracted from a CRYST1 record, or None if no CRYST1 record is found.
              
    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If an error occurs during parsing.
    """
    atoms = []
    header_lines = []
    pbc = None

    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # First pass: extract header lines and CRYST1 (PBC) information.
        for line in lines:
            if line.startswith(('HEADER', 'TITLE', 'REMARK')):
                header_lines.append(line.strip())
            elif line.startswith('CRYST1'):
                try:
                    a = float(line[6:15].strip())
                    b = float(line[15:24].strip())
                    c = float(line[24:33].strip())
                    alpha = float(line[33:40].strip())
                    beta = float(line[40:47].strip())
                    gamma = float(line[47:54].strip())
                    space_group = line[55:66].strip()
                    pbc = (a, b, c, alpha, beta, gamma, space_group)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse CRYST1 line: {line.strip()} - {str(e)}")
        
        # Second pass: parse ATOM and HETATM records.
        for line in lines:
            if not (line.startswith("ATOM") or line.startswith("HETATM")):
                continue
            try:
                # Use fixed-width columns (1-indexed):
                # Record name: columns 1-6 (line[0:6])
                # Atom serial number: columns 7-11 (line[6:11])
                # Atom name: columns 13-16 (line[12:16])
                # Residue name: columns 18-20 (line[17:20])
                # Chain identifier: column 22 (line[21:22])
                # Residue sequence number: columns 23-26 (line[22:26])
                # X: columns 31-38 (line[30:38])
                # Y: columns 39-46 (line[38:46])
                # Z: columns 47-54 (line[46:54])
                # Occupancy: columns 55-60 (line[54:60])
                # Temperature factor: columns 61-66 (line[60:66])
                # Element: columns 77-78 (line[76:78])
                record = line[0:6].strip()
                if record not in ("ATOM", "HETATM"):
                    continue
                serial = int(line[6:11].strip())
                atom_name = line[12:16].strip()
                residue_name = line[17:20].strip()
                chain_id = line[21:22].strip()
                residue_number = int(line[22:26].strip())
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
                occupancy_str = line[54:60].strip()
                occupancy = float(occupancy_str) if occupancy_str else 1.0
                temp_factor_str = line[60:66].strip()
                temperature_factor = float(temp_factor_str) if temp_factor_str else 0.0
                
                element = line[76:78].strip()
                if not element and atom_name:
                    element = re.sub(r'[0-9]+', '', atom_name).strip()
                
                # Charge is not standard; default to "0.0"
                charge = "0.0"
                
                # Normalize near-zero coordinates.
                x = 0.0 if abs(x) < 1e-8 else x
                y = 0.0 if abs(y) < 1e-8 else y
                z = 0.0 if abs(z) < 1e-8 else z
                
                atom = {
                    'atom_name': atom_name,
                    'x': x,
                    'y': y,
                    'z': z,
                    'residue_name': residue_name,
                    'residue_number': residue_number,
                    'atom_type': atom_name,  # Default type is the atom name.
                    'element': element,
                    'charge': charge,
                    'chain_id': chain_id,
                    'occupancy': occupancy,
                    'temperature_factor': temperature_factor
                }
                atoms.append(atom)
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing atom line: {line.strip()} - {str(e)}")
                continue
        
        if not atoms:
            logger.warning(f"No valid atom records found in PDB file: {filename}")
        
        return header_lines, atoms, pbc
        
    except FileNotFoundError:
        logger.error(f"PDB file not found: {filename}")
        raise
    except Exception as e:
        logger.error(f"Error parsing PDB file {filename}: {str(e)}")
        raise ValueError(f"Invalid PDB file format: {str(e)}")

def pdb_atoms_to_molecules(atoms):
    """
    Converts PDB atom records to Molecule objects, grouped by residue.
    
    Args:
        atoms (list): List of atom dictionaries from parse_pdb.
        
    Returns:
        list: List of Molecule objects.
    """
    # Group atoms by residue (consider chain_id if needed)
    residues = {}
    for atom_dict in atoms:
        key = (atom_dict['residue_name'], atom_dict['residue_number'])
        if key not in residues:
            residues[key] = []
        residues[key].append(atom_dict)
    
    # Create a Molecule for each residue
    molecules = []
    for residue_atoms in residues.values():
        atoms = []
        for atom_dict in residue_atoms:
            atom = Atom(
                atom_name=atom_dict['atom_name'],
                x=atom_dict['x'],
                y=atom_dict['y'],
                z=atom_dict['z'],
                residue_name=atom_dict['residue_name'],
                residue_number=atom_dict['residue_number'],
                atom_type=atom_dict.get('atom_type', atom_dict['atom_name']),
                element=atom_dict['element'],
                charge=atom_dict['charge']
            )
            atoms.append(atom)
        
        molecules.append(Molecule(atoms))
    
    return molecules