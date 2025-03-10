#!/usr/bin/env python3
"""
Test script to verify parsing of 1NEC sample files.
"""

import sys
from pathlib import Path

from molsaic.parsers.car_parser import parse_car, car_blocks_to_molecules
from molsaic.parsers.mdf_parser import parse_mdf
from molsaic.parsers.pdb_parser import parse_pdb, pdb_atoms_to_molecules

# Path to sample files
SAMPLE_PATH = Path("samplefiles/1NEC")
CAR_FILE = SAMPLE_PATH / "NEC_0H.car"
MDF_FILE = SAMPLE_PATH / "NEC_0H.mdf"
PDB_FILE = SAMPLE_PATH / "NEC_0H.pdb"

def test_car_parsing():
    """Test parsing of the CAR file."""
    print(f"Parsing CAR file: {CAR_FILE}")
    header_lines, molecules, pbc_coords = parse_car(CAR_FILE)
    
    print(f"Header lines: {len(header_lines)}")
    print(f"Molecules: {len(molecules)}")
    print(f"First molecule atoms: {len(molecules[0])}")
    print(f"PBC coordinates: {pbc_coords}")
    
    # Convert to Molecule objects
    mol_objects = car_blocks_to_molecules(molecules)
    print(f"Molecule objects: {len(mol_objects)}")
    print(f"First molecule: {mol_objects[0]}")

def test_mdf_parsing():
    """Test parsing of the MDF file."""
    print(f"Parsing MDF file: {MDF_FILE}")
    headers, mdf_data = parse_mdf(MDF_FILE)
    
    print(f"Header lines: {len(headers)}")
    print(f"MDF data entries: {len(mdf_data)}")
    print(f"Sample keys: {list(mdf_data.keys())[:5]}")
    print(f"Sample C1 data: {mdf_data.get(('NEC', 'C1'))}")

def test_pdb_parsing():
    """Test parsing of the PDB file."""
    print(f"Parsing PDB file: {PDB_FILE}")
    header_lines, atoms, pbc = parse_pdb(PDB_FILE)
    
    print(f"Header lines: {len(header_lines)}")
    print(f"Atoms: {len(atoms)}")
    print(f"PBC: {pbc}")
    
    # Convert to Molecule objects
    mol_objects = pdb_atoms_to_molecules(atoms)
    print(f"Molecule objects: {len(mol_objects)}")
    print(f"First molecule: {mol_objects[0]}")

if __name__ == "__main__":
    print("=== Testing CAR parsing ===")
    test_car_parsing()
    print("\n=== Testing MDF parsing ===")
    test_mdf_parsing()
    print("\n=== Testing PDB parsing ===")
    test_pdb_parsing()