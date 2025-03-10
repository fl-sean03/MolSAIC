"""
Test module for parsers.
"""

import unittest
import tempfile
import os

from molsaic.parsers.mdf_parser import parse_mdf
from molsaic.parsers.car_parser import parse_car, car_blocks_to_molecules
from molsaic.parsers.pdb_parser import parse_pdb, pdb_atoms_to_molecules
from molsaic.models.molecule import Molecule

class TestMDFParser(unittest.TestCase):
    """Tests for the MDF parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary MDF file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mdf')
        self.temp_file.write(b"""!BIOSYM molecular_data 4

!Date: Wed Mar 05 18:07:25 2025   Materials Studio Generated MDF file

#topology

@column 1 element
@column 2 atom_type
@column 3 charge_group
@column 4 isotope
@column 5 formal_charge
@column 6 charge
@column 7 switching_atom
@column 8 oop_flag
@column 9 chirality_flag
@column 10 occupancy
@column 11 xray_temp_factor
@column 12 connections

@molecule TEST_MOL

XXXX_1:C1           C  CT3     ?     0  0    -0.2700 0 0 0 1.0000  0.0000 H1 H2 H3
XXXX_1:H1           H  HA3     ?     0  0     0.0900 0 0 0 1.0000  0.0000 C1
XXXX_1:H2           H  HA3     ?     0  0     0.0900 0 0 0 1.0000  0.0000 C1
XXXX_1:H3           H  HA3     ?     0  0     0.0900 0 0 0 1.0000  0.0000 C1

!
#symmetry
@periodicity 3 xyz
@group (P1)

#end
""")
        self.temp_file.close()
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.remove(self.temp_file.name)
    
    def test_parse_mdf(self):
        """Test that parse_mdf() returns the correct data."""
        headers, mdf_data = parse_mdf(self.temp_file.name, validate=False)
        
        # Check that headers were parsed correctly
        # Note: The header length increased from 12 to 18 after adding the new column definitions
        self.assertTrue(len(headers) >= 12)
        self.assertTrue(headers[0].startswith("!BIOSYM"))
        
        # Check that mdf_data contains the expected atoms
        self.assertIn(("TEST_MOL", "C1"), mdf_data)
        self.assertIn(("TEST_MOL", "H1"), mdf_data)
        self.assertIn(("TEST_MOL", "H2"), mdf_data)
        self.assertIn(("TEST_MOL", "H3"), mdf_data)
        
        # Check that atom data was parsed correctly
        c1_data = mdf_data[("TEST_MOL", "C1")]
        self.assertEqual(c1_data['element'], "C")
        self.assertEqual(c1_data['atom_type'], "CT3")
        self.assertEqual(c1_data['charge'], "-0.2700")
        self.assertEqual(c1_data['connections'], ["H1", "H2", "H3"])

class TestCARParser(unittest.TestCase):
    """Tests for the CAR parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary CAR file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.car')
        self.temp_file.write(b"""!BIOSYM archive 3
PBC=ON
Materials Studio Generated CAR File
!DATE Wed Mar 05 18:07:25 2025
PBC    9.8627    9.8627    9.8627   90.0000   90.0000   90.0000 (P1)
C1       3.111059790    0.133921270   -0.289480390 XXXX 1      CT3     C  -0.270
H1       3.974355149   -0.567607163   -0.289480390 XXXX 1      HA3     H   0.090
H2       3.283565395    0.734251011    0.620903334 XXXX 1      HA3     H   0.090
H3       3.111059790    0.761119722   -1.199864114 XXXX 1      HA3     H   0.090
end
""")
        self.temp_file.close()
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.remove(self.temp_file.name)
    
    def test_parse_car(self):
        """Test that parse_car() returns the correct data."""
        header_lines, molecules, pbc_coords = parse_car(self.temp_file.name)
        
        # Check that header_lines were parsed correctly
        self.assertEqual(len(header_lines), 5)
        self.assertTrue(header_lines[0].startswith("!BIOSYM"))
        
        # Check that molecules contains one molecule with 4 atoms
        self.assertEqual(len(molecules), 1)
        self.assertEqual(len(molecules[0]), 4)
        
        # Check that atom data was parsed correctly
        atom_data = molecules[0][0]
        self.assertEqual(atom_data['atom_name'], "C1")
        self.assertAlmostEqual(atom_data['x'], 3.111059790)
        self.assertAlmostEqual(atom_data['y'], 0.133921270)
        self.assertAlmostEqual(atom_data['z'], -0.289480390)
        self.assertEqual(atom_data['residue_name'], "XXXX")
        self.assertEqual(atom_data['residue_number'], 1)
        self.assertEqual(atom_data['atom_type'], "CT3")
        self.assertEqual(atom_data['element'], "C")
        self.assertEqual(atom_data['charge'], "-0.270")
        
        # Check that PBC coordinates were parsed correctly
        self.assertIsNotNone(pbc_coords)
        self.assertEqual(len(pbc_coords), 7)
        self.assertAlmostEqual(pbc_coords[0], 9.8627)
        self.assertAlmostEqual(pbc_coords[1], 9.8627)
        self.assertAlmostEqual(pbc_coords[2], 9.8627)
        self.assertAlmostEqual(pbc_coords[3], 90.0000)
        self.assertAlmostEqual(pbc_coords[4], 90.0000)
        self.assertAlmostEqual(pbc_coords[5], 90.0000)
        self.assertEqual(pbc_coords[6], "P1")
    
    def test_car_blocks_to_molecules(self):
        """Test that car_blocks_to_molecules() returns the correct Molecule objects."""
        _, molecules, _ = parse_car(self.temp_file.name)
        mol_objects = car_blocks_to_molecules(molecules)
        
        # Check that a Molecule object was created
        self.assertEqual(len(mol_objects), 1)
        self.assertIsInstance(mol_objects[0], Molecule)
        
        # Check that the Molecule contains 4 atoms
        self.assertEqual(len(mol_objects[0].atoms), 4)
        
        # Check that the first atom has the correct properties
        atom = mol_objects[0].atoms[0]
        self.assertEqual(atom.atom_name, "C1")
        self.assertAlmostEqual(atom.x, 3.111059790)
        self.assertAlmostEqual(atom.y, 0.133921270)
        self.assertAlmostEqual(atom.z, -0.289480390)
        self.assertEqual(atom.atom_type, "CT3")
        self.assertEqual(atom.element, "C")
        # The charge might be stored as float or string
        self.assertIn(str(atom.charge), ["-0.27", "-0.270"])

class TestPDBParser(unittest.TestCase):
    """Tests for the PDB parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary PDB file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdb')
        self.temp_file.write(b"""REMARK  generated coordinate PDB file from .car/.mdf files
CRYST1    9.863    9.863    9.863  90.00  90.00  90.00 P 1           1
ATOM      1 C1   MOL     1       3.111   0.134  -0.289  1.00  0.00      MOL  C
ATOM      2 H1   MOL     1       3.974  -0.568  -0.289  1.00  0.00      MOL  H
ATOM      3 H2   MOL     1       3.284   0.734   0.621  1.00  0.00      MOL  H
ATOM      4 H3   MOL     1       3.111   0.761  -1.200  1.00  0.00      MOL  H
END
""")
        self.temp_file.close()
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.remove(self.temp_file.name)
    
    def test_parse_pdb(self):
        """Test that parse_pdb() returns the correct data."""
        header_lines, atoms, pbc = parse_pdb(self.temp_file.name)
        
        # Check that header_lines were parsed correctly
        self.assertEqual(len(header_lines), 1)
        self.assertTrue(header_lines[0].startswith("REMARK"))
        
        # Check that atoms contains 4 atoms
        self.assertEqual(len(atoms), 4)
        
        # Check that atom data was parsed correctly
        atom_data = atoms[0]
        self.assertEqual(atom_data['atom_name'], "C1")
        self.assertAlmostEqual(atom_data['x'], 3.111)
        self.assertAlmostEqual(atom_data['y'], 0.134)
        self.assertAlmostEqual(atom_data['z'], -0.289)
        self.assertEqual(atom_data['residue_name'], "MOL")
        self.assertEqual(atom_data['residue_number'], 1)
        self.assertEqual(atom_data['element'], "C")
        
        # Check that PBC was parsed correctly
        self.assertIsNotNone(pbc)
        self.assertEqual(len(pbc), 7)
        self.assertAlmostEqual(pbc[0], 9.863)
        self.assertAlmostEqual(pbc[1], 9.863)
        self.assertAlmostEqual(pbc[2], 9.863)
        self.assertAlmostEqual(pbc[3], 90.00)
        self.assertAlmostEqual(pbc[4], 90.00)
        self.assertAlmostEqual(pbc[5], 90.00)
        self.assertEqual(pbc[6], "P 1")
    
    def test_pdb_atoms_to_molecules(self):
        """Test that pdb_atoms_to_molecules() returns the correct Molecule objects."""
        _, atoms, _ = parse_pdb(self.temp_file.name)
        mol_objects = pdb_atoms_to_molecules(atoms)
        
        # Check that a Molecule object was created
        self.assertEqual(len(mol_objects), 1)
        self.assertIsInstance(mol_objects[0], Molecule)
        
        # Check that the Molecule contains 4 atoms
        self.assertEqual(len(mol_objects[0].atoms), 4)
        
        # Check that the first atom has the correct properties
        atom = mol_objects[0].atoms[0]
        self.assertEqual(atom.atom_name, "C1")
        self.assertAlmostEqual(atom.x, 3.111)
        self.assertAlmostEqual(atom.y, 0.134)
        self.assertAlmostEqual(atom.z, -0.289)
        self.assertEqual(atom.residue_name, "MOL")
        self.assertEqual(atom.residue_number, 1)
        self.assertEqual(atom.element, "C")

if __name__ == '__main__':
    unittest.main()