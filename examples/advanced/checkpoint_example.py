#!/usr/bin/env python3
"""
Example demonstrating pipeline checkpointing for long-running operations.
"""

import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the pipeline
from moltools.pipeline import MolecularPipeline

# Input/output paths for example
INPUT_CAR = "../samplefiles/1NEC/NEC_0H.car"
INPUT_MDF = "../samplefiles/1NEC/NEC_0H.mdf" 
FF_MAPPING = "../mappings/charge_to_ff.json"
CHARGE_MAPPING = "../mappings/ff_to_charge.json"

# Create output directory if needed
OUTPUT_DIR = "checkpoint_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_checkpoint():
    """Create and save a pipeline checkpoint."""
    logger.info("Creating a pipeline checkpoint...")
    
    # Output files
    checkpoint_file = os.path.join(OUTPUT_DIR, "pipeline.checkpoint")
    
    # Create pipeline
    pipeline = MolecularPipeline()
    
    # Load data and run some transformations
    logger.info("Loading molecular data and running initial transformations...")
    pipeline.load(INPUT_CAR, INPUT_MDF)
    pipeline.update_ff_types(FF_MAPPING)
    
    # Save the pipeline state to a checkpoint
    logger.info("Saving pipeline checkpoint...")
    pipeline.save_checkpoint(checkpoint_file)
    
    logger.info(f"Checkpoint saved to: {checkpoint_file}")
    return checkpoint_file

def resume_from_checkpoint(checkpoint_file):
    """Resume pipeline processing from a checkpoint."""
    logger.info(f"Resuming from checkpoint: {checkpoint_file}")
    
    # Output files
    output_car = os.path.join(OUTPUT_DIR, "checkpoint_output.car")
    output_mdf = os.path.join(OUTPUT_DIR, "checkpoint_output.mdf")
    
    # Load the pipeline from checkpoint
    pipeline = MolecularPipeline.load_checkpoint(checkpoint_file)
    
    # Continue with additional transformations
    logger.info("Continuing with additional transformations...")
    pipeline.update_charges(CHARGE_MAPPING)
    pipeline.generate_grid(grid_dims=(2, 2, 2), gap=2.0)
    
    # Save final result
    logger.info("Saving final output...")
    pipeline.save(output_car, output_mdf, "NEC")
    
    logger.info(f"Final outputs: {output_car}, {output_mdf}")
    return output_car, output_mdf

def simulate_distributed_workflow():
    """
    Simulate a distributed workflow where:
    1. Initial transformations are run on one machine and checkpointed
    2. Further processing continues on another machine from the checkpoint
    """
    logger.info("Simulating distributed workflow with checkpointing")
    
    # First part: Create and save checkpoint
    logger.info("==== PART 1: Initial Processing ====")
    checkpoint_file = create_checkpoint()
    
    # Simulate transferring checkpoint to another system
    logger.info("\nSimulating transfer of checkpoint file to another system...")
    time.sleep(2)  # Just for demonstration
    
    # Second part: Resume from checkpoint
    logger.info("\n==== PART 2: Continued Processing ====")
    output_files = resume_from_checkpoint(checkpoint_file)
    
    return output_files

def main():
    """Run the checkpointing example."""
    logger.info("Starting MolecularPipeline checkpointing example")
    
    # Run simulated distributed workflow
    output_files = simulate_distributed_workflow()
    
    print("\n" + "="*80)
    print("CHECKPOINTING EXAMPLE COMPLETED")
    print("="*80)
    print(f"Final outputs: {output_files[0]}, {output_files[1]}")
    print("="*80)
    
    print("\nThis example demonstrates how pipeline processing can be:")
    print("1. Started on one system")
    print("2. Saved to a checkpoint file")
    print("3. Transferred to another system")
    print("4. Resumed and completed from the checkpoint")
    print("\nThis is useful for:")
    print("- Long-running processes that may be interrupted")
    print("- Distributed processing across multiple systems")
    print("- Collaborative workflows where different team members handle different stages")

if __name__ == "__main__":
    main()