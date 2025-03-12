"""
Force-field update command implementation.

This module provides the CLI command for updating force-field types based on a mapping.
"""

import argparse
import logging
from typing import Dict, Any

from molsaic.cli.base import BaseCommand, PipelineHelper
from molsaic import config
from molsaic.transformers import update_ff

class UpdateFFCommand(BaseCommand):
    """
    CLI command for updating force-field types in molecular files.
    
    This command updates force-field types in CAR/MDF files based on a charge-element
    to force-field type mapping file (JSON).
    """
    
    name = "update-ff"
    help = "Update force-field types based on a mapping"
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for the update-ff command.
        
        Args:
            parser (argparse.ArgumentParser): The parser to configure
        """
        parser.add_argument("--mdf", help="Input MDF file")
        parser.add_argument("--car", help="Input CAR file")
        parser.add_argument("--output-mdf", help="Output MDF file")
        parser.add_argument("--output-car", help="Output CAR file")
        parser.add_argument("--mapping", required=True, help="JSON mapping file")
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the update-ff command with the given arguments.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        self.logger.info("Executing force-field update command...")
        
        # Create pipeline helper
        helper = PipelineHelper(args)
        
        # Check for file mode deprecation
        helper.check_file_mode_deprecation()
        
        # Validate debug_output option
        if args.debug_output and not helper.use_object_mode:
            self.logger.warning("Debug output is only available in object-based mode. Ignoring --debug-output.")
            args.debug_output = False
        
        try:
            # Validate arguments based on mode
            self._validate_args(args, helper.use_object_mode)
            
            if helper.use_object_mode:
                return self._execute_object_mode(args, helper)
            else:
                return self._execute_file_mode(args)
        except Exception as e:
            return self.handle_error(e, "Force-field update failed")
    
    def _validate_args(self, args: argparse.Namespace, use_object_mode: bool) -> None:
        """
        Validate command arguments based on processing mode.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            use_object_mode (bool): Whether using object-based mode
            
        Raises:
            ValueError: If validation fails
        """
        if use_object_mode:
            # Object-based approach validation
            if not (args.mdf and args.car):
                raise ValueError("Both --mdf and --car are required when using object-based mode")
            if not (args.output_mdf or args.output_car):
                raise ValueError("At least one of --output-mdf or --output-car must be provided")
        else:
            # File-based approach validation
            if not (args.mdf or args.car):
                raise ValueError("At least one of --mdf or --car must be provided")
            if args.mdf and not args.output_mdf:
                raise ValueError("--output-mdf is required when --mdf is provided")
            if args.car and not args.output_car:
                raise ValueError("--output-car is required when --car is provided")
    
    def _execute_object_mode(self, args: argparse.Namespace, helper: PipelineHelper) -> int:
        """
        Execute the update-ff command using the object-based approach.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            helper (PipelineHelper): Helper for pipeline operations
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        self.logger.info("Using object-based approach for force-field update")
        
        # Create and configure pipeline
        pipeline = helper.create_pipeline()
        
        # Load, transform, save
        helper.load_input_files(pipeline) \
               .update_ff_types(args.mapping) \
               .save(args.output_car, args.output_mdf)
        
        self.logger.info("Force-field types updated successfully")
        return 0
    
    def _execute_file_mode(self, args: argparse.Namespace) -> int:
        """
        Execute the update-ff command using the legacy file-based approach.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        self.logger.info("Using legacy file-based approach for force-field update")
        
        results = update_ff.update_ff_types(
            car_file=args.car,
            mdf_file=args.mdf,
            output_car=args.output_car,
            output_mdf=args.output_mdf,
            mapping_file=args.mapping
        )
        
        if 'car_updates' in results:
            self.logger.info(f"Updated {results['car_updates']} atoms in CAR file: {args.output_car}")
        if 'mdf_updates' in results:
            self.logger.info(f"Updated {results['mdf_updates']} atoms in MDF file: {args.output_mdf}")
            
        return 0

# Standalone entry point for direct execution
def main():
    """Entry point for directly running the update-ff command."""
    import sys
    from molsaic import config
    
    # Set up logging
    config.setup_logging()
    
    # Create parser
    parser = argparse.ArgumentParser(description="Force-field Type Update Tool")
    
    # Add command-specific arguments
    cmd = UpdateFFCommand()
    cmd.configure_parser(parser)
    
    # Add global options
    parser.add_argument("--log-level", 
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      default=config.DEFAULT_LOG_LEVEL,
                      help="Set logging level")
    parser.add_argument("--file-mode", action="store_true", 
                      help="[DEPRECATED] Use legacy file-based approach instead of object-based pipeline")
    parser.add_argument("--debug-output", action="store_true",
                      help="Generate intermediate files for debugging (only available in object-based mode)")
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