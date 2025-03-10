#!/usr/bin/env python3
"""
Example script demonstrating how to use the Packmol integration tool.

This example shows:
1. Parsing an existing Packmol input file
2. Modifying the configuration
3. Generating a new input file
4. Executing Packmol with the new configuration

Requirements:
- Packmol executable must be installed and available in PATH or 
  configured via environment variable MOLSAIC_PACKMOL_PATH
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the parent directory to the Python path so we can import molsaic
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from molsaic.external_tools import PackmolTool

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    
    # Example input file path (you would replace this with your actual file)
    example_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.abspath(os.path.join(example_dir, '../../data/molecules'))
    
    # Example Packmol input file (adjust this to an actual file in your system)
    input_file = os.path.join(example_dir, "example.inp")
    
    # Create a sample input file if it doesn't exist
    if not os.path.exists(input_file):
        create_sample_input_file(input_file, resources_dir)
    
    # Create a Packmol tool instance
    packmol = PackmolTool()
    
    # Parse the existing Packmol input file
    logging.info("Parsing Packmol input file...")
    with open(input_file, 'r') as f:
        config = packmol.parse_packmol_file(input_file)
    
    # Print the parsed configuration
    logging.info("Parsed configuration:")
    print(json.dumps(config, indent=2))
    
    # Modify the configuration
    logging.info("Modifying configuration...")
    
    # Example: Change the output file
    if 'output' in config['global']:
        config['global']['output'] = ["modified_output.pdb"]
    else:
        config['global']['output'] = ["modified_output.pdb"]
    
    # Example: Change the tolerance
    if 'tolerance' in config['global']:
        config['global']['tolerance'] = ["2.0"]  # Increase tolerance
    
    # Example: Modify a structure block
    if config['structures']:
        # Update the number of molecules in the first structure
        if 'number' in config['structures'][0]['properties']:
            current_number = int(config['structures'][0]['properties']['number'][0])
            config['structures'][0]['properties']['number'] = [str(current_number * 2)]
    
    # Generate a new input file
    output_file = os.path.join(os.path.dirname(input_file), "modified.inp")
    logging.info(f"Generating new input file: {output_file}")
    packmol.generate_packmol_file(config, output_file)
    
    # Execute Packmol with the new input file
    logging.info("Executing Packmol...")
    try:
        result = packmol.execute(input_file=output_file)
        
        # Check if execution was successful
        if result['return_code'] == 0:
            logging.info("Packmol execution successful!")
            if result.get('output_file'):
                logging.info(f"Output file created: {result['output_file']}")
        else:
            logging.error("Packmol execution failed.")
    except Exception as e:
        logging.error(f"Error executing Packmol: {e}")

def create_sample_input_file(file_path, resources_dir):
    """Create a sample Packmol input file for demonstration purposes."""
    # Example assumes there are PDB files available in the resources directory
    # Adjust the file paths as needed
    with open(file_path, 'w') as f:
        f.write(f"""# Example Packmol input file for demonstration
# Created automatically by the example script

tolerance 2.0
filetype pdb
output example_output.pdb

# Water box
structure {resources_dir}/water.pdb
  number 100
  inside box 0. 0. 0. 30. 30. 30.
end structure

# Solute molecule
structure {resources_dir}/molecule.pdb
  number 1
  fixed 15. 15. 15. 0. 0. 0.
end structure
""")
    logging.info(f"Created sample input file: {file_path}")
    logging.warning("Using a sample input file with placeholder paths. Please modify with actual molecule files.")

if __name__ == "__main__":
    main()