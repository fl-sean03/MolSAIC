"""
External tools integration framework for MolSAIC.

This module provides base classes and interfaces for integrating external
executable tools with the MolSAIC object-based workflow.
"""

from .base import BaseExternalTool
from .workspace import WorkspaceManager
from .msi2namd import MSI2NAMDTool
from .packmol import PackmolTool

__all__ = ['BaseExternalTool', 'WorkspaceManager', 'MSI2NAMDTool', 'PackmolTool']