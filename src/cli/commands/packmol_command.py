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
        parser.add_argument("--output-dir", default="packmol_output",
                            help="Directory to store the output files (default: packmol_output)")
        parser.add_argument("--timeout", type=int, default=900,
                            help="Timeout in seconds for Packmol execution (default: 900 seconds)")
        parser.add_argument("--continue-on-timeout", action="store_true",
                            help="Continue execution if timeout occurs and use partial results if available")
        parser.add_argument("--continue-on-error", action="store_true",
                            help="Continue execution even if Packmol fails (will use partial or empty results)")
    
    def _copy_output_file(self, source_file: str, output_dir: str, suffix: str = None) -> str:
        """
        Copy a file to the output directory with an optional suffix.
        
        Args:
            source_file (str): Path to the source file
            output_dir (str): Path to the output directory
            suffix (str, optional): Suffix to add to the filename (e.g., '_partial')
            
        Returns:
            str: Path to the copied file, or None if copy failed
        """
        try:
            import shutil
            basename = os.path.basename(source_file)
            
            # Add suffix if provided
            if suffix:
                name_parts = os.path.splitext(basename)
                dest_file = f"{name_parts[0]}{suffix}{name_parts[1]}"
            else:
                dest_file = basename
                
            dest_path = os.path.join(output_dir, dest_file)
            
            # Copy the file
            shutil.copy2(source_file, dest_path)
            return dest_path
        except Exception as copy_err:
            self.logger.warning(f"Could not copy output file: {str(copy_err)}")
            return None
            
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the Packmol command.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        self.logger.info("Executing Packmol command...")
        
        # Get base output directory name and handle enumeration if it exists
        base_output_dir = args.output_dir
        if not os.path.isabs(base_output_dir):
            base_output_dir = os.path.abspath(base_output_dir)
        
        # If the directory exists, enumerate it (packmol_output_1, packmol_output_2, etc.)
        output_dir = base_output_dir
        counter = 1
        while os.path.exists(output_dir):
            output_dir = f"{base_output_dir}_{counter}"
            counter += 1
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            self.logger.info(f"Using output directory: {output_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create output directory '{output_dir}': {str(e)}")
            self.logger.error("Please check directory permissions or provide a different output directory")
            return 1
        
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
                try:
                    # Pass the continue flags to the execute method
                    result = packmol.execute(
                        input_file=args.input_file,
                        output_file=args.output_file,
                        update_dict=update_dict,
                        timeout=args.timeout,
                        continue_on_error=args.continue_on_error
                    )
                    self.logger.info(f"Using timeout of {args.timeout} seconds")
                    
                    # Check if execution timed out
                    if result.get('timed_out', False):
                        self.logger.warning(f"Packmol timed out after {args.timeout} seconds")
                        
                        # Check if we have partial results
                        if result.get('output_files') and args.continue_on_timeout:
                            self.logger.info("Using partial results and continuing execution")
                            for output_file in result.get('output_files', []):
                                file_size = os.path.getsize(output_file)
                                self.logger.info(f"Partial output file: {output_file} ({file_size} bytes)")
                                
                                # Copy the partial output file to the output directory
                                copied_path = self._copy_output_file(output_file, output_dir, suffix="_partial")
                                if copied_path:
                                    self.logger.info(f"Copied partial output to: {copied_path}")
                        elif not args.continue_on_timeout:
                            self.logger.error("Timeout occurred and --continue-on-timeout not specified")
                            return 1
                        else:
                            self.logger.error("Timeout occurred and no partial results available")
                            return 1
                    # Check if execution was successful
                    elif result['return_code'] == 0:
                        self.logger.info("Packmol execution successful!")
                        if result.get('output_file'):
                            self.logger.info(f"Output file created: {result['output_file']}")
                            
                            # Copy the successful output file to the output directory
                            output_file = result['output_file']
                            copied_path = self._copy_output_file(output_file, output_dir)
                            if copied_path:
                                self.logger.info(f"Copied output to: {copied_path}")
                    # Otherwise, it failed but we're continuing
                    elif args.continue_on_error:
                        self.logger.warning("Packmol execution failed but continuing as requested")
                        if result.get('output_files'):
                            for output_file in result.get('output_files', []):
                                self.logger.info(f"Using output file despite error: {output_file}")
                                
                                # Copy the output file to the output directory
                                copied_path = self._copy_output_file(output_file, output_dir, suffix="_error")
                                if copied_path:
                                    self.logger.info(f"Copied error output to: {copied_path}")
                    else:
                        self.logger.error("Packmol execution failed.")
                        return 1
                except ValueError as e:
                    # Handle specific error for missing structure files
                    if "Missing structure files" in str(e):
                        self.logger.error(str(e))
                        
                        # Try to extract file names from input file to help the user
                        with open(args.input_file, 'r') as f:
                            content = f.read()
                            
                        # Show the structure lines to help users debug
                        structure_lines = [line.strip() for line in content.splitlines() 
                                          if line.strip().lower().startswith('structure ')]
                                          
                        if structure_lines:
                            self.logger.error("\nFiles referenced in the Packmol input file:")
                            for line in structure_lines:
                                self.logger.error(f"  {line}")
                        
                        # Clear guidance
                        input_dir = os.path.dirname(os.path.abspath(args.input_file))
                        self.logger.error("\nTo fix this issue:")
                        self.logger.error(f"1. Make sure all PDB files are in the SAME directory as your input file: {input_dir}")
                        self.logger.error(f"   The input file ({os.path.basename(args.input_file)}) and PDB files should be in the same directory.")
                        self.logger.error("2. Check that the filenames in your input file match exactly with the actual PDB files")
                        
                        # List available PDB files
                        current_dir = os.getcwd()
                        pdb_files = [f for f in os.listdir(current_dir) if f.endswith('.pdb')]
                        if pdb_files:
                            self.logger.error(f"\nPDB files available in current directory:")
                            for pdb in pdb_files:
                                self.logger.error(f"  {pdb}")
                        else:
                            self.logger.error(f"\nNo PDB files found in current directory: {current_dir}")
                    
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