#\!/usr/bin/env python3
"""
Basic usage tutorial for MolSAIC package.

This tutorial demonstrates the basic usage of the MolSAIC package.
"""

from src.models.system import MolecularSystem
from src.parsers.car_parser import CARParser
from src.parsers.mdf_parser import MDFParser
from src.transformers.grid import GridTransformer

def main():
    """Main tutorial function."""
    # Load a system from CAR/MDF files
    print("Loading system from CAR/MDF files...")
    car_parser = CARParser("../../data/molecules/1NEC/NEC_0H.car")
    mdf_parser = MDFParser("../../data/molecules/1NEC/NEC_0H.mdf")
    
    # Parse the files
    car_data = car_parser.parse()
    mdf_data = mdf_parser.parse()
    
    # Create a molecular system from the data
    system = MolecularSystem.from_parsed_data(car_data, mdf_data)
    
    # Print basic system information
    print(f"System loaded: {system.name}")
    print(f"Number of atoms: {len(system.atoms)}")
    print(f"Number of molecules: {len(system.molecules)}")
    
    # Create a grid transformer to replicate the system
    grid_transformer = GridTransformer(system)
    replicated_system = grid_transformer.transform(x_copies=2, y_copies=2, z_copies=1)
    
    print("\nAfter grid replication:")
    print(f"Number of atoms: {len(replicated_system.atoms)}")
    print(f"Number of molecules: {len(replicated_system.molecules)}")
    
    print("\nTutorial completed successfully\!")

if __name__ == "__main__":
    main()
