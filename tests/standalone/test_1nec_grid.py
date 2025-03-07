#!/usr/bin/env python3
"""
Test script to verify grid replication with 1NEC sample files.
"""

import sys
from pathlib import Path

from moltools.transformers.grid import grid_from_files, generate_grid_files

# Path to sample files
SAMPLE_PATH = Path("samplefiles/1NEC")
CAR_FILE = SAMPLE_PATH / "NEC_0H.car"
MDF_FILE = SAMPLE_PATH / "NEC_0H.mdf"

# Output files
OUTPUT_PATH = Path("test_outputs")
OUTPUT_CAR = OUTPUT_PATH / "grid_1nec.car"
OUTPUT_MDF = OUTPUT_PATH / "grid_1nec.mdf"

def test_grid_generation():
    """Test grid generation using 1NEC files."""
    print(f"Creating grid from files: {CAR_FILE}, {MDF_FILE}")
    grid_dims = (2, 2, 2)
    gap = 2.0
    
    # Generate grid files
    generate_grid_files(
        str(CAR_FILE), 
        str(MDF_FILE), 
        str(OUTPUT_CAR), 
        str(OUTPUT_MDF), 
        grid_dims=grid_dims, 
        gap=gap, 
        base_name="NEC"
    )
    
    print(f"Grid files generated:")
    print(f"CAR file: {OUTPUT_CAR}")
    print(f"MDF file: {OUTPUT_MDF}")
    
    # Verify output files exist and have content
    print(f"CAR file size: {OUTPUT_CAR.stat().st_size} bytes")
    print(f"MDF file size: {OUTPUT_MDF.stat().st_size} bytes")
    
    # Print summary of generated files
    with open(OUTPUT_CAR, 'r') as f:
        car_lines = f.readlines()
        print(f"CAR file lines: {len(car_lines)}")
        print(f"Header: {car_lines[0:5]}")
    
    with open(OUTPUT_MDF, 'r') as f:
        mdf_lines = f.readlines()
        print(f"MDF file lines: {len(mdf_lines)}")
        print(f"Header: {mdf_lines[0:5]}")
        # Count number of molecule blocks
        molecules = [line for line in mdf_lines if line.startswith("@molecule")]
        print(f"Number of molecule blocks: {len(molecules)}")

if __name__ == "__main__":
    print("=== Testing grid replication ===")
    test_grid_generation()