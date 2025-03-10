"""
Workspace management for MolSAIC.

This module provides the WorkspaceManager class for creating and managing
temporary directories for tool execution and file processing.
"""

import os
import uuid
import shutil
import fnmatch
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple, Set

from . import config

logger = logging.getLogger(__name__)

class WorkspaceManager:
    """
    Manages temporary workspace directories for MolSAIC operations.
    
    This class provides functionality for creating, tracking, and cleaning up
    temporary directories. It supports retention policies and file tracking.
    
    Attributes:
        base_path (str): Base directory for workspaces
        current_workspace (str): Path to the current active workspace
        tracked_files (set): Set of files created in the workspace
        retention_hours (int): How long to keep workspaces (0 = forever)
    """
    
    def __init__(self, base_path: Optional[str] = None, 
                 retention_hours: Optional[int] = None,
                 prefix: str = "molsaic_"):
        """
        Initialize a WorkspaceManager.
        
        Args:
            base_path (str, optional): Base directory for workspaces. Default uses config.
            retention_hours (int, optional): Retention policy in hours. Default uses config.
            prefix (str, optional): Prefix for workspace directories. Default is "molsaic_".
        """
        self.base_path = base_path or config.DEFAULT_WORKSPACE_PATH
        self.retention_hours = retention_hours if retention_hours is not None else config.WORKSPACE_RETENTION
        self.prefix = prefix
        self.current_workspace = None
        self.tracked_files = set()
        
        # Try to create the base directory if it doesn't exist
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path, exist_ok=True)
                logger.debug(f"Created workspace base directory: {self.base_path}")
            except OSError as e:
                # Always use current directory - never fall back to temp
                self.base_path = os.path.join(".", ".molsaic_workspace")
                try:
                    os.makedirs(self.base_path, exist_ok=True)
                    logger.warning(f"Created workspace in current directory: {self.base_path}")
                except OSError as e2:
                    # If we can't create the directory, log the error but don't change the path
                    # This will allow the error to propagate and be handled by the CLI
                    logger.error(f"Failed to create workspace directory: {str(e2)}")
    
    def create_workspace(self, name: Optional[str] = None) -> str:
        """
        Create a new workspace directory.
        
        Args:
            name (str, optional): Name for the workspace. Default generates a unique name.
            
        Returns:
            str: Path to the created workspace
            
        Raises:
            OSError: If workspace creation fails
        """
        # Generate a unique name if not provided
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            name = f"{timestamp}_{unique_id}"
        
        # Create full workspace path
        workspace_path = os.path.join(self.base_path, f"{self.prefix}{name}")
        
        # Create the directory
        try:
            os.makedirs(workspace_path, exist_ok=True)
            logger.debug(f"Created workspace: {workspace_path}")
        except OSError as e:
            logger.error(f"Failed to create workspace: {str(e)}")
            raise
        
        # Set as current workspace
        self.current_workspace = workspace_path
        self.tracked_files = set()
        
        # Set up file logging in this workspace
        self._setup_workspace_logging(workspace_path)
        
        return workspace_path
        
    def _setup_workspace_logging(self, workspace_path: str) -> None:
        """
        Set up logging to a file in the workspace.
        
        This flushes all logs from the memory handler to a file
        and sets up a FileHandler for future logs.
        
        Args:
            workspace_path (str): Path to the workspace directory
        """
        # Create log file path
        log_file = os.path.join(workspace_path, "molsaic.log")
        
        # First, flush all memory-captured logs to our file
        try:
            config.flush_logs_to_file(log_file)
            
            # Create a file handler for future logs
            root_logger = logging.getLogger()
            
            # Create a formatter that includes all information
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Create and configure file handler
            file_handler = logging.FileHandler(log_file, mode='a')  # Append mode
            file_handler.setFormatter(formatter)
            # Set to DEBUG level to capture everything
            file_handler.setLevel(logging.DEBUG)
            
            # Save the handler for later removal
            self._file_handler = file_handler
            
            # Add the handler to the root logger
            root_logger.addHandler(file_handler)
            
            logger.debug(f"Set up logging to file: {log_file}")
        except Exception as e:
            logger.warning(f"Failed to set up workspace logging: {str(e)}")
    
    def track_file(self, file_path: str) -> None:
        """
        Track a file created in the workspace.
        
        Args:
            file_path (str): Path to the file to track
        """
        self.tracked_files.add(os.path.abspath(file_path))
    
    def track_files(self, file_paths: List[str]) -> None:
        """
        Track multiple files created in the workspace.
        
        Args:
            file_paths (list): List of file paths to track
        """
        for file_path in file_paths:
            self.track_file(file_path)
    
    def get_tracked_files(self, pattern: Optional[str] = None) -> List[str]:
        """
        Get tracked files, optionally filtered by pattern.
        
        Args:
            pattern (str, optional): Glob pattern to filter files. Default is None (all files).
            
        Returns:
            list: List of matching tracked file paths
        """
        if pattern is None:
            return list(self.tracked_files)
        
        return [f for f in self.tracked_files if fnmatch.fnmatch(os.path.basename(f), pattern)]
    
    def cleanup_current(self, keep_patterns: Optional[List[str]] = None) -> None:
        """
        Clean up the current workspace, keeping files matching patterns.
        
        Args:
            keep_patterns (list, optional): Glob patterns for files to keep. Default preserves
                                           output files from config.PRESERVE_FILE_PATTERNS.
        """
        if self.current_workspace is None or not os.path.exists(self.current_workspace):
            logger.warning("No current workspace to clean up")
            return
        
        if keep_patterns is None:
            keep_patterns = config.PRESERVE_FILE_PATTERNS
        
        logger.debug(f"Cleaning up workspace: {self.current_workspace}")
        
        # Get all files in the workspace
        all_files = []
        for root, _, files in os.walk(self.current_workspace):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        # Determine files to keep
        files_to_keep = set()
        for pattern in keep_patterns:
            for file in all_files:
                if fnmatch.fnmatch(os.path.basename(file), pattern):
                    files_to_keep.add(file)
        
        # Remove files not in keep list
        for file in all_files:
            if file not in files_to_keep:
                try:
                    os.unlink(file)
                    logger.debug(f"Deleted: {file}")
                except OSError as e:
                    logger.warning(f"Failed to delete {file}: {str(e)}")
    
    def cleanup_old_workspaces(self) -> int:
        """
        Clean up workspaces older than the retention policy.
        
        Returns:
            int: Number of workspaces cleaned up
        """
        if self.retention_hours <= 0:
            logger.debug("Workspace retention policy is set to keep forever")
            return 0
        
        if not os.path.exists(self.base_path):
            logger.warning(f"Workspace base path does not exist: {self.base_path}")
            return 0
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # Get all workspace directories
        count = 0
        for item in os.listdir(self.base_path):
            if not item.startswith(self.prefix):
                continue
                
            item_path = os.path.join(self.base_path, item)
            if not os.path.isdir(item_path):
                continue
                
            # Skip current workspace
            if self.current_workspace and os.path.samefile(item_path, self.current_workspace):
                continue
                
            # Check modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(item_path))
            if mod_time < cutoff_time:
                try:
                    shutil.rmtree(item_path)
                    logger.debug(f"Removed old workspace: {item_path} (last modified: {mod_time})")
                    count += 1
                except OSError as e:
                    logger.warning(f"Failed to remove workspace {item_path}: {str(e)}")
        
        if count > 0:
            logger.info(f"Cleaned up {count} old workspaces (older than {self.retention_hours} hours)")
        
        return count
    
    def get_workspace_path(self, filename: Optional[str] = None) -> str:
        """
        Get the path to the current workspace, optionally with a filename appended.
        
        Args:
            filename (str, optional): Filename to append to the workspace path.
            
        Returns:
            str: Path to the workspace or file in workspace
            
        Raises:
            ValueError: If no current workspace exists
        """
        if self.current_workspace is None:
            raise ValueError("No active workspace. Call create_workspace() first.")
            
        if filename:
            return os.path.join(self.current_workspace, filename)
        return self.current_workspace
    
    def close(self, cleanup: bool = True, keep_patterns: Optional[List[str]] = None) -> None:
        """
        Close the workspace manager.
        
        Args:
            cleanup (bool, optional): Whether to clean up temporary files. Default is True.
            keep_patterns (list, optional): Glob patterns for files to keep. Default None.
        """
        # Remove the file handler if it exists
        try:
            if hasattr(self, '_file_handler'):
                # Get the root logger
                root_logger = logging.getLogger()
                # Remove our file handler
                root_logger.removeHandler(self._file_handler)
                # Close the file handler
                self._file_handler.close()
                delattr(self, '_file_handler')
        except Exception as e:
            logger.warning(f"Error removing log file handler: {str(e)}")
        
        if cleanup and self.current_workspace:
            self.cleanup_current(keep_patterns=keep_patterns)
            
        self.current_workspace = None
        self.tracked_files = set()
    
    def __enter__(self) -> 'WorkspaceManager':
        """
        Context manager entry.
        
        Returns:
            WorkspaceManager: Self reference
        """
        if not self.current_workspace:
            self.create_workspace()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit.
        
        Cleans up the workspace unless an exception occurred.
        """
        # Only clean up on normal exit (no exception)
        self.close(cleanup=(exc_type is None))


# Function to create a global workspace
def create_global_workspace(name: Optional[str] = None) -> str:
    """
    Create a global workspace that can be used by any part of the code.
    
    Args:
        name (str, optional): Name for the workspace. Default generates a unique name.
        
    Returns:
        str: Path to the created workspace
    """
    wm = WorkspaceManager()
    workspace_path = wm.create_workspace(name)
    
    # Store the workspace manager in config for later access
    config.session_workspace = wm
    
    return workspace_path