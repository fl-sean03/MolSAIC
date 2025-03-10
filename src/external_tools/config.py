"""
Configuration for external tools integration.

This module contains configuration settings for external tool executables
and tool-specific options. Workspace configuration has been moved to the
main config module.
"""

import os
import logging
from pathlib import Path
from .. import config as main_config

logger = logging.getLogger(__name__)

# Refer to the main config for workspace configuration
DEFAULT_WORKSPACE_PATH = main_config.DEFAULT_WORKSPACE_PATH
WORKSPACE_RETENTION = main_config.WORKSPACE_RETENTION
TEMP_FILE_PATTERNS = main_config.TEMP_FILE_PATTERNS
PRESERVE_FILE_PATTERNS = main_config.PRESERVE_FILE_PATTERNS

# External executable paths (default to expecting them in PATH)
# Users can override these through environment variables
EXECUTABLES = {
    # Map tool name to either: 
    # - None (expect in PATH)
    # - Absolute path to executable
    # - List of potential locations to check
    'msi2namd': os.environ.get('MOLTOOLS_MSI2NAMD_PATH', '/home/sf2/LabWork/software/msi2namd.exe'),
    'packmol': os.environ.get('MOLTOOLS_PACKMOL_PATH', '/home/sf2/LabWork/software/packmol-20.15.3/packmol'),
}

# Maximum concurrent external processes
MAX_CONCURRENT_PROCESSES = int(os.environ.get('MOLTOOLS_MAX_PROCESSES', '4'))

# Timeouts (in seconds)
DEFAULT_PROCESS_TIMEOUT = int(os.environ.get('MOLTOOLS_PROCESS_TIMEOUT', '300'))  # 5 minutes
