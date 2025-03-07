"""
Base class for external tool integration.

This module provides the BaseExternalTool abstract class which serves as the
foundation for all external tool integrations.
"""

import os
import abc
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple

from ..workspace import WorkspaceManager
from .utils import find_executable, run_process, copy_files
from . import config

logger = logging.getLogger(__name__)

class BaseExternalTool(abc.ABC):
    """
    Abstract base class for external tool integration.
    
    This class defines the standard interface for external tool integrations
    and provides common functionality for executable resolution, workspace
    management, and process execution.
    
    Attributes:
        name (str): Name of the external tool
        executable_path (str): Path to the tool executable
        workspace_manager (WorkspaceManager): Workspace manager instance
        default_timeout (int): Default timeout for tool execution in seconds
    """
    
    def __init__(self, 
                 executable_path: Optional[str] = None,
                 workspace_manager: Optional[WorkspaceManager] = None,
                 timeout: Optional[int] = None):
        """
        Initialize a new external tool integration.
        
        Args:
            executable_path (str, optional): Path to the executable. If None, will search PATH.
            workspace_manager (WorkspaceManager, optional): Workspace manager to use.
                                                         If None, a new one will be created.
            timeout (int, optional): Default timeout for tool execution in seconds.
        
        Raises:
            ValueError: If the executable cannot be found
        """
        self.name = self._get_tool_name()
        
        # First try to use the session workspace if available
        from .. import config as main_config
        if not workspace_manager and hasattr(main_config, 'session_workspace') and main_config.session_workspace:
            self.workspace_manager = main_config.session_workspace
        else:
            # Fall back to provided workspace_manager or create a new one
            self.workspace_manager = workspace_manager or WorkspaceManager()
            
        self.default_timeout = timeout or config.DEFAULT_PROCESS_TIMEOUT
        
        # Find the executable
        if executable_path:
            # Use provided path if it exists and is executable
            if os.path.isfile(executable_path) and os.access(executable_path, os.X_OK):
                self.executable_path = executable_path
            else:
                raise ValueError(f"Executable not found or not executable: {executable_path}")
        else:
            # Try to find the executable in PATH
            self.executable_path = find_executable(self.name)
            if not self.executable_path:
                raise ValueError(f"Could not find executable for tool: {self.name}")
        
        logger.debug(f"Initialized {self.name} tool with executable: {self.executable_path}")
    
    @abc.abstractmethod
    def _get_tool_name(self) -> str:
        """
        Get the name of the tool.
        
        This method should be implemented by subclasses to return the name of the tool.
        The name is used for executable resolution and logging.
        
        Returns:
            str: Name of the tool
        """
        pass
    
    @abc.abstractmethod
    def validate_inputs(self, **kwargs) -> None:
        """
        Validate input parameters before execution.
        
        This method should be implemented by subclasses to validate any
        input parameters before tool execution.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Raises:
            ValueError: If inputs are invalid
        """
        pass
    
    @abc.abstractmethod
    def prepare_inputs(self, workspace_path: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare input files in the workspace.
        
        This method should be implemented by subclasses to create any
        necessary input files in the workspace directory.
        
        Args:
            workspace_path (str): Path to the workspace directory
            **kwargs: Tool-specific parameters
            
        Returns:
            dict: Information about prepared inputs, such as file paths
            
        Raises:
            ValueError: If input preparation fails
        """
        pass
    
    @abc.abstractmethod
    def build_command(self, input_info: Dict[str, Any], **kwargs) -> List[str]:
        """
        Build the command to be executed.
        
        This method should be implemented by subclasses to build the command
        list for the specific tool using the prepared inputs.
        
        Args:
            input_info (dict): Information from prepare_inputs
            **kwargs: Tool-specific parameters
            
        Returns:
            list: Command list to be executed
        """
        pass
    
    @abc.abstractmethod
    def process_output(self, return_code: int, stdout: str, stderr: str, 
                      input_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Process the tool's output.
        
        This method should be implemented by subclasses to process the
        output of the tool execution and extract relevant information.
        
        Args:
            return_code (int): Process return code
            stdout (str): Process standard output
            stderr (str): Process standard error
            input_info (dict): Information from prepare_inputs
            **kwargs: Tool-specific parameters
            
        Returns:
            dict: Processed output information
            
        Raises:
            RuntimeError: If the tool execution failed
        """
        pass
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the external tool.
        
        This method orchestrates the full tool execution workflow:
        1. Create/prepare workspace
        2. Validate inputs
        3. Prepare input files
        4. Build and execute command
        5. Process output
        6. Clean up (if requested)
        
        Args:
            **kwargs: Tool-specific parameters and options including:
                - timeout (int): Timeout in seconds
                - cleanup (bool): Whether to clean up workspace after execution
                - keep_patterns (list): Glob patterns for files to keep during cleanup
                - output_dir (str): Directory to copy output files to
                
        Returns:
            dict: Tool execution results
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If tool execution failed
            OSError: If workspace or file operations fail
        """
        # Extract common options
        timeout = kwargs.pop('timeout', self.default_timeout)
        cleanup = kwargs.pop('cleanup', True)
        keep_patterns = kwargs.pop('keep_patterns', None)
        output_dir = kwargs.pop('output_dir', None)
        
        # Use the workspace_manager's current workspace if it exists
        if not self.workspace_manager.current_workspace:
            self.workspace_manager.create_workspace()
        
        # Create a tool-specific subdirectory in the workspace
        import os
        # Use the tool name to create a consistent subdirectory name
        tool_dir_name = self.name.lower().replace('-', '_').replace(' ', '_')
        tool_dir = os.path.join(self.workspace_manager.current_workspace, tool_dir_name)
        os.makedirs(tool_dir, exist_ok=True)
        
        workspace_path = tool_dir
        logger.info(f"Executing {self.name} in workspace: {workspace_path}")
        
        try:
            # Validate inputs
            self.validate_inputs(**kwargs)
            
            # Prepare input files
            input_info = self.prepare_inputs(workspace_path, **kwargs)
            
            # Build command
            cmd = self.build_command(input_info, **kwargs)
            
            # Execute command
            logger.info(f"Running command: {' '.join(cmd)}")
            logger.info(f"Working directory: {workspace_path}")
            
            # List files in workspace for debugging
            files_in_workspace = os.listdir(workspace_path)
            logger.info(f"Files in workspace: {', '.join(files_in_workspace)}")
            
            # Execute the command
            return_code, stdout, stderr = run_process(
                cmd=cmd,
                cwd=workspace_path,
                timeout=timeout,
                capture_output=True
            )
            
            # Log files are now automatically created by run_process
            logger.info(f"Process execution completed with return code {return_code}")
            
            # If there was an error, log more details
            if return_code != 0:
                logger.error(f"Command failed with return code {return_code}")
                if stdout.strip():
                    logger.error(f"STDOUT: {stdout.strip()}")
                if stderr.strip():
                    logger.error(f"STDERR: {stderr.strip()}")
            
            # Process output
            result = self.process_output(return_code, stdout, stderr, input_info, **kwargs)
            
            # Copy only output files (not logs) if requested
            if output_dir:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                
                # Only copy actual output files, not log files
                output_files = result.get('output_files', [])
                
                if output_files:
                    # Copy only output files
                    copied_files = copy_files(output_files, output_dir, flatten=True)
                    result['copied_files'] = copied_files
                    
                    logger.info(f"Copied {len(copied_files)} files to: {output_dir}")
            
            return result
            
        finally:
            # Clean up just the tool directory if requested, not the entire workspace
            if cleanup:
                import shutil
                import glob
                
                # If keep_patterns is specified, only delete files that don't match patterns
                if keep_patterns:
                    for root, _, files in os.walk(workspace_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            should_keep = any(glob.fnmatch.fnmatch(os.path.basename(file_path), pattern) 
                                           for pattern in keep_patterns)
                            if not should_keep:
                                try:
                                    os.unlink(file_path)
                                    logger.debug(f"Deleted: {file_path}")
                                except:
                                    pass
                else:
                    # Otherwise remove the entire directory
                    try:
                        shutil.rmtree(workspace_path)
                        logger.debug(f"Cleaned up tool directory: {workspace_path}")
                    except:
                        logger.debug(f"Failed to clean up tool directory: {workspace_path}")
    
    def __enter__(self) -> 'BaseExternalTool':
        """
        Context manager entry.
        
        Ensures a workspace is created.
        
        Returns:
            BaseExternalTool: Self reference
        """
        if not self.workspace_manager.current_workspace:
            self.workspace_manager.create_workspace()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit.
        
        Cleans up the workspace unless an exception occurred.
        """
        # Let the workspace manager handle cleanup
        self.workspace_manager.__exit__(exc_type, exc_val, exc_tb)