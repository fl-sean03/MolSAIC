"""
Base class and utilities for CLI commands.

This module provides the foundation for implementing CLI commands in a modular way.
All commands should inherit from the BaseCommand class and implement its abstract methods.
"""

import argparse
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from molsaic import config

class BaseCommand(ABC):
    """
    Base class for all CLI commands.
    
    All commands should inherit from this class and implement:
    - configure_parser: to set up command-specific arguments
    - execute: to implement the command logic
    
    Attributes:
        name (str): The name of the command used in CLI
        help (str): A brief description of the command for the help message
    """
    
    name = None  # Command name (required in subclasses)
    help = None  # Command help text (required in subclasses)
    
    def __init__(self):
        """Initialize the command with a logger."""
        if not self.name:
            raise ValueError(f"Command {self.__class__.__name__} must define a name attribute")
        if not self.help:
            raise ValueError(f"Command {self.__class__.__name__} must define a help attribute")
            
        self.logger = logging.getLogger(f"molsaic.cli.{self.name}")
    
    @abstractmethod
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            parser (argparse.ArgumentParser): The parser to configure
        """
        pass
    
    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the command with the given arguments.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        pass
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """
        Validate command arguments.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
            
        Returns:
            bool: True if arguments are valid, False otherwise
        """
        return True
        
    def setup_output_directory(self, base_dir: str) -> str:
        """
        Set up an output directory with automatic enumeration if it exists.
        
        Args:
            base_dir (str): Base output directory name
            
        Returns:
            str: Path to the created output directory
            
        Raises:
            ValueError: If directory creation fails
        """
        # Ensure absolute path
        if not os.path.isabs(base_dir):
            base_dir = os.path.abspath(base_dir)
        
        # If the directory exists, enumerate it (example_1, example_2, etc.)
        output_dir = base_dir
        counter = 1
        while os.path.exists(output_dir):
            output_dir = f"{base_dir}_{counter}"
            counter += 1
        
        try:
            # Create directory
            os.makedirs(output_dir, exist_ok=True)
            self.logger.info(f"Using output directory: {output_dir}")
            return output_dir
        except Exception as e:
            error_msg = f"Failed to create output directory '{output_dir}': {str(e)}"
            self.logger.error(error_msg)
            self.logger.error("Please check directory permissions or provide a different output directory")
            raise ValueError(error_msg)
    
    def copy_output_file(self, source_file: str, output_dir: str, suffix: str = None) -> str:
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
            self.logger.info(f"Copied output file to: {dest_path}")
            return dest_path
        except Exception as copy_err:
            self.logger.warning(f"Could not copy output file: {str(copy_err)}")
            return None
    
    def handle_error(self, error: Exception, error_prefix: str = "Command execution failed") -> int:
        """
        Handle errors consistently across all commands.
        
        Args:
            error (Exception): The exception that occurred
            error_prefix (str): Prefix for the error message
            
        Returns:
            int: Exit code (always 1 for failure)
        """
        error_msg = f"{error_prefix}: {str(error)}"
        self.logger.error(error_msg)
        
        # Add more detailed troubleshooting info based on error type
        if isinstance(error, FileNotFoundError):
            self.logger.error("A required file was not found. Check file paths and permissions.")
        elif isinstance(error, PermissionError):
            self.logger.error("Permission denied. Check if you have necessary permissions.")
        elif isinstance(error, ValueError):
            self.logger.error("Invalid input or configuration. Please check arguments.")
        
        # Keep workspace on error for debugging
        import molsaic.config as cfg
        cfg.keep_session_workspace = True
        
        if hasattr(cfg, 'session_workspace') and cfg.session_workspace:
            self.logger.info(f"Logs available in workspace: {cfg.session_workspace.current_workspace}")
        
        return 1

class PipelineHelper:
    """
    Helper class for working with MolecularPipeline.
    
    This class provides a simplified interface for creating and configuring
    a MolecularPipeline instance based on command-line arguments.
    """
    
    def __init__(self, args):
        """
        Initialize with command-line arguments.
        
        Args:
            args (argparse.Namespace): The parsed command-line arguments
        """
        self.args = args
        self.logger = logging.getLogger("molsaic.cli.pipeline")
        self.use_object_mode = not getattr(args, 'file_mode', False)
        self.debug = getattr(args, 'debug_output', False)
        self.debug_prefix = getattr(args, 'debug_prefix', 'debug_')
        self.keep_workspaces = getattr(args, 'keep', False)
    
    def create_pipeline(self):
        """
        Create and configure a MolecularPipeline instance.
        
        Returns:
            MolecularPipeline: A configured pipeline instance
        """
        from molsaic.pipeline import MolecularPipeline
        
        # Set configuration based on CLI args
        config.keep_all_workspaces = self.args.keep
        config.keep_session_workspace = self.args.keep or getattr(self.args, 'keep_logs', False)
        
        # Create pipeline
        pipeline = MolecularPipeline(
            debug=self.debug,
            debug_prefix=self.debug_prefix,
            keep_workspace=config.keep_all_workspaces
        )
        
        return pipeline
        
    def load_input_files(self, pipeline):
        """
        Load input files into the pipeline.
        
        Args:
            pipeline (MolecularPipeline): The pipeline to load into
            
        Returns:
            MolecularPipeline: The pipeline with loaded files
            
        Raises:
            ValueError: If required input files are missing
        """
        if not hasattr(self.args, 'car') or not hasattr(self.args, 'mdf'):
            raise ValueError("Input files not specified in arguments")
            
        if not self.args.car or not self.args.mdf:
            raise ValueError("Both CAR and MDF files are required in object mode")
            
        return pipeline.load(self.args.car, self.args.mdf)
        
    def save_output_files(self, pipeline):
        """
        Save output files from the pipeline.
        
        Args:
            pipeline (MolecularPipeline): The pipeline to save from
            
        Returns:
            MolecularPipeline: The pipeline after saving
            
        Raises:
            ValueError: If required output files are not specified
        """
        car_file = getattr(self.args, 'output_car', None)
        mdf_file = getattr(self.args, 'output_mdf', None)
        base_name = getattr(self.args, 'base_name', 'MOL')
        
        if not car_file and not mdf_file:
            raise ValueError("At least one output file must be specified")
            
        return pipeline.save(car_file, mdf_file, base_name)
        
    def check_file_mode_deprecation(self):
        """
        Check if file mode is being used and show deprecation warning if needed.
        """
        if not self.use_object_mode and config.FILE_MODE_DEPRECATED:
            config.show_file_mode_deprecation_warning(self.logger)

    def validate_file_mode(self):
        """
        Validate arguments based on the processing mode (object vs file).
        
        Returns:
            bool: True if validation passes
            
        Raises:
            ValueError: If validation fails with detailed message
        """
        if self.use_object_mode:
            # Object mode requires both input files
            if not (self.args.mdf and self.args.car):
                raise ValueError("Both --mdf and --car are required when using object-based mode")
                
            # Object mode requires at least one output file
            if hasattr(self.args, 'output_mdf') or hasattr(self.args, 'output_car'):
                if not (getattr(self.args, 'output_mdf', None) or getattr(self.args, 'output_car', None)):
                    raise ValueError("At least one of --output-mdf or --output-car must be provided")
        else:
            # File mode requires at least one input file
            if hasattr(self.args, 'mdf') and hasattr(self.args, 'car'):
                if not (self.args.mdf or self.args.car):
                    raise ValueError("At least one of --mdf or --car must be provided")
                
            # File mode requires matching output for each input
            if hasattr(self.args, 'mdf') and self.args.mdf and not getattr(self.args, 'output_mdf', None):
                raise ValueError("--output-mdf is required when --mdf is provided in file mode")
                
            if hasattr(self.args, 'car') and self.args.car and not getattr(self.args, 'output_car', None):
                raise ValueError("--output-car is required when --car is provided in file mode")
                
        return True