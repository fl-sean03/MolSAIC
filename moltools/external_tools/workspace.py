"""
Workspace management for external tools.

This module has been moved to moltools.workspace.
This file exists for backward compatibility.
"""

import logging
import warnings
from typing import Optional, List

from ..workspace import WorkspaceManager, create_global_workspace

# Emit deprecation warning
warnings.warn(
    "The workspace module has been moved from moltools.external_tools.workspace to moltools.workspace. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all symbols for backward compatibility
__all__ = ['WorkspaceManager', 'create_global_workspace']