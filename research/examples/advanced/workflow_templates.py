#!/usr/bin/env python3
"""
Example demonstrating the use of workflow templates.
"""

import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import workflow templates
from src.templates.workflows import (
    create_grid_pipeline,
    create_ff_update_pipeline,
    create_charge_update_pipeline,
    create_complete_transformation_pipeline
)

# Input/output paths for example
INPUT_CAR = "../../data/molecules/1NEC/NEC_0H.car"
INPUT_MDF = "../../data/molecules/1NEC/NEC_0H.mdf" 
FF_MAPPING = "../../data/mappings/charge_to_ff.json"
CHARGE_MAPPING = "../../data/mappings/ff_to_charge.json"

# Create output directory if needed
OUTPUT_DIR = "template_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_grid_template():
    """Example using grid template."""
    logger.info("Running grid template...")
    
    output_car = os.path.join(OUTPUT_DIR, "grid_output.car")
    output_mdf = os.path.join(OUTPUT_DIR, "grid_output.mdf")
    
    # Create and run grid pipeline
    pipeline = create_grid_pipeline(
        input_car=INPUT_CAR,
        input_mdf=INPUT_MDF,
        output_car=output_car,
        output_mdf=output_mdf,
        grid_dims=(2, 2, 2),
        gap=2.0
    )
    
    logger.info(f"Grid template complete: {len(pipeline.get_system().molecules)} molecules")
    return output_car, output_mdf

def run_ff_update_template():
    """Example using force-field update template."""
    logger.info("Running force-field update template...")
    
    output_car = os.path.join(OUTPUT_DIR, "ff_output.car")
    output_mdf = os.path.join(OUTPUT_DIR, "ff_output.mdf")
    
    # Create and run force-field pipeline
    pipeline = create_ff_update_pipeline(
        input_car=INPUT_CAR,
        input_mdf=INPUT_MDF,
        output_car=output_car,
        output_mdf=output_mdf,
        mapping_file=FF_MAPPING
    )
    
    logger.info("Force-field update template complete")
    return output_car, output_mdf

def run_charge_update_template():
    """Example using charge update template."""
    logger.info("Running charge update template...")
    
    output_car = os.path.join(OUTPUT_DIR, "charge_output.car")
    output_mdf = os.path.join(OUTPUT_DIR, "charge_output.mdf")
    
    # Create and run charge update pipeline
    pipeline = create_charge_update_pipeline(
        input_car=INPUT_CAR,
        input_mdf=INPUT_MDF,
        output_car=output_car,
        output_mdf=output_mdf,
        mapping_file=CHARGE_MAPPING
    )
    
    logger.info("Charge update template complete")
    return output_car, output_mdf

def run_complete_template():
    """Example using the complete transformation template."""
    logger.info("Running complete transformation template...")
    
    output_car = os.path.join(OUTPUT_DIR, "complete_output.car")
    output_mdf = os.path.join(OUTPUT_DIR, "complete_output.mdf")
    checkpoint_file = os.path.join(OUTPUT_DIR, "checkpoint")
    
    # Create and run complete pipeline with checkpoints
    pipeline = create_complete_transformation_pipeline(
        input_car=INPUT_CAR,
        input_mdf=INPUT_MDF,
        output_car=output_car,
        output_mdf=output_mdf,
        ff_mapping_file=FF_MAPPING,
        charge_mapping_file=CHARGE_MAPPING,
        grid_dims=(3, 3, 3),
        gap=1.5,
        debug=True,
        debug_prefix=os.path.join(OUTPUT_DIR, "debug_"),
        checkpoint_file=checkpoint_file
    )
    
    logger.info(f"Complete template with checkpointing complete: {len(pipeline.get_system().molecules)} molecules")
    logger.info(f"Checkpoint files created: {checkpoint_file}.step1 through {checkpoint_file}.step4")
    
    return output_car, output_mdf, checkpoint_file

def main():
    """Run the workflow templates examples."""
    logger.info("Starting workflow templates example")
    
    # Run each template example
    grid_files = run_grid_template()
    print("\n" + "-"*80 + "\n")
    
    ff_files = run_ff_update_template()
    print("\n" + "-"*80 + "\n")
    
    charge_files = run_charge_update_template()
    print("\n" + "-"*80 + "\n")
    
    complete_files = run_complete_template()
    
    print("\n" + "="*80)
    print("WORKFLOW TEMPLATES EXAMPLES COMPLETED")
    print("="*80)
    print(f"Grid template outputs:      {grid_files[0]}, {grid_files[1]}")
    print(f"FF update template outputs: {ff_files[0]}, {ff_files[1]}")
    print(f"Charge update outputs:      {charge_files[0]}, {charge_files[1]}")
    print(f"Complete template outputs:  {complete_files[0]}, {complete_files[1]}")
    print(f"                            Checkpoints: {complete_files[2]}.step1 - {complete_files[2]}.step4")
    print("="*80)
    
    print("\nWorkflow templates provide:")
    print("1. Simplified interfaces for common transformation patterns")
    print("2. Standardized parameter handling")
    print("3. Built-in checkpoint support for long-running processes")
    print("4. Debug output capabilities")

if __name__ == "__main__":
    main()