"""
Test module for models.
"""

import unittest
from moltools.models.atom import Atom
from moltools.models.molecule import Molecule
from moltools.models.system import System

class TestAtom(unittest.TestCase):
    """Tests for the Atom class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.atom = Atom(
            atom_name="C1",
            x=1.0,
            y=2.0,
            z=3.0,
            residue_name="MOL",
            residue_number=1,
            atom_type="CA",
            element="C",
            charge=-0.27
        )
    
    def test_atom_creation(self):
        """Test that Atom objects are created correctly."""
        self.assertEqual(self.atom.atom_name, "C1")
        self.assertEqual(self.atom.x, 1.0)
        self.assertEqual(self.atom.y, 2.0)
        self.assertEqual(self.atom.z, 3.0)
        self.assertEqual(self.atom.residue_name, "MOL")
        self.assertEqual(self.atom.residue_number, 1)
        self.assertEqual(self.atom.atom_type, "CA")
        self.assertEqual(self.atom.element, "C")
        self.assertEqual(self.atom.charge, -0.27)
        self.assertEqual(self.atom.connections, [])
    
    def test_atom_copy(self):
        """Test that Atom.copy() creates a deep copy."""
        # Add connections to test their copying
        self.atom.connections = ["H1", "H2", "H3"]
        
        copy = self.atom.copy()
        self.assertEqual(copy.atom_name, self.atom.atom_name)
        self.assertEqual(copy.x, self.atom.x)
        self.assertEqual(copy.y, self.atom.y)
        self.assertEqual(copy.z, self.atom.z)
        self.assertEqual(copy.residue_name, self.atom.residue_name)
        self.assertEqual(copy.residue_number, self.atom.residue_number)
        self.assertEqual(copy.atom_type, self.atom.atom_type)
        self.assertEqual(copy.element, self.atom.element)
        self.assertEqual(copy.charge, self.atom.charge)
        self.assertEqual(copy.connections, self.atom.connections)
        
        # Check that it's a deep copy of the list
        self.assertIsNot(copy.connections, self.atom.connections)
        
        # Check that it's a deep copy
        copy.x = 5.0
        self.assertNotEqual(copy.x, self.atom.x)
        
        # Modify connections and ensure they're independent
        copy.connections.append("H4")
        self.assertNotEqual(len(copy.connections), len(self.atom.connections))
    
    def test_as_dict(self):
        """Test that Atom.as_dict() returns the correct dictionary."""
        # Add connections to test they are included in the dict
        self.atom.connections = ["H1", "H2", "H3"]
        
        d = self.atom.as_dict()
        self.assertEqual(d['atom_name'], "C1")
        self.assertEqual(d['x'], 1.0)
        self.assertEqual(d['y'], 2.0)
        self.assertEqual(d['z'], 3.0)
        self.assertEqual(d['residue_name'], "MOL")
        self.assertEqual(d['residue_number'], 1)
        self.assertEqual(d['atom_type'], "CA")
        self.assertEqual(d['element'], "C")
        self.assertEqual(d['charge'], -0.27)
        self.assertEqual(d['connections'], ["H1", "H2", "H3"])
        
        # Make sure it's a copy of the list, not the original
        self.assertIsNot(d['connections'], self.atom.connections)

class TestMolecule(unittest.TestCase):
    """Tests for the Molecule class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.atom1 = Atom(
            atom_name="C1",
            x=0.0,
            y=0.0,
            z=0.0,
            residue_name="MOL",
            residue_number=1,
            atom_type="CA",
            element="C",
            charge=-0.27
        )
        self.atom2 = Atom(
            atom_name="H1",
            x=1.0,
            y=0.0,
            z=0.0,
            residue_name="MOL",
            residue_number=1,
            atom_type="HA",
            element="H",
            charge=0.09
        )
        self.molecule = Molecule([self.atom1, self.atom2])
    
    def test_molecule_creation(self):
        """Test that Molecule objects are created correctly."""
        self.assertEqual(len(self.molecule.atoms), 2)
        self.assertEqual(self.molecule.atoms[0].atom_name, "C1")
        self.assertEqual(self.molecule.atoms[1].atom_name, "H1")
    
    def test_compute_bbox(self):
        """Test that Molecule.compute_bbox() returns the correct values."""
        bbox, center, size = self.molecule.compute_bbox()
        self.assertEqual(bbox, (0.0, 1.0, 0.0, 0.0, 0.0, 0.0))
        self.assertEqual(center, (0.5, 0.0, 0.0))
        self.assertEqual(size, (1.0, 0.0, 0.0))
    
    def test_replicate(self):
        """Test that Molecule.replicate() creates a correctly translated copy."""
        # Add connections to test they are preserved during replication
        self.atom1.connections = ["H1"]
        self.atom2.connections = ["C1"]
        
        offset = (10.0, 10.0, 10.0)
        center = (0.5, 0.0, 0.0)  # Center of the molecule
        new_mol = self.molecule.replicate(offset, center)
        
        # Check that atoms are translated correctly
        self.assertEqual(new_mol.atoms[0].x, 9.5)  # 0.0 - 0.5 + 10.0
        self.assertEqual(new_mol.atoms[0].y, 10.0)  # 0.0 - 0.0 + 10.0
        self.assertEqual(new_mol.atoms[0].z, 10.0)  # 0.0 - 0.0 + 10.0
        
        self.assertEqual(new_mol.atoms[1].x, 10.5)  # 1.0 - 0.5 + 10.0
        self.assertEqual(new_mol.atoms[1].y, 10.0)  # 0.0 - 0.0 + 10.0
        self.assertEqual(new_mol.atoms[1].z, 10.0)  # 0.0 - 0.0 + 10.0
        
        # Check that connections are preserved
        self.assertEqual(new_mol.atoms[0].connections, ["H1"])
        self.assertEqual(new_mol.atoms[1].connections, ["C1"])

class TestSystem(unittest.TestCase):
    """Tests for the System class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.atom1 = Atom(
            atom_name="C1",
            x=0.0,
            y=0.0,
            z=0.0,
            residue_name="MOL",
            residue_number=1,
            atom_type="CA",
            element="C",
            charge=-0.27
        )
        self.atom2 = Atom(
            atom_name="H1",
            x=1.0,
            y=0.0,
            z=0.0,
            residue_name="MOL",
            residue_number=1,
            atom_type="HA",
            element="H",
            charge=0.09
        )
        self.molecule = Molecule([self.atom1, self.atom2])
        self.mdf_data = {
            ("MOL", "C1"): {
                'element': "C",
                'atom_type': "CA",
                'charge_group': "?",
                'isotope': "0",
                'formal_charge': "0",
                'charge': "-0.27",
                'switching_atom': "0",
                'oop_flag': "0",
                'chirality_flag': "0",
                'occupancy': "1.0000",
                'xray_temp_factor': "0.0000",
                'connections': ["H1"]
            },
            ("MOL", "H1"): {
                'element': "H",
                'atom_type': "HA",
                'charge_group': "?",
                'isotope': "0",
                'formal_charge': "0",
                'charge': "0.09",
                'switching_atom': "0",
                'oop_flag': "0",
                'chirality_flag': "0",
                'occupancy': "1.0000",
                'xray_temp_factor': "0.0000",
                'connections': ["C1"]
            }
        }
        self.system = System(self.mdf_data)
    
    def test_system_creation(self):
        """Test that System objects are created correctly."""
        self.assertEqual(self.system.mdf_data, self.mdf_data)
        self.assertEqual(self.system.molecules, [])
        self.assertIsNone(self.system.pbc)
    
    def test_generate_grid(self):
        """Test that System.generate_grid() creates the correct grid."""
        self.system.generate_grid(self.molecule, (2, 2, 2), 1.0)
        self.assertEqual(len(self.system.molecules), 8)  # 2x2x2 = 8 molecules
        self.assertIsNotNone(self.system.pbc)
        
        # Check PBC
        self.assertAlmostEqual(self.system.pbc[0], 4.0)  # 2 * (1.0 (size) + 1.0 (gap))
        self.assertAlmostEqual(self.system.pbc[1], 2.0)  # 2 * (0.0 (size) + 1.0 (gap))
        self.assertAlmostEqual(self.system.pbc[2], 2.0)  # 2 * (0.0 (size) + 1.0 (gap))

if __name__ == '__main__':
    unittest.main()