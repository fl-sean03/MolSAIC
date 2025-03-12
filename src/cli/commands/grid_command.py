"""
Grid replication command implementation.

This module provides the CLI command for generating grid replications of molecules.
"""

import argparse
import logging
from typing import Tuple

from molsaic.cli.base import BaseCommand, PipelineHelper
from molsaic import config
from molsaic.transformers import grid

class GridCommand(BaseCommand):
    """
    CLI command for generating grid replications of molecules.
    
    This command creates a 3D grid of replicated molecules from input CAR/MDF files.
    It supports both object-based and legacy file-based approaches.
    """
    
    name = "grid"
    help = "Generate a grid of replicated molecules"
    
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for the grid command.
        
        Args:
            parser (argparse.ArgumentParser): The parser to configure
        """
        parser.add_argument("--mdf", required=True, help="Input MDF file")
        parser.add_argument("--car", required=True, help="Input CAR file")
        parser.add_argument("--output-mdf", default="grid_box.mdf", help="Output MDF file")
        parser.add_argument("--output-car", default="grid_box.car", help="Output CAR file")
        parser.add_argument("--grid", type=int, default=config.DEFAULT_GRID_SIZE, 
                          help=f"Grid dimension along each axis (default: {config.DEFAULT_GRID_SIZE})")
        parser.add_argument("--gap", type=float, default=config.DEFAULT_GAP, 
                          help=f"Gap (in Angstroms) between molecules (default: {config.DEFAULT_GAP})")
        parser.add_argument("--base-name", default="MOL", 
                          help="Base molecule name for output molecules")
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the grid command with the given arguments.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        self.logger.info("Executing grid replication command...")
        grid_dims = (args.grid, args.grid, args.grid)
        
        # Create pipeline helper
        helper = PipelineHelper(args)
        
        # Check for file mode deprecation
        helper.check_file_mode_deprecation()
        
        # Validate debug_output option
        if args.debug_output and not helper.use_object_mode:
            self.logger.warning("Debug output is only available in object-based mode. Ignoring --debug-output.")
            args.debug_output = False
        
        try:
            if helper.use_object_mode:
                return self._execute_object_mode(args, helper, grid_dims)
            else:
                return self._execute_file_mode(args, grid_dims)
        except Exception as e:
            return self.handle_error(e, "Grid generation failed")
    
    def _execute_object_mode(self, args: argparse.Namespace, helper: PipelineHelper, 
                           grid_dims: Tuple[int, int, int]) -> int:
        """
        Execute the grid command using the object-based approach.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            helper (PipelineHelper): Helper for pipeline operations
            grid_dims (Tuple[int, int, int]): 3D grid dimensions
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        self.logger.info("Using object-based approach for grid replication")
        
        # Create and configure pipeline
        pipeline = helper.create_pipeline()
        
        # Load, transform, save
        helper.load_input_files(pipeline) \
               .generate_grid(grid_dims, args.gap) \
               .save(args.output_car, args.output_mdf, args.base_name)
        
        total_molecules = grid_dims[0] * grid_dims[1] * grid_dims[2]
        self.logger.info(f"Grid generation successful: {grid_dims[0]}x{grid_dims[1]}x{grid_dims[2]} = {total_molecules} molecules")
        
        return 0
    
    def _execute_file_mode(self, args: argparse.Namespace, grid_dims: Tuple[int, int, int]) -> int:
        """
        Execute the grid command using the legacy file-based approach.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            grid_dims (Tuple[int, int, int]): 3D grid dimensions
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        self.logger.info("Using legacy file-based approach for grid replication")
        
        grid.generate_grid_files(
            args.car, args.mdf, 
            args.output_car, args.output_mdf, 
            grid_dims, args.gap, args.base_name
        )
        
        total_molecules = grid_dims[0] * grid_dims[1] * grid_dims[2]
        self.logger.info(f"Grid generation successful: {grid_dims[0]}x{grid_dims[1]}x{grid_dims[2]} = {total_molecules} molecules")
        
        return 0

# Standalone entry point for direct execution
def main():
    """Entry point for directly running the grid command."""
    import sys
    from molsaic import config
    
    # Set up logging
    config.setup_logging()
    
    # Create parser
    parser = argparse.ArgumentParser(description="Grid Replication Tool")
    
    # Add command-specific arguments
    cmd = GridCommand()
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