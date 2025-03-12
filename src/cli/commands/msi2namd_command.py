"""
MSI2NAMD conversion command implementation.

This module provides the CLI command for converting files to NAMD format (PDB/PSF).
"""

import argparse
import logging
import os
from typing import Dict, Any

from molsaic.cli.base import BaseCommand, PipelineHelper
from molsaic import config
from molsaic.external_tools import MSI2NAMDTool

class MSI2NAMDCommand(BaseCommand):
    """
    CLI command for converting Material Studio files to NAMD format.
    
    This command converts Material Studio files (CAR/MDF) to NAMD format (PDB/PSF)
    using the MSI2NAMD external tool integration.
    """
    
    name = "msi2namd"
    help = "Convert files to NAMD format (PDB/PSF) using MSI2NAMD"
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for the msi2namd command.
        
        Args:
            parser (argparse.ArgumentParser): The parser to configure
        """
        parser.add_argument("--mdf", required=True, help="Input MDF file")
        parser.add_argument("--car", required=True, help="Input CAR file")
        parser.add_argument("--output-dir", default="namd_output", 
                         help="Output directory for NAMD files (default: namd_output)")
        parser.add_argument("--residue-name", help="Residue name for NAMD files (max 4 characters)")
        parser.add_argument("--parameter-file", required=True, 
                         help="Parameter file for MSI2NAMD conversion (REQUIRED)")
        parser.add_argument("--charge-groups", action="store_true", 
                         help="Include charge groups in conversion (-cg flag)")
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the msi2namd command with the given arguments.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        self.logger.info("Executing MSI2NAMD conversion command...")
        
        # MSI2NAMD conversion is only available in object mode
        if getattr(args, 'file_mode', False):
            self.logger.error("MSI2NAMD conversion is only available in object-based mode")
            return 1
            
        try:
            # Get base output directory name and handle enumeration if it exists
            output_dir = self.setup_output_directory(args.output_dir)
            
            # Update the argument with the resolved output directory path
            args.output_dir = output_dir
            self.logger.debug(f"Using MSI2NAMD output directory: {output_dir}")
            
            # Create pipeline helper
            helper = PipelineHelper(args)
            
            # Create pipeline
            pipeline = helper.create_pipeline()
            
            # Load system
            helper.load_input_files(pipeline)
            
            # Convert to NAMD - respect global keep flags
            cleanup_workspace = not config.keep_all_workspaces
            
            # Use the msi2namd method
            pipeline.msi2namd(
                output_dir=args.output_dir,
                residue_name=args.residue_name,
                parameter_file=args.parameter_file,
                charge_groups=args.charge_groups,
                cleanup_workspace=cleanup_workspace
            )
            
            # Report result files
            for key, file_path in pipeline.namd_files.items():
                if file_path and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path) / 1024  # Size in KB
                    self.logger.info(f"Generated {key}: {os.path.basename(file_path)} ({file_size:.1f} KB)")
            
            self.logger.info(f"MSI2NAMD conversion successful. Output files in: {args.output_dir}")
            
            return 0
        except Exception as e:
            return self.handle_error(e, "MSI2NAMD conversion failed")
        
    def _add_backward_compatibility(self, parser: argparse.ArgumentParser) -> None:
        """
        Add backward compatibility for the deprecated convert-to-namd command.
        
        Args:
            parser (argparse.ArgumentParser): The parser to configure
        """
        # This is a potential extension point for deprecation warnings and help text
        pass

# Standalone entry point for direct execution
def main():
    """Entry point for directly running the msi2namd command."""
    import sys
    from molsaic import config
    
    # Set up logging
    config.setup_logging()
    
    # Create parser
    parser = argparse.ArgumentParser(description="MSI2NAMD Conversion Tool")
    
    # Add command-specific arguments
    cmd = MSI2NAMDCommand()
    cmd.configure_parser(parser)
    
    # Add global options
    parser.add_argument("--log-level", 
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      default=config.DEFAULT_LOG_LEVEL,
                      help="Set logging level")
    
    # MSI2NAMD doesn't support file mode, but add other global options
    parser.add_argument("--debug-output", action="store_true",
                      help="Generate intermediate files for debugging")
    parser.add_argument("--debug-prefix", default="debug_",
                      help="Prefix for debug output files (only with --debug-output)")
    
    # Add keep options
    keep_group = parser.add_mutually_exclusive_group()
    keep_group.add_argument("--keep", action="store_true",
                      help="Keep all artifacts after completion (logs and workspaces)")
    keep_group.add_argument("--keep-logs", action="store_true",
                      help="Keep only logs after completion (cleanup workspaces)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Update logging with the user-specified level
    config.setup_logging(args.log_level)
    
    # Create a new workspace for this session
    try:
        from molsaic.cli.utils.workspace import setup_workspace
        setup_workspace()
    except Exception as e:
        print(f"Failed to set up workspace: {str(e)}")
        return 1
    
    try:
        # Execute command
        return cmd.execute(args)
    finally:
        # Clean up
        from molsaic.cli.utils.workspace import cleanup_session
        cleanup_session()

if __name__ == "__main__":
    import sys
    sys.exit(main())