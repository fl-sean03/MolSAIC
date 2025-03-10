#!/usr/bin/env python3
"""
Example of MSI2NAMD conversion with MolSAIC.

This example demonstrates how to use the msi2namd method to
convert molecular files to NAMD format using the external tools integration
framework.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to be able to import molsaic
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from molsaic.pipeline import MolecularPipeline

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """Run the MSI2NAMD conversion example."""
    # Define sample files
    sample_dir = Path(__file__).parent.parent.parent / "samplefiles" / "1NEC"
    car_file = sample_dir / "NEC_0H.car"
    mdf_file = sample_dir / "NEC_0H.mdf"
    
    # Create output directory
    output_dir = Path("namd_output")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Converting {car_file.name} and {mdf_file.name} to NAMD format using MSI2NAMD...")
    
    try:
        # Create pipeline
        pipeline = MolecularPipeline(debug=True, debug_prefix="debug_namd_")
        
        # Load molecular system
        pipeline.load(str(car_file), str(mdf_file))
        
        # Convert to NAMD format using MSI2NAMD
        pipeline.msi2namd(
            output_dir=str(output_dir),
            residue_name="NEC",
            # Parameter file would be specified here if available
            # parameter_file="path/to/params.prm",
            cleanup_workspace=True,
            charge_groups=False
        )
        
        # Print output files
        print("\nGenerated NAMD files:")
        for key, file_path in pipeline.namd_files.items():
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / 1024  # Size in KB
                print(f"  {key}: {os.path.basename(file_path)} ({file_size:.1f} KB)")
        
        print("\nConversion complete!")
        
    except (ValueError, RuntimeError) as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()