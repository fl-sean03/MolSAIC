#!/usr/bin/env python3
"""
Script to profile performance with 3NEC files.
"""

import cProfile
import pstats
import io
import time
from pathlib import Path

from src.parsers.car_parser import parse_car, car_blocks_to_molecules
from src.parsers.mdf_parser import parse_mdf
from src.transformers.legacy.grid import grid_from_files, generate_grid_files
from src.transformers.legacy.update_ff import update_ff_types
from src.transformers.legacy.update_charges import update_charges

# Path to sample files
SAMPLE_PATH = Path("../../data/molecules/3NEC")
CAR_FILE = SAMPLE_PATH / "3_NEC0H.car"
MDF_FILE = SAMPLE_PATH / "3_NEC0H.mdf"

# Output files
OUTPUT_PATH = Path("./outputs")
GRID_CAR = OUTPUT_PATH / "grid_3nec.car"
GRID_MDF = OUTPUT_PATH / "grid_3nec.mdf"
FF_CAR = OUTPUT_PATH / "ff_3nec.car"
FF_MDF = OUTPUT_PATH / "ff_3nec.mdf"
CHARGE_CAR = OUTPUT_PATH / "charge_3nec.car"
CHARGE_MDF = OUTPUT_PATH / "charge_3nec.mdf"

# Mapping files
MAPPING_PATH = Path("../../data/mappings")
CHARGE_TO_FF = MAPPING_PATH / "charge_to_ff.json"
FF_TO_CHARGE = MAPPING_PATH / "ff_to_charge.json"

# Create output directory if needed
OUTPUT_PATH.mkdir(exist_ok=True)

def profile_grid_generation():
    """Profile grid generation with 3NEC files."""
    print("Profiling grid generation...")
    pr = cProfile.Profile()
    pr.enable()
    
    start_time = time.time()
    grid_from_files(
        str(CAR_FILE),
        str(MDF_FILE),
        grid_dims=(4, 4, 4),
        gap=2.0
    )
    elapsed = time.time() - start_time
    
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())
    print(f"Total time: {elapsed:.2f} seconds")
    
    # Generate grid files to disk (separate timing)
    print("\nGenerating grid files...")
    start_time = time.time()
    generate_grid_files(
        str(CAR_FILE),
        str(MDF_FILE),
        str(GRID_CAR),
        str(GRID_MDF),
        grid_dims=(4, 4, 4),
        gap=2.0,
        base_name="NEC"
    )
    elapsed = time.time() - start_time
    print(f"Grid generation to disk: {elapsed:.2f} seconds")

def profile_ff_update():
    """Profile force-field update with 3NEC files."""
    print("\nProfiling force-field update...")
    pr = cProfile.Profile()
    pr.enable()
    
    start_time = time.time()
    results = update_ff_types(
        car_file=str(CAR_FILE),
        mdf_file=str(MDF_FILE),
        output_car=str(FF_CAR),
        output_mdf=str(FF_MDF),
        mapping_file=str(CHARGE_TO_FF)
    )
    elapsed = time.time() - start_time
    
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())
    
    print(f"Force-field update results: {results}")
    print(f"Total time: {elapsed:.2f} seconds")

def profile_charge_update():
    """Profile charge update with 3NEC files."""
    print("\nProfiling charge update...")
    pr = cProfile.Profile()
    pr.enable()
    
    start_time = time.time()
    results = update_charges(
        car_file=str(CAR_FILE),
        mdf_file=str(MDF_FILE),
        output_car=str(CHARGE_CAR),
        output_mdf=str(CHARGE_MDF),
        mapping_file=str(FF_TO_CHARGE)
    )
    elapsed = time.time() - start_time
    
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())
    
    print(f"Charge update results: {results}")
    print(f"Total time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    profile_grid_generation()
    profile_ff_update()
    profile_charge_update()