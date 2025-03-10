"""
Utility functions for external tools integration.

This module provides helper functions for executing external processes,
handling paths, and managing temporary files.
"""

import os
import sys
import stat
import shutil
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple

from . import config

logger = logging.getLogger(__name__)

def find_executable(name: str) -> Optional[str]:
    """
    Find the path to an executable.
    
    Args:
        name: Name of the executable to find
        
    Returns:
        Path to the executable if found, otherwise None
    """
    # First check if we have a configured path
    if name in config.EXECUTABLES and config.EXECUTABLES[name]:
        configured_path = config.EXECUTABLES[name]
        
        # Handle various configurations
        if isinstance(configured_path, str):
            if os.path.isfile(configured_path) and os.access(configured_path, os.X_OK):
                return configured_path
        elif isinstance(configured_path, list):
            for path in configured_path:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    return path
    
    # Search in PATH
    path_env = os.environ.get("PATH", "")
    
    # Add .exe extension if on Windows
    names_to_try = [name]
    if sys.platform.startswith('win'):
        if not name.lower().endswith('.exe'):
            names_to_try.append(f"{name}.exe")
    
    # Search all directories in PATH
    for directory in path_env.split(os.pathsep):
        if not directory:
            continue
            
        for name_to_try in names_to_try:
            exe_file = os.path.join(directory, name_to_try)
            if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
                return exe_file
    
    return None

def create_temp_file(prefix: str = 'molsaic_', suffix: str = '.tmp', 
                     directory: Optional[str] = None, content: Optional[str] = None) -> str:
    """
    Create a temporary file with optional content.
    
    Args:
        prefix: Prefix for temporary file name
        suffix: Suffix for temporary file (extension)
        directory: Directory where to create the file
        content: Optional content to write to the file
        
    Returns:
        Path to the created temporary file
    """
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=directory)
    
    try:
        if content is not None:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
        else:
            os.close(fd)
            
        # Make the file readable and writable by everyone
        os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR | 
                           stat.S_IRGRP | stat.S_IWGRP | 
                           stat.S_IROTH | stat.S_IWOTH)
    except Exception as e:
        os.close(fd)
        os.unlink(temp_path)
        raise e
        
    return temp_path

def run_process(cmd: List[str], cwd: Optional[str] = None, 
                env: Optional[Dict[str, str]] = None, 
                timeout: Optional[int] = None,
                capture_output: bool = True,
                stdin_file: Optional[str] = None) -> Tuple[int, str, str]:
    """
    Run an external process with proper error handling.
    
    Args:
        cmd: Command list to execute
        cwd: Working directory
        env: Environment variables
        timeout: Timeout in seconds
        capture_output: Whether to capture and return stdout/stderr
        stdin_file: Optional file to provide as stdin to the process
        
    Returns:
        Tuple of (return_code, stdout, stderr)
        
    Raises:
        subprocess.TimeoutExpired: If the process times out
        subprocess.SubprocessError: If the process fails to start
    """
    if timeout is None:
        timeout = config.DEFAULT_PROCESS_TIMEOUT
        
    logger.debug(f"Running command: {' '.join(cmd)}")
    
    # Prepare environment
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    
    # Save command to log file in the working directory
    if cwd:
        cmd_log_path = os.path.join(cwd, "process_cmd.log")
        try:
            with open(cmd_log_path, 'w') as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Working directory: {cwd}\n")
                f.write(f"Environment: {str(env)}\n")
                f.write(f"Timeout: {timeout} seconds\n")
                f.write(f"User: {os.environ.get('USER', 'unknown')}\n")
                f.write(f"Path: {os.environ.get('PATH', 'unknown')}\n")
        except Exception as e:
            logger.warning(f"Failed to save command log: {str(e)}")
    
    try:
        # If stdin_file is provided, open it to feed to the subprocess
        stdin_fh = None
        if stdin_file:
            logger.info(f"Using stdin file: {stdin_file}")
            try:
                stdin_fh = open(stdin_file, 'r')
            except Exception as e:
                logger.error(f"Failed to open stdin file: {e}")
                raise RuntimeError(f"Failed to open stdin file: {e}")
                
        # Always use subprocess.Popen to have more control over process execution
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=process_env,
            stdin=stdin_fh if stdin_fh else None,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            bufsize=1  # Line buffered
        )
        
        stdout_data = ""
        stderr_data = ""
        
        # Real-time capture of output if needed
        if capture_output:
            # Use select to handle output as it becomes available
            import select
            import time
            
            # Keep track of stdout and stderr output as it comes in
            stdout_chunks = []
            stderr_chunks = []
            
            # Maximum time to wait (total timeout)
            end_time = time.time() + timeout if timeout else None
            
            # Set up polling
            poller = select.poll()
            poller.register(process.stdout, select.POLLIN)
            poller.register(process.stderr, select.POLLIN)
            
            # Keep track of which files are still open
            open_stdout = True
            open_stderr = True
            
            # To save output as it comes in
            if cwd:
                stdout_log_path = os.path.join(cwd, "process_stdout.log")
                stderr_log_path = os.path.join(cwd, "process_stderr.log")
                stdout_file = open(stdout_log_path, 'w')
                stderr_file = open(stderr_log_path, 'w')
            
            try:
                # Read output while process is running
                while open_stdout or open_stderr:
                    # Check if we've exceeded the timeout
                    if end_time and time.time() > end_time:
                        process.terminate()
                        raise subprocess.TimeoutExpired(cmd, timeout)
                    
                    # Wait for output (100ms timeout)
                    events = poller.poll(100)
                    
                    for fd, event in events:
                        if fd == process.stdout.fileno() and open_stdout:
                            line = process.stdout.readline()
                            if line:
                                stdout_chunks.append(line)
                                if cwd:
                                    stdout_file.write(line)
                                    stdout_file.flush()
                            else:
                                poller.unregister(process.stdout)
                                open_stdout = False
                                
                        elif fd == process.stderr.fileno() and open_stderr:
                            line = process.stderr.readline()
                            if line:
                                stderr_chunks.append(line)
                                if cwd:
                                    stderr_file.write(line)
                                    stderr_file.flush()
                            else:
                                poller.unregister(process.stderr)
                                open_stderr = False
                    
                    # If the process has ended and no more output, break
                    if process.poll() is not None and not events:
                        break
                
                # Read any remaining output
                if open_stdout:
                    remaining_stdout = process.stdout.read()
                    if remaining_stdout:
                        stdout_chunks.append(remaining_stdout)
                        if cwd:
                            stdout_file.write(remaining_stdout)
                
                if open_stderr:
                    remaining_stderr = process.stderr.read()
                    if remaining_stderr:
                        stderr_chunks.append(remaining_stderr)
                        if cwd:
                            stderr_file.write(remaining_stderr)
                
                # Combine all output
                stdout_data = "".join(stdout_chunks)
                stderr_data = "".join(stderr_chunks)
                
            finally:
                # Close log files
                if cwd:
                    stdout_file.close()
                    stderr_file.close()
                    
                    # Save return code
                    try:
                        with open(os.path.join(cwd, "process_result.log"), 'w') as f:
                            f.write(f"Return code: {process.returncode}\n")
                            f.write(f"Execution time: {time.time() - (end_time - timeout) if end_time else 'unknown'} seconds\n")
                    except Exception as e:
                        logger.warning(f"Failed to save result log: {str(e)}")
        else:
            # Wait for process to complete without capturing output
            process.wait(timeout=timeout)
        
        # Return collected data
        return process.returncode, stdout_data, stderr_data
        
    except subprocess.TimeoutExpired as e:
        # Try to terminate the process
        try:
            process.terminate()
        except:
            pass
        
        logger.error(f"Process timed out after {timeout} seconds: {' '.join(cmd)}")
        
        # Save timeout information to log
        if cwd:
            try:
                with open(os.path.join(cwd, "process_error.log"), 'w') as f:
                    f.write(f"ERROR: Process timed out after {timeout} seconds\n")
                    f.write(f"Command: {' '.join(cmd)}\n")
            except Exception as log_err:
                logger.warning(f"Failed to save error log: {str(log_err)}")
        
        raise
        
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to run process: {str(e)}")
        
        # Save error information to log
        if cwd:
            try:
                with open(os.path.join(cwd, "process_error.log"), 'w') as f:
                    f.write(f"ERROR: Failed to run process: {str(e)}\n")
                    f.write(f"Command: {' '.join(cmd)}\n")
            except Exception as log_err:
                logger.warning(f"Failed to save error log: {str(log_err)}")
        
        raise

def copy_files(source_files: Union[str, List[str]], target_dir: str, 
               flatten: bool = False, overwrite: bool = True) -> List[str]:
    """
    Copy files to a target directory.
    
    Args:
        source_files: Path or list of paths to source files (supports glob patterns)
        target_dir: Target directory
        flatten: If True, flatten directory structure
        overwrite: If True, overwrite existing files
        
    Returns:
        List of paths to copied files in the target directory
    """
    import glob
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
    # Convert single file to list
    if isinstance(source_files, str):
        source_files = [source_files]
    
    # Expand glob patterns
    expanded_files = []
    for pattern in source_files:
        expanded_files.extend(glob.glob(pattern, recursive=True))
    
    # Copy each file
    copied_files = []
    for source_file in expanded_files:
        if not os.path.isfile(source_file):
            continue
            
        if flatten:
            # Just use the filename
            target_file = os.path.join(target_dir, os.path.basename(source_file))
        else:
            # Preserve relative path
            rel_path = os.path.relpath(source_file, os.path.commonpath([os.path.dirname(f) for f in expanded_files]))
            target_file = os.path.join(target_dir, rel_path)
            
            # Create parent directories
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
        
        # Skip if file exists and no overwrite
        if not overwrite and os.path.exists(target_file):
            logger.debug(f"Skipping existing file: {target_file}")
            copied_files.append(target_file)
            continue
            
        # Copy the file
        logger.debug(f"Copying {source_file} -> {target_file}")
        shutil.copy2(source_file, target_file)
        copied_files.append(target_file)
    
    return copied_files