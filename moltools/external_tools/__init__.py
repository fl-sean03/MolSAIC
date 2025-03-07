"""
External tools integration framework for MolTools.

This module provides base classes and interfaces for integrating external
executable tools with the MolTools object-based workflow.
"""

from .base import BaseExternalTool
from .workspace import WorkspaceManager

__all__ = ['BaseExternalTool', 'WorkspaceManager']