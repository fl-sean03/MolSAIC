"""
Base class and utilities for CLI commands.

This module provides the foundation for implementing CLI commands in a modular way.
All commands should inherit from the BaseCommand class and implement its abstract methods.
"""

import argparse
import logging
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