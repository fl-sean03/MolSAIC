"""
Packmol command implementation.

This module provides the CLI command for working with Packmol input files.
It allows parsing, updating, generating, and executing Packmol input files.
"""

import argparse
import json
import logging
import os
from typing import Dict, Any, Optional

from molsaic.cli.base import BaseCommand
from molsaic import config
from molsaic.external_tools import PackmolTool

class PackmolCommand(BaseCommand):
    """
    CLI command for working with Packmol input files.
    
    This command provides functionality to:
    - Parse existing Packmol input files
    - Apply updates to the configuration
    - Generate new input files
    - Execute Packmol
    """
    
    name = "packmol"
    help = "Work with Packmol input files"
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for the Packmol command.
        
        Args:
            parser (argparse.ArgumentParser): The parser to configure
        """
        parser.add_argument("--input-file", required=True,
                            help="Path to an existing Packmol input file")
        parser.add_argument("--output-file",
                            help="Path to write the generated Packmol input file")
        parser.add_argument("--update-file",
                            help="Path to a JSON file with updates to apply")
        parser.add_argument("--execute", action="store_true",
                            help="Execute Packmol after processing")
        parser.add_argument("--print-json", action="store_true",
                            help="Print configuration as JSON and exit")
        parser.add_argument("--timeout", type=int, default=900,
                            help="Timeout in seconds for Packmol execution (default: 900 seconds)")
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the Packmol command.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        self.logger.info("Executing Packmol command...")
        
        try:
            # Create a Packmol tool instance
            packmol = PackmolTool()
            
            # Parse input file
            self.logger.info(f"Parsing Packmol input file: {args.input_file}")
            config_dict = packmol.parse_packmol_file(args.input_file)
            
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
                        self.logger.info(f"Loaded updates from file: {args.update_file}")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse update file as JSON: {e}")
                        return 1
                else:
                    self.logger.error(f"Update file not found: {args.update_file}")
                    return 1
            
            # Execute Packmol if requested
            if args.execute:
                self.logger.info("Executing Packmol...")
                result = packmol.execute(
                    input_file=args.input_file,
                    output_file=args.output_file,
                    update_dict=update_dict,
                    timeout=args.timeout
                )
                self.logger.info(f"Using timeout of {args.timeout} seconds")
                
                # Check if execution was successful
                if result['return_code'] == 0:
                    self.logger.info("Packmol execution successful!")
                    if result.get('output_file'):
                        self.logger.info(f"Output file created: {result['output_file']}")
                else:
                    self.logger.error("Packmol execution failed.")
                    return 1
            # Otherwise, just update and generate a new input file
            elif args.output_file:
                self.logger.info(f"Generating Packmol input file: {args.output_file}")
                
                # Apply updates if provided
                if update_dict:
                    config_dict = packmol.update_dict(config_dict, update_dict)
                    self.logger.info("Applied updates to configuration.")
                
                # Generate the new input file
                packmol.generate_packmol_file(config_dict, args.output_file)
                self.logger.info(f"Generated input file: {args.output_file}")
            else:
                self.logger.error("Either --output-file or --execute must be specified.")
                return 1
                
            return 0
        except Exception as e:
            self.logger.error(f"Packmol operation failed: {str(e)}")
            # Keep workspace on error
            config.keep_session_workspace = True
            self.logger.info(f"Logs available in workspace: {config.session_workspace.current_workspace}")
            return 1

# Standalone entry point for direct execution
def main():
    """Entry point for directly running the Packmol command."""
    import argparse
    from molsaic import config
    
    # Set up logging
    config.setup_logging()
    
    # Create parser
    parser = argparse.ArgumentParser(description="Packmol Tool - Work with Packmol input files")
    
    # Add command-specific arguments
    cmd = PackmolCommand()
    cmd.configure_parser(parser)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    return cmd.execute(args)

if __name__ == "__main__":
    import sys
    sys.exit(main())