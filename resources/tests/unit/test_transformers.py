"""
Test module for transformers.
"""

import unittest
import tempfile
import os
import json

from molsaic.models.atom import Atom
from molsaic.models.molecule import Molecule
from molsaic.models.system import System
# Import from legacy modules instead of the new refactored ones
from molsaic.transformers.legacy.grid import generate_grid
from molsaic.transformers.update_ff import update_ff_types
from molsaic.transformers.legacy.update_ff import load_mapping
from molsaic.transformers.update_charges import update_charges

class TestGridTransformer(unittest.TestCase):
    """Tests for the grid transformer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple molecule for testing
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
    
    def test_generate_grid(self):
        """Test that generate_grid() creates a grid of molecules."""
        system = generate_grid(self.molecule, (2, 2, 2), 1.0)
        
        # Check that a System object was created
        self.assertIsInstance(system, System)
        
        # Check that the System contains 8 molecules
        self.assertEqual(len(system.molecules), 8)
        
        # Check that the PBC was set correctly
        self.assertIsNotNone(system.pbc)
        self.assertEqual(len(system.pbc), 7)
        self.assertAlmostEqual(system.pbc[0], 4.0)  # 2 * (1.0 (size) + 1.0 (gap))
        self.assertAlmostEqual(system.pbc[1], 2.0)  # 2 * (0.0 (size) + 1.0 (gap))
        self.assertAlmostEqual(system.pbc[2], 2.0)  # 2 * (0.0 (size) + 1.0 (gap))
        
        # Check that molecules were placed at different positions
        positions = [(mol.atoms[0].x, mol.atoms[0].y, mol.atoms[0].z) for mol in system.molecules]
        unique_positions = set(positions)
        self.assertEqual(len(unique_positions), 8)

class TestUpdateFFTransformer(unittest.TestCase):
    """Tests for the force-field update transformer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary CAR file for testing
        self.temp_car = tempfile.NamedTemporaryFile(delete=False, suffix='.car')
        self.temp_car.write(b"""!BIOSYM archive 3
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
        self.temp_car.close()
        
        # Create a temporary MDF file for testing
        self.temp_mdf = tempfile.NamedTemporaryFile(delete=False, suffix='.mdf')
        self.temp_mdf.write(b"""!BIOSYM molecular_data 4

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
        self.temp_mdf.close()
        
        # Create a temporary mapping file for testing
        self.temp_mapping = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_mapping.write(b"""
{
    "(-0.27, C)": "NEW_TYPE",
    "(0.09, H)": "NEW_H_TYPE"
}
""")
        self.temp_mapping.close()
        
        # Output files
        self.output_car = tempfile.NamedTemporaryFile(delete=False, suffix='.car').name
        self.output_mdf = tempfile.NamedTemporaryFile(delete=False, suffix='.mdf').name
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.remove(self.temp_car.name)
        os.remove(self.temp_mdf.name)
        os.remove(self.temp_mapping.name)
        if os.path.exists(self.output_car):
            os.remove(self.output_car)
        if os.path.exists(self.output_mdf):
            os.remove(self.output_mdf)
    
    def test_load_mapping(self):
        """Test that load_mapping() loads a mapping from a JSON file."""
        mapping = load_mapping(self.temp_mapping.name)
        self.assertIn((-0.27, "C"), mapping)
        self.assertEqual(mapping[(-0.27, "C")], "NEW_TYPE")
        self.assertIn((0.09, "H"), mapping)
        self.assertEqual(mapping[(0.09, "H")], "NEW_H_TYPE")
    
    def test_update_ff_types(self):
        """Test that update_ff_types() updates force-field types correctly."""
        results = update_ff_types(
            car_file=self.temp_car.name,
            mdf_file=self.temp_mdf.name,
            output_car=self.output_car,
            output_mdf=self.output_mdf,
            mapping_file=self.temp_mapping.name
        )
        
        # Check that updates were made
        self.assertIn("car_updates", results)
        self.assertIn("mdf_updates", results)
        
        # The CAR file has 1 carbon and 3 hydrogens that should be updated
        self.assertEqual(results["car_updates"], 4)
        
        # The MDF file has 1 carbon and 3 hydrogens that should be updated
        self.assertEqual(results["mdf_updates"], 4)
        
        # Check that output files were created
        self.assertTrue(os.path.exists(self.output_car))
        self.assertTrue(os.path.exists(self.output_mdf))

class TestUpdateChargesTransformer(unittest.TestCase):
    """Tests for the charge update transformer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary CAR file for testing
        self.temp_car = tempfile.NamedTemporaryFile(delete=False, suffix='.car')
        self.temp_car.write(b"""!BIOSYM archive 3
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
        self.temp_car.close()
        
        # Create a temporary MDF file for testing
        self.temp_mdf = tempfile.NamedTemporaryFile(delete=False, suffix='.mdf')
        self.temp_mdf.write(b"""!BIOSYM molecular_data 4

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
        self.temp_mdf.close()
        
        # Create a temporary mapping file for testing
        self.temp_mapping = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_mapping.write(b"""
{
    "CT3": -0.33,
    "HA3": 0.11
}
""")
        self.temp_mapping.close()
        
        # Output files
        self.output_car = tempfile.NamedTemporaryFile(delete=False, suffix='.car').name
        self.output_mdf = tempfile.NamedTemporaryFile(delete=False, suffix='.mdf').name
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.remove(self.temp_car.name)
        os.remove(self.temp_mdf.name)
        os.remove(self.temp_mapping.name)
        if os.path.exists(self.output_car):
            os.remove(self.output_car)
        if os.path.exists(self.output_mdf):
            os.remove(self.output_mdf)
    
    def test_update_charges(self):
        """Test that update_charges() updates charges correctly."""
        results = update_charges(
            car_file=self.temp_car.name,
            mdf_file=self.temp_mdf.name,
            output_car=self.output_car,
            output_mdf=self.output_mdf,
            mapping_file=self.temp_mapping.name
        )
        
        # Check that updates were made
        self.assertIn("car_updates", results)
        self.assertIn("mdf_updates", results)
        
        # The CAR file has 1 CT3 atom and 3 HA3 atoms that should be updated
        self.assertEqual(results["car_updates"], 4)
        
        # The MDF file has 1 CT3 atom and 3 HA3 atoms that should be updated
        self.assertEqual(results["mdf_updates"], 4)
        
        # Check that output files were created
        self.assertTrue(os.path.exists(self.output_car))
        self.assertTrue(os.path.exists(self.output_mdf))

if __name__ == '__main__':
    unittest.main()