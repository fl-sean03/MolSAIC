#!/usr/bin/env python3
"""
Test script to verify parsing and handling of 3NEC sample files.
"""

import sys
from pathlib import Path

from moltools.parsers.car_parser import parse_car, car_blocks_to_molecules
from moltools.parsers.mdf_parser import parse_mdf
from moltools.transformers.grid import grid_from_files

# Path to sample files
SAMPLE_PATH = Path("samplefiles/3NEC")
CAR_FILE = SAMPLE_PATH / "3_NEC0H.car"
MDF_FILE = SAMPLE_PATH / "3_NEC0H.mdf"

def test_3nec_parsing():
    """Test parsing of 3NEC files with multiple molecules."""
    print(f"Parsing 3NEC CAR file: {CAR_FILE}")
    header_lines, molecules, pbc_coords = parse_car(str(CAR_FILE))
    
    print(f"Header lines: {len(header_lines)}")
    print(f"Number of molecules: {len(molecules)}")
    
    for i, mol in enumerate(molecules):
        print(f"Molecule {i+1}: {len(mol)} atoms")
    
    print(f"PBC coordinates: {pbc_coords}")
    
    # Convert to Molecule objects
    mol_objects = car_blocks_to_molecules(molecules)
    print(f"Molecule objects: {len(mol_objects)}")
    
    # Test MDF parsing
    print(f"\nParsing 3NEC MDF file: {MDF_FILE}")
    headers, mdf_data = parse_mdf(str(MDF_FILE))
    
    print(f"Header lines: {len(headers)}")
    print(f"MDF data entries: {len(mdf_data)}")
    
    # Find unique residue names in MDF data
    residues = set()
    for key in mdf_data.keys():
        residues.add(key[0])
    print(f"Unique residues in MDF data: {residues}")

def test_3nec_grid():
    """Test grid creation using 3NEC files with multiple molecules."""
    print(f"Creating grid from 3NEC files: {CAR_FILE}, {MDF_FILE}")
    
    try:
        system = grid_from_files(
            str(CAR_FILE),
            str(MDF_FILE),
            grid_dims=(2, 2, 2),
            gap=2.0
        )
        
        print(f"Created system with {len(system.molecules)} molecules")
        print(f"PBC dimensions: {system.pbc[0:3]}")
        
        # Check first few molecules
        for i, mol in enumerate(system.molecules[:5]):
            print(f"Grid molecule {i+1}: {len(mol.atoms)} atoms")
            
    except Exception as e:
        print(f"Error creating grid from 3NEC files: {str(e)}")

if __name__ == "__main__":
    print("=== Testing 3NEC file parsing ===")
    test_3nec_parsing()
    print("\n=== Testing grid creation with 3NEC files ===")
    test_3nec_grid()