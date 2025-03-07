#!/usr/bin/env python3
"""
Example script demonstrating both the default object-based approach and 
the legacy file-based approach for molecular transformations.

This script shows how to:
1. Use the default object-based approach with the MolecularPipeline
2. Use the legacy file-based approach
3. Compare the two approaches with identical workflows
"""

import os
import logging
from time import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Input/output paths for examples
INPUT_CAR = "../samplefiles/1NEC/NEC_0H.car"
INPUT_MDF = "../samplefiles/1NEC/NEC_0H.mdf" 
FF_MAPPING = "../mappings/charge_to_ff.json"
CHARGE_MAPPING = "../mappings/ff_to_charge.json"

# Create output directory if needed
OUTPUT_DIR = "comparison_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_file_based_approach():
    """
    Demonstrate the legacy file-based approach with multiple transformations
    requiring intermediate files.
    """
    logger.info("Running file-based approach...")
    start_time = time()
    
    # Import file-based transformation functions
    from moltools.transformers.update_ff import update_ff_types
    from moltools.transformers.update_charges import update_charges
    from moltools.transformers.grid import replicate_grid
    
    # Step 1: Update force field types (with intermediate files)
    ff_output_car = os.path.join(OUTPUT_DIR, "file_step1.car")
    ff_output_mdf = os.path.join(OUTPUT_DIR, "file_step1.mdf")
    
    logger.info("Step 1: Updating force field types...")
    update_ff_types(
        car_file=INPUT_CAR,
        mdf_file=INPUT_MDF,
        output_car=ff_output_car,
        output_mdf=ff_output_mdf,
        mapping_file=FF_MAPPING
    )
    
    # Step 2: Update charges (with more intermediate files)
    charge_output_car = os.path.join(OUTPUT_DIR, "file_step2.car")
    charge_output_mdf = os.path.join(OUTPUT_DIR, "file_step2.mdf")
    
    logger.info("Step 2: Updating charges...")
    update_charges(
        car_file=ff_output_car,
        mdf_file=ff_output_mdf,
        output_car=charge_output_car,
        output_mdf=charge_output_mdf,
        mapping_file=CHARGE_MAPPING
    )
    
    # Step 3: Create grid replication (final output)
    grid_output_car = os.path.join(OUTPUT_DIR, "file_final.car")
    grid_output_mdf = os.path.join(OUTPUT_DIR, "file_final.mdf")
    
    logger.info("Step 3: Creating grid replication...")
    replicate_grid(
        car_file=charge_output_car,
        mdf_file=charge_output_mdf,
        output_car=grid_output_car,
        output_mdf=grid_output_mdf,
        grid_dims=(2, 2, 2),
        gap=2.0
    )
    
    elapsed = time() - start_time
    logger.info(f"File-based approach completed in {elapsed:.2f} seconds")
    logger.info(f"Final outputs: {grid_output_car}, {grid_output_mdf}")
    
    # Cleanup intermediate files (optional)
    # os.remove(ff_output_car)
    # os.remove(ff_output_mdf)
    # os.remove(charge_output_car)
    # os.remove(charge_output_mdf)
    
    return elapsed


def run_object_based_approach():
    """
    Demonstrate the default object-based approach with chained transformations
    and no intermediate files.
    """
    logger.info("Running object-based approach...")
    start_time = time()
    
    # Import object-based pipeline
    from moltools.pipeline import MolecularPipeline
    
    # Create output paths
    output_car = os.path.join(OUTPUT_DIR, "object_final.car")
    output_mdf = os.path.join(OUTPUT_DIR, "object_final.mdf")
    
    # Chain all operations in a fluent API with no intermediate files
    logger.info("Running pipeline with chained operations...")
    pipeline = MolecularPipeline()
    pipeline.load(INPUT_CAR, INPUT_MDF) \
            .update_ff_types(mapping_file=FF_MAPPING) \
            .update_charges(mapping_file=CHARGE_MAPPING) \
            .generate_grid(grid_dims=(2, 2, 2), gap=2.0) \
            .save(output_car, output_mdf)
            
    elapsed = time() - start_time
    logger.info(f"Object-based approach completed in {elapsed:.2f} seconds")
    logger.info(f"Final outputs: {output_car}, {output_mdf}")
    
    return elapsed


def run_object_based_with_debug():
    """
    Demonstrate the default object-based approach with debug output
    for examining intermediate steps.
    """
    logger.info("Running object-based approach with debug output...")
    start_time = time()
    
    # Import object-based pipeline
    from moltools.pipeline import MolecularPipeline
    
    # Create output paths
    output_car = os.path.join(OUTPUT_DIR, "object_debug_final.car")
    output_mdf = os.path.join(OUTPUT_DIR, "object_debug_final.mdf")
    
    # Enable debug mode with a prefix for intermediate files
    logger.info("Running pipeline with debug output...")
    pipeline = MolecularPipeline(debug=True, debug_prefix=os.path.join(OUTPUT_DIR, "debug_"))
    
    # Each step will create intermediate files with the debug prefix
    pipeline.load(INPUT_CAR, INPUT_MDF)  # Initial system state
    pipeline.update_ff_types(mapping_file=FF_MAPPING)  # Creates debug_1_*.car/mdf
    pipeline.update_charges(mapping_file=CHARGE_MAPPING)  # Creates debug_2_*.car/mdf
    pipeline.generate_grid(grid_dims=(2, 2, 2), gap=2.0)  # Creates debug_3_*.car/mdf
    pipeline.save(output_car, output_mdf)  # Final output
            
    elapsed = time() - start_time
    logger.info(f"Object-based approach with debug completed in {elapsed:.2f} seconds")
    logger.info(f"Final outputs: {output_car}, {output_mdf}")
    logger.info(f"Debug outputs: {os.path.join(OUTPUT_DIR, 'debug_*')}")
    
    return elapsed


def main():
    """Run all examples and compare results."""
    logger.info("Starting example comparing default object-based vs legacy file-based approaches")
    
    # Run both approaches
    object_time = run_object_based_approach()
    print("\n" + "-"*80 + "\n")
    debug_time = run_object_based_with_debug()
    print("\n" + "-"*80 + "\n")
    file_time = run_file_based_approach()
    
    # Compare results
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    print(f"Legacy file-based approach: {file_time:.2f} seconds")
    print(f"Default object-based approach: {object_time:.2f} seconds")
    print(f"Object with debug: {debug_time:.2f} seconds")
    print("="*80)
    
    # Note: This is a sample script - actual performance will vary based on implementation
    print("\nNOTE: The default object-based approach is generally faster")
    print("because it avoids repeated file I/O operations and parsing overhead.")
    print("\nThe debug mode adds file I/O for intermediate steps but provides valuable")
    print("visibility into the transformation process for troubleshooting.")


if __name__ == "__main__":
    main()