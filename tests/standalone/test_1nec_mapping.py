#!/usr/bin/env python3
"""
Test script to verify force-field and charge updates with 1NEC sample files.
"""

import sys
from pathlib import Path

from moltools.transformers.update_ff import update_ff_types
from moltools.transformers.update_charges import update_charges

# Path to sample files
SAMPLE_PATH = Path("samplefiles/1NEC")
CAR_FILE = SAMPLE_PATH / "NEC_0H.car"
MDF_FILE = SAMPLE_PATH / "NEC_0H.mdf"

# Output files
OUTPUT_PATH = Path("test_outputs")
FF_OUTPUT_CAR = OUTPUT_PATH / "ff_updated_1nec.car"
FF_OUTPUT_MDF = OUTPUT_PATH / "ff_updated_1nec.mdf"
CHARGE_OUTPUT_CAR = OUTPUT_PATH / "charge_updated_1nec.car"
CHARGE_OUTPUT_MDF = OUTPUT_PATH / "charge_updated_1nec.mdf"

# Mapping files
MAPPING_PATH = Path("mappings")
CHARGE_TO_FF = MAPPING_PATH / "charge_to_ff.json"
FF_TO_CHARGE = MAPPING_PATH / "ff_to_charge.json"

def test_ff_update():
    """Test force-field type updates using 1NEC files."""
    print(f"Updating force-field types for files: {CAR_FILE}, {MDF_FILE}")
    
    # Update force-field types
    results = update_ff_types(
        car_file=str(CAR_FILE),
        mdf_file=str(MDF_FILE),
        output_car=str(FF_OUTPUT_CAR),
        output_mdf=str(FF_OUTPUT_MDF),
        mapping_file=str(CHARGE_TO_FF)
    )
    
    print(f"Force-field update results: {results}")
    
    # Verify output files exist and have content
    print(f"CAR file size: {FF_OUTPUT_CAR.stat().st_size} bytes")
    print(f"MDF file size: {FF_OUTPUT_MDF.stat().st_size} bytes")
    
    # Print summary and sample of updated files
    with open(FF_OUTPUT_CAR, 'r') as f:
        car_lines = f.readlines()
        print(f"CAR file lines: {len(car_lines)}")
        print(f"Sample updated lines:")
        for i, line in enumerate(car_lines):
            if i > 4 and i < 10:  # Skip header, show a few atom lines
                print(f"  {line.strip()}")
    
    with open(FF_OUTPUT_MDF, 'r') as f:
        mdf_lines = f.readlines()
        print(f"MDF file lines: {len(mdf_lines)}")
        print(f"Sample updated lines:")
        for i, line in enumerate(mdf_lines):
            if "XXXX_1:C1" in line or "XXXX_1:N1" in line:
                print(f"  {line.strip()}")

def test_charge_update():
    """Test charge updates using 1NEC files."""
    print(f"Updating charges for files: {CAR_FILE}, {MDF_FILE}")
    
    # Update charges
    results = update_charges(
        car_file=str(CAR_FILE),
        mdf_file=str(MDF_FILE),
        output_car=str(CHARGE_OUTPUT_CAR),
        output_mdf=str(CHARGE_OUTPUT_MDF),
        mapping_file=str(FF_TO_CHARGE)
    )
    
    print(f"Charge update results: {results}")
    
    # Verify output files exist and have content
    print(f"CAR file size: {CHARGE_OUTPUT_CAR.stat().st_size} bytes")
    print(f"MDF file size: {CHARGE_OUTPUT_MDF.stat().st_size} bytes")
    
    # Print summary and sample of updated files
    with open(CHARGE_OUTPUT_CAR, 'r') as f:
        car_lines = f.readlines()
        print(f"CAR file lines: {len(car_lines)}")
        print(f"Sample updated lines:")
        for i, line in enumerate(car_lines):
            if i > 4 and i < 10:  # Skip header, show a few atom lines
                print(f"  {line.strip()}")
    
    with open(CHARGE_OUTPUT_MDF, 'r') as f:
        mdf_lines = f.readlines()
        print(f"MDF file lines: {len(mdf_lines)}")
        print(f"Sample updated lines:")
        for i, line in enumerate(mdf_lines):
            if "XXXX_1:C1" in line or "XXXX_1:N1" in line:
                print(f"  {line.strip()}")

if __name__ == "__main__":
    print("=== Testing force-field type updates ===")
    test_ff_update()
    print("\n=== Testing charge updates ===")
    test_charge_update()