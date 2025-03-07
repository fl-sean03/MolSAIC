"""
Module for the Molecule class - represents a collection of atoms.
"""

import logging

logger = logging.getLogger(__name__)

class Molecule:
    """
    A class representing a molecule as a collection of atoms.
    
    Attributes:
        atoms (list): List of Atom objects making up the molecule.
    """
    
    def __init__(self, atoms):
        """
        Initialize a Molecule object.
        
        Args:
            atoms (list): List of Atom objects.
        """
        self.atoms = atoms
    
    def compute_bbox(self):
        """
        Compute the bounding box, center, and size of the molecule.
        
        Returns:
            tuple: A tuple containing:
                - bbox (tuple): (min_x, max_x, min_y, max_y, min_z, max_z)
                - center (tuple): (center_x, center_y, center_z)
                - size (tuple): (size_x, size_y, size_z)
        """
        if not self.atoms:
            logger.warning("Attempting to compute bounding box of empty molecule")
            return (0, 0, 0, 0, 0, 0), (0, 0, 0), (0, 0, 0)
        
        xs = [atom.x for atom in self.atoms]
        ys = [atom.y for atom in self.atoms]
        zs = [atom.z for atom in self.atoms]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
        
        center = ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
        size = (max_x - min_x, max_y - min_y, max_z - min_z)
        
        bbox = (min_x, max_x, min_y, max_y, min_z, max_z)
        return bbox, center, size
    
    def replicate(self, offset, center=None):
        """
        Create a new Molecule by translating this molecule.
        
        Args:
            offset (tuple): The translation offset (x, y, z).
            center (tuple, optional): The center point for translation. 
                If None, the molecule's bounding box center is used.
        
        Returns:
            Molecule: A new translated Molecule.
        """
        if center is None:
            _, center, _ = self.compute_bbox()
        
        new_atoms = []
        # First, create all atoms to get their references
        atom_map = {}  # Maps original atom names to new atom objects
        
        for atom in self.atoms:
            new_atom = atom.copy()
            new_atom.x = atom.x - center[0] + offset[0]
            new_atom.y = atom.y - center[1] + offset[1]
            new_atom.z = atom.z - center[2] + offset[2]
            new_atom.residue_number = 1  # Reset residue number for each copy
            new_atoms.append(new_atom)
            atom_map[atom.atom_name] = new_atom
        
        # Now that all atoms exist, preserve connection information
        for i, atom in enumerate(self.atoms):
            if hasattr(atom, 'connections') and atom.connections:
                # Connections are preserved as they were in the original molecule
                new_atoms[i].connections = atom.connections.copy()
        
        return Molecule(new_atoms)
    
    def __len__(self):
        """
        Get the number of atoms in the molecule.
        
        Returns:
            int: Number of atoms.
        """
        return len(self.atoms)
    
    def __repr__(self):
        """
        String representation of the molecule.
        
        Returns:
            str: A string representation of the molecule.
        """
        if not self.atoms:
            return "Molecule(empty)"
        
        return f"Molecule({len(self.atoms)} atoms, residue={self.atoms[0].residue_name})"