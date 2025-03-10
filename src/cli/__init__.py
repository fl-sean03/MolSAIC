"""
Command-line interface for MolTools.

This module provides the main entry point for the command-line interface,
which dispatches to the appropriate command handler based on the subcommand.
"""

import argparse
import logging
import sys
from typing import Dict, List, Type, Optional

from moltools import config
from moltools.cli.base import BaseCommand
from moltools.cli.commands import get_commands
from moltools.cli.utils.workspace import setup_workspace, cleanup_session

logger = logging.getLogger(__name__)

def create_parser() -> argparse.ArgumentParser:
    """
    Create the main argument parser with all subcommands.
    
    Returns:
        argparse.ArgumentParser: The configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="MolTools - Molecular Data Processing Tools",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    # Global options
    parser.add_argument("--log-level", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default=config.DEFAULT_LOG_LEVEL,
                        help="Set logging level")
    
    # Add global options for all subcommands
    parser.add_argument("--file-mode", action="store_true", 
                      help="[DEPRECATED] Use legacy file-based approach instead of object-based pipeline")
    parser.add_argument("--debug-output", action="store_true",
                      help="Generate intermediate files for debugging (only available in object-based mode)")
    parser.add_argument("--debug-prefix", default="debug_",
                      help="Prefix for debug output files (only with --debug-output)")
    
    # Split into two separate flags for clarity
    keep_group = parser.add_mutually_exclusive_group()
    keep_group.add_argument("--keep", action="store_true",
                      help="Keep all artifacts after completion (logs and workspaces)")
    keep_group.add_argument("--keep-logs", action="store_true",
                      help="Keep only logs after completion (cleanup workspaces)")
    
    # Subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    
    # Register all available commands
    commands = get_commands()
    for cmd_name, cmd_class in commands.items():
        cmd_instance = cmd_class()
        cmd_parser = subparsers.add_parser(cmd_name, help=cmd_instance.help)
        cmd_instance.configure_parser(cmd_parser)
    
    return parser

def main() -> int:
    """
    Main entry point for the CLI.
    
    Parses arguments, sets up logging and workspace, and dispatches to
    the appropriate command handler.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Set up logging right away to capture all logs
    config.setup_logging()
    
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Update logging with the user-specified level
    config.setup_logging(args.log_level)
    
    # Create a new workspace for this session
    try:
        setup_workspace()
    except Exception as e:
        logger.error(f"Failed to set up workspace: {str(e)}")
        return 1
    
    # Set flags based on the keep options
    if args.keep:
        # Keep everything
        config.keep_session_workspace = True
        config.keep_all_workspaces = True
    elif args.keep_logs:
        # Keep only logs
        config.keep_session_workspace = True
        config.keep_all_workspaces = False
    else:
        # Keep nothing
        config.keep_session_workspace = False
        config.keep_all_workspaces = False
    
    # Check for file mode deprecation
    if args.file_mode and config.FILE_MODE_DEPRECATED:
        config.show_file_mode_deprecation_warning(logger)
    
    # Execute the requested command if specified
    if not args.command:
        parser.print_help()
        return 1
    
    # Get the command and execute it
    commands = get_commands()
    cmd_class = commands[args.command]
    cmd_instance = cmd_class()
    
    try:
        return cmd_instance.execute(args)
    except Exception as e:
        logger.error(f"Command execution failed: {str(e)}")
        # Keep workspace on error
        config.keep_session_workspace = True
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
    finally:
        cleanup_session()
    
    sys.exit(exit_code)