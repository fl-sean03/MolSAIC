"""
Workspace utilities for CLI commands.

This module provides functions for creating and managing workspaces
for CLI commands.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional

from moltools import config

logger = logging.getLogger(__name__)

def setup_workspace() -> str:
    """
    Set up a workspace for the current session.
    
    Creates a workspace directory and initializes the global session workspace.
    
    Returns:
        str: Path to the created workspace
        
    Raises:
        PermissionError: If the current directory is not writable
        RuntimeError: If workspace creation fails
    """
    # Get the current directory
    current_dir = os.getcwd()
    logger.info(f"Current working directory: {current_dir}")
    
    # Check if the directory exists and is writable
    if not os.access(current_dir, os.W_OK):
        logger.error(f"Current directory is not writable: {current_dir}")
        raise PermissionError(f"Current directory is not writable: {current_dir}")
    
    # Create workspace directory if it doesn't exist yet
    workspace_dir = os.path.join(current_dir, ".moltools_workspace")
    logger.info(f"Creating workspace directory: {workspace_dir}")
    
    # Try to create the directory
    os.makedirs(workspace_dir, exist_ok=True)
    
    # Verify the directory was created
    if not os.path.exists(workspace_dir):
        logger.error(f"Failed to create workspace directory: {workspace_dir}")
        raise RuntimeError(f"Failed to create workspace directory: {workspace_dir}")
    
    # Explicitly set the workspace path
    os.environ['MOLTOOLS_WORKSPACE_PATH'] = workspace_dir
    
    # Create the workspace
    from moltools.workspace import create_global_workspace
    workspace_path = create_global_workspace("session_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    logger.debug(f"Created session workspace: {workspace_path}")
    logger.info(f"All logs will be saved to: {os.path.join(workspace_path, 'moltools.log')}")
    
    return workspace_path

def cleanup_session() -> None:
    """
    Clean up the session workspace if needed.
    
    Uses configuration settings to determine whether to keep or clean up
    the workspace. Also keeps the workspace if an error occurred.
    """
    if config.session_workspace:
        # Keep the workspace if requested with --keep or if there was an error
        should_keep = (
            getattr(config, 'keep_session_workspace', False) or 
            sys.exc_info()[0] is not None
        )
        
        if should_keep:
            if sys.exc_info()[0] is not None:
                logger.info(f"Keeping session workspace due to error. Logs available at: {config.session_workspace.current_workspace}")
            else:
                if config.keep_all_workspaces:
                    logger.info(f"Keeping all workspaces and logs (--keep). Session workspace: {config.session_workspace.current_workspace}")
                else:
                    logger.info(f"Keeping logs only (--keep-logs). Session workspace: {config.session_workspace.current_workspace}")
        else:
            # Clean up the session workspace
            logger.debug(f"Cleaning up session workspace: {config.session_workspace.current_workspace}")
            config.session_workspace.close(cleanup=True)