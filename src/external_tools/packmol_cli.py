#!/usr/bin/env python3
"""
Command-line interface for the Packmol tool integration.

This module provides a command-line interface for parsing, modifying,
and executing Packmol input files.

DEPRECATED: This standalone CLI implementation is deprecated and will be removed in a future version.
Please use the modular CLI implementation in src/cli/commands/packmol_command.py instead.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Add the parent directory to the Python path so we can import molsaic
parent_dir = str(Path(__file__).resolve().parents[2])
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from molsaic.external_tools import PackmolTool
from molsaic import config

def setup_logging(verbose=False, log_file="packmol_runner.log"):
    """
    Setup logging to both the console and a file.
    
    Args:
        verbose (bool): If True, use DEBUG level for console output.
        log_file (str): The file path where logs will be written.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture all messages

    # Define a log message format.
    formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")

    # Create and add a console handler.
    console_handler = logging.StreamHandler()
    console_level = logging.DEBUG if verbose else logging.INFO
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create and add a file handler.
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file.
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.debug("Verbose logging enabled.")

def parse_args():
    """
    Parse command-line arguments for the Packmol tool.
    
    Returns:
        argparse.Namespace: The parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Packmol Tool - Parse, update, generate, and execute Packmol input files."
    )
    parser.add_argument("--input-file", type=str,
                        help="Path to an existing Packmol input file to parse.")
    parser.add_argument("--output-file", type=str,
                        help="Path to write the generated Packmol input file.")
    parser.add_argument("--update-file", type=str,
                        help="Path to a JSON file containing updates to apply to the configuration.")
    parser.add_argument("--print-json", action="store_true",
                        help="Print the parsed configuration as JSON and exit.")
    parser.add_argument("--execute", action="store_true",
                        help="Execute Packmol after processing the input file.")
    parser.add_argument("--exe", type=str,
                        help="Path to the Packmol executable (overrides environment variable).")
    parser.add_argument("--log-file", type=str, default="packmol_runner.log",
                        help="File to output logs (default: packmol_runner.log).")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose (debug) logging.")
    parser.add_argument("--keep", action="store_true",
                        help="Keep workspace files after execution.")
    return parser.parse_args()

def main():
    """
    Main entry point for the Packmol CLI.
    
    DEPRECATED: This implementation is deprecated. Use the modular CLI implementation
    in src/cli/commands/packmol_command.py instead.
    """
    # Show deprecation warning
    import warnings
    warnings.warn(
        "This standalone CLI implementation is deprecated and will be removed in a future version. "
        "Please use 'molsaic packmol' instead, which provides the same functionality.",
        DeprecationWarning, stacklevel=2
    )
    args = parse_args()
    setup_logging(args.verbose, args.log_file)
    logger = logging.getLogger(__name__)
    
    # Set keep workspace flag in config
    config.keep_all_workspaces = args.keep
    
    try:
        # Create a Packmol tool instance
        executable_path = args.exe if args.exe else None
        packmol = PackmolTool(executable_path=executable_path)
        
        # Parse input file if provided
        if args.input_file:
            logger.info(f"Parsing Packmol input file: {args.input_file}")
            config_dict = packmol.parse_packmol_file(args.input_file)
        else:
            logger.error("Input file is required.")
            return 1
        
        # Print JSON and exit if requested
        if args.print_json:
            print(json.dumps(config_dict, indent=2))
            return 0
        
        # Load updates from file if provided
        update_dict = None
        if args.update_file:
            if os.path.isfile(args.update_file):
                try:
                    with open(args.update_file, 'r') as f:
                        update_dict = json.load(f)
                    logger.info(f"Loaded updates from file: {args.update_file}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse update file as JSON: {e}")
                    return 1
            else:
                logger.error(f"Update file not found: {args.update_file}")
                return 1
        
        # Execute Packmol if requested
        if args.execute:
            logger.info("Executing Packmol...")
            try:
                result = packmol.execute(
                    input_file=args.input_file,
                    output_file=args.output_file,
                    update_dict=update_dict
                )
                
                # Check if execution was successful
                if result['return_code'] == 0:
                    logger.info("Packmol execution successful!")
                    
                    # Log the output file information
                    if result.get('output_file'):
                        logger.info(f"Output file created: {result['output_file']}")
                    else:
                        logger.warning("No output file information available.")
                    
                    return 0
                else:
                    logger.error("Packmol execution failed.")
                    return 1
            except Exception as e:
                logger.error(f"Error executing Packmol: {e}")
                return 1
        # Otherwise, just update and generate a new input file
        elif args.output_file:
            logger.info(f"Generating Packmol input file: {args.output_file}")
            
            # Apply updates if provided
            if update_dict:
                config_dict = packmol.update_dict(config_dict, update_dict)
                logger.info("Applied updates to configuration.")
            
            # Generate the new input file
            try:
                packmol.generate_packmol_file(config_dict, args.output_file)
                logger.info(f"Generated input file: {args.output_file}")
                return 0
            except Exception as e:
                logger.error(f"Failed to generate input file: {e}")
                return 1
        else:
            logger.error("Either --output-file or --execute must be specified.")
            return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())