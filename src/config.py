"""
Configuration module for MolSAIC.
Provides default parameters and logging setup.
"""

import logging
import warnings
import os
import tempfile
from pathlib import Path

# Default configuration values
DEFAULT_GRID_SIZE = 8
DEFAULT_GAP = 2.0
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_OBJECT_MODE = True  # Set object-based pipeline as the default

# Workspace configuration moved from external_tools/config.py
# IMPORTANT: Always use current working directory, never fall back to temp
# The actual directory creation and error handling happens in the CLI
DEFAULT_WORKSPACE_PATH = os.environ.get(
    'MOLSAIC_WORKSPACE_PATH', 
    os.path.join(".", ".molsaic_workspace")  # Use relative path to avoid getcwd() issues
)

# Don't try to create the directory at import time - we'll do this in the CLI
WORKSPACE_RETENTION = 24  # Default: clean up workspaces older than 24 hours

# Temporary file patterns for workspaces
TEMP_FILE_PATTERNS = [
    '*.tmp', 
    'temp_*.*', 
    '*.log',
]

# File patterns to always keep
PRESERVE_FILE_PATTERNS = [
    '*.pdb',
    '*.psf',
    '*.namd',
    '*.params',
    '*.out',
    '*_output.log',
    '*_error.log',
    '*_command.log',
    'process_*.log',
    'molsaic.log'
]

# Deprecation settings for file-mode
FILE_MODE_DEPRECATED = True  # Flag indicating file mode is deprecated
FILE_MODE_REMOVAL_VERSION = "2.0.0"  # Version when file mode will be removed
FILE_MODE_DEPRECATION_MESSAGE = (
    "File-based mode is deprecated and will be removed in version {version}. "
    "Please use the default object-based mode instead."
)

# Warning levels (increasing severity)
WARNING_LEVEL_INFO = 0      # General information about deprecation
WARNING_LEVEL_WARNING = 1   # Warning that deprecation is planned
WARNING_LEVEL_ERROR = 2     # Error indicating removal is imminent
CURRENT_WARNING_LEVEL = WARNING_LEVEL_WARNING

# Global variables
_memory_handler = None
_memory_logs = []
session_workspace = None  # Will hold the global workspace for the current session
keep_session_workspace = False  # Flag to keep the session workspace 
keep_all_workspaces = False  # Flag to keep all workspaces

class MemoryHandler(logging.Handler):
    """Custom handler that stores logs in memory until they can be flushed to file."""
    
    def __init__(self):
        super().__init__()
        self.logs = []
        self.formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.setLevel(logging.DEBUG)  # Always capture everything
        
    def emit(self, record):
        # Store a copy of the record to avoid issues with record reuse
        self.logs.append(self.format(record))
        
    def flush_to_file(self, file_path):
        """Flush all stored logs to a file."""
        try:
            with open(file_path, 'w') as f:
                for log_line in self.logs:
                    f.write(log_line + '\n')
            return True
        except Exception as e:
            logging.error(f"Error flushing logs to file: {str(e)}")
            return False

def setup_logging(log_level=DEFAULT_LOG_LEVEL):
    """
    Sets up logging for MolSAIC.
    
    Args:
        log_level (str): Logging level. Default is INFO.
    """
    global _memory_handler
    
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Set up basic configuration with standard format
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Add memory handler to capture all logs for later flushing
    if _memory_handler is None:
        _memory_handler = MemoryHandler()
        _memory_handler.setLevel(logging.DEBUG)  # Capture all logs regardless of console level
        
        # Add the handler to the root logger
        logging.getLogger().addHandler(_memory_handler)

def flush_logs_to_file(file_path):
    """
    Flush all logs captured in memory to a file.
    
    Args:
        file_path (str): Path to the log file
        
    Returns:
        bool: True if successful, False otherwise
    """
    global _memory_handler
    
    if _memory_handler is None:
        logging.warning("No memory handler initialized for log flushing")
        return False
        
    return _memory_handler.flush_to_file(file_path)
    
def show_file_mode_deprecation_warning(logger=None):
    """
    Shows a deprecation warning for file mode based on the current warning level.
    
    Args:
        logger (logging.Logger, optional): Logger to use for warning. 
                                          If None, uses warnings module.
    """
    if not FILE_MODE_DEPRECATED:
        return
        
    # Format the message
    message = FILE_MODE_DEPRECATION_MESSAGE.format(version=FILE_MODE_REMOVAL_VERSION)
    
    # Show warning based on severity level
    if logger is not None:
        if CURRENT_WARNING_LEVEL >= WARNING_LEVEL_ERROR:
            logger.error(message)
        elif CURRENT_WARNING_LEVEL >= WARNING_LEVEL_WARNING:
            logger.warning(message)
        else:
            logger.info(message)
    else:
        if CURRENT_WARNING_LEVEL >= WARNING_LEVEL_ERROR:
            warnings.warn(message, DeprecationWarning, stacklevel=2)
        elif CURRENT_WARNING_LEVEL >= WARNING_LEVEL_WARNING:
            warnings.warn(message, PendingDeprecationWarning, stacklevel=2)
        else:
            warnings.warn(message, UserWarning, stacklevel=2)