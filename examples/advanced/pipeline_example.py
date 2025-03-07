#!/usr/bin/env python3
"""
Example script demonstrating the MolecularPipeline for chaining multiple transformations.

This script shows how to:
1. Load molecular data from files
2. Update force-field types and charges
3. Generate a grid replication
4. Save the final results
"""

import os
import logging
from time import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the pipeline
from src.pipeline import MolecularPipeline

# Input/output paths for example
INPUT_CAR = "../../tests/data/1NEC/NEC_0H.car"
INPUT_MDF = "../../tests/data/1NEC/NEC_0H.mdf" 
FF_MAPPING = "../../tests/data/mappings/charge_to_ff.json"
CHARGE_MAPPING = "../../tests/data/mappings/ff_to_charge.json"

# Create output directory if needed
OUTPUT_DIR = "pipeline_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_pipeline_with_debug():
    """
    Run a pipeline with debug output for intermediate steps.
    """
    logger.info("Running pipeline with debug output...")
    start_time = time()
    
    # Output files
    output_car = os.path.join(OUTPUT_DIR, "pipeline_output.car")
    output_mdf = os.path.join(OUTPUT_DIR, "pipeline_output.mdf")
    debug_prefix = os.path.join(OUTPUT_DIR, "debug_")
    
    # Create pipeline with debug enabled
    pipeline = MolecularPipeline(debug=True, debug_prefix=debug_prefix)
    
    # Load data
    logger.info("Loading molecular data...")
    pipeline.load(INPUT_CAR, INPUT_MDF)
    
    # Update force-field types
    logger.info("Updating force-field types...")
    pipeline.update_ff_types(FF_MAPPING)  # Creates debug_1_*.car/mdf
    
    # Update charges
    logger.info("Updating charges...")
    pipeline.update_charges(CHARGE_MAPPING)  # Creates debug_2_*.car/mdf
    
    # Generate grid
    logger.info("Generating grid replication...")
    pipeline.generate_grid(grid_dims=(2, 2, 2), gap=2.0)  # Creates debug_3_*.car/mdf
    
    # Save final result
    logger.info("Saving final output...")
    pipeline.save(output_car, output_mdf, "NEC")
    
    elapsed = time() - start_time
    logger.info(f"Pipeline execution completed in {elapsed:.2f} seconds")
    logger.info(f"Final outputs: {output_car}, {output_mdf}")
    logger.info(f"Debug outputs: {debug_prefix}*")
    
    return output_car, output_mdf

def run_fluent_pipeline():
    """
    Run a pipeline with method chaining (fluent API).
    """
    logger.info("Running fluent pipeline...")
    start_time = time()
    
    # Output files
    output_car = os.path.join(OUTPUT_DIR, "fluent_output.car")
    output_mdf = os.path.join(OUTPUT_DIR, "fluent_output.mdf")
    
    # Create pipeline and chain all operations
    logger.info("Executing chained pipeline...")
    
    (MolecularPipeline()
        .load(INPUT_CAR, INPUT_MDF)
        .update_ff_types(FF_MAPPING)
        .update_charges(CHARGE_MAPPING)
        .generate_grid(grid_dims=(3, 3, 3), gap=1.5)
        .save(output_car, output_mdf, "NEC"))
    
    elapsed = time() - start_time
    logger.info(f"Fluent pipeline execution completed in {elapsed:.2f} seconds")
    logger.info(f"Final outputs: {output_car}, {output_mdf}")
    
    return output_car, output_mdf

def main():
    """Run the pipeline examples."""
    logger.info("Starting MolecularPipeline example")
    
    # Run both pipeline examples
    debug_files = run_pipeline_with_debug()
    print("\n" + "-"*80 + "\n")
    fluent_files = run_fluent_pipeline()
    
    print("\n" + "="*80)
    print("PIPELINE EXAMPLES COMPLETED")
    print("="*80)
    print(f"Debug pipeline outputs:  {debug_files[0]}, {debug_files[1]}")
    print(f"                         {os.path.join(OUTPUT_DIR, 'debug_*')}")
    print(f"Fluent pipeline outputs: {fluent_files[0]}, {fluent_files[1]}")
    print("="*80)
    
    print("\nNote: The debug pipeline creates intermediate files at each step,")
    print("while the fluent pipeline only creates the final output files.")
    print("\nBoth approaches use the same System object model internally,")
    print("but offer different API styles depending on your needs.")

if __name__ == "__main__":
    main()