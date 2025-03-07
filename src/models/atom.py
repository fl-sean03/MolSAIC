"""
Module for the Atom class - represents a single atom in a molecular system.
"""

class Atom:
    """
    A class representing a single atom in a molecular system.
    
    Attributes:
        atom_name (str): Name of the atom (e.g., "C1", "H1").
        x (float): X-coordinate.
        y (float): Y-coordinate.
        z (float): Z-coordinate.
        residue_name (str): Name of the residue the atom belongs to.
        residue_number (int): Number of the residue the atom belongs to.
        atom_type (str): Force field atom type.
        element (str): Chemical element symbol.
        charge (float): Partial charge.
        connections (list): List of atom connection strings.
    """
    
    def __init__(self, atom_name, x, y, z, residue_name, residue_number, atom_type, element, charge, connections=None):
        """
        Initialize an Atom object.
        
        Args:
            atom_name (str): Name of the atom.
            x (float): X-coordinate.
            y (float): Y-coordinate.
            z (float): Z-coordinate.
            residue_name (str): Name of the residue the atom belongs to.
            residue_number (int): Number of the residue the atom belongs to.
            atom_type (str): Force field atom type.
            element (str): Chemical element symbol.
            charge (float or str): Partial charge (can be numeric or string).
            connections (list, optional): List of connection strings. Default is None.
        """
        self.atom_name = atom_name
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.residue_name = residue_name
        self.residue_number = int(residue_number)
        self.atom_type = atom_type
        self.element = element
        self.connections = connections or []
        
        # Handle charge which might be passed as a string
        try:
            self.charge = float(charge)
        except (ValueError, TypeError):
            self.charge = charge  # Keep as string if conversion fails
    
    def copy(self):
        """
        Create a deep copy of this atom.
        
        Returns:
            Atom: A new Atom object with the same attributes.
        """
        return Atom(
            self.atom_name,
            self.x,
            self.y,
            self.z,
            self.residue_name,
            self.residue_number,
            self.atom_type,
            self.element,
            self.charge,
            self.connections.copy() if self.connections else []
        )
    
    def as_dict(self):
        """
        Convert the atom to a dictionary representation.
        
        Returns:
            dict: Dictionary with atom attributes.
        """
        return {
            'atom_name': self.atom_name,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'residue_name': self.residue_name,
            'residue_number': self.residue_number,
            'atom_type': self.atom_type,
            'element': self.element,
            'charge': self.charge,
            'connections': self.connections.copy() if self.connections else []
        }
    
    def __repr__(self):
        """
        String representation of the atom.
        
        Returns:
            str: A string representation of the atom.
        """
        return (f"Atom(name={self.atom_name}, element={self.element}, "
                f"coords=({self.x:.3f}, {self.y:.3f}, {self.z:.3f}), "
                f"residue={self.residue_name}_{self.residue_number})")