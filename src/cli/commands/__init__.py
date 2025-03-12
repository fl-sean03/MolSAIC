"""
Command registry for CLI commands.

This module provides a registry of available CLI commands. New commands should
be imported and registered in the get_commands() function.
"""

from typing import Dict, Type
from molsaic.cli.base import BaseCommand

# Import command classes here
from .grid_command import GridCommand
from .update_ff_command import UpdateFFCommand
from .update_charges_command import UpdateChargesCommand
from .packmol_command import PackmolCommand
from .msi2namd_command import MSI2NAMDCommand

def get_commands() -> Dict[str, Type[BaseCommand]]:
    """
    Get all available commands.
    
    Returns:
        Dict[str, Type[BaseCommand]]: A mapping of command names to command classes
    """
    return {
        # Command name -> Command class mapping
        "grid": GridCommand,
        "update-ff": UpdateFFCommand,
        "update-charges": UpdateChargesCommand,
        "packmol": PackmolCommand,
        "msi2namd": MSI2NAMDCommand,
    }