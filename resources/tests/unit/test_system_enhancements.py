"""
Unit tests for the enhanced System class methods.
"""

import os
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock

from molsaic.models.system import System
from molsaic.models.molecule import Molecule
from molsaic.models.atom import Atom

class TestSystemEnhancements(unittest.TestCase):
    """Test cases for the enhanced System class methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple system with test data
        self.system = System()
        
        # Create a test molecule with atoms
        atoms = [
            Atom(atom_name="C1", x=1.0, y=1.0, z=1.0, 
                 residue_name="RES", residue_number=1,
                 atom_type="C_TYPE", element="C", charge=-0.27),
            Atom(atom_name="H1", x=2.0, y=1.0, z=1.0, 
                 residue_name="RES", residue_number=1,
                 atom_type="H_TYPE", element="H", charge=0.09),
            Atom(atom_name="N1", x=1.0, y=2.0, z=1.0, 
                 residue_name="RES", residue_number=1,
                 atom_type="N_TYPE", element="N", charge=0.0)
        ]
        
        molecule = Molecule(atoms)
        self.system.molecules.append(molecule)
        
        # Add MDF data
        self.system.mdf_data = {
            ("RES", "C1"): {
                "element": "C",
                "atom_type": "C_TYPE",
                "charge": -0.27,
                "charge_group": "?",
                "isotope": "0",
                "formal_charge": "0",
                "switching_atom": "0",
                "oop_flag": "0",
                "chirality_flag": "0",
                "occupancy": "1.0000",
                "xray_temp_factor": "0.0000",
                "connections": []
            },
            ("RES", "H1"): {
                "element": "H",
                "atom_type": "H_TYPE",
                "charge": 0.09,
                "charge_group": "?",
                "isotope": "0",
                "formal_charge": "0",
                "switching_atom": "0",
                "oop_flag": "0",
                "chirality_flag": "0",
                "occupancy": "1.0000",
                "xray_temp_factor": "0.0000",
                "connections": []
            },
            ("RES", "N1"): {
                "element": "N",
                "atom_type": "N_TYPE",
                "charge": 0.0,
                "charge_group": "?",
                "isotope": "0",
                "formal_charge": "0",
                "switching_atom": "0",
                "oop_flag": "0",
                "chirality_flag": "0",
                "occupancy": "1.0000",
                "xray_temp_factor": "0.0000",
                "connections": []
            }
        }
        
    def test_update_ff_types_with_dict(self):
        """Test updating force-field types using a dictionary mapping."""
        # Create a test mapping
        ff_mapping = {
            (-0.27, "C"): "C_NEW",
            (0.09, "H"): "H_NEW"
        }
        
        # Update force-field types
        updates = self.system.update_ff_types(ff_mapping)
        
        # Verify updates
        self.assertEqual(updates, 2)
        self.assertEqual(self.system.molecules[0].atoms[0].atom_type, "C_NEW")
        self.assertEqual(self.system.molecules[0].atoms[1].atom_type, "H_NEW")
        self.assertEqual(self.system.molecules[0].atoms[2].atom_type, "N_TYPE")  # Unchanged
        
        # Verify MDF data updates
        self.assertEqual(self.system.mdf_data[("RES", "C1")]["atom_type"], "C_NEW")
        self.assertEqual(self.system.mdf_data[("RES", "H1")]["atom_type"], "H_NEW")
        self.assertEqual(self.system.mdf_data[("RES", "N1")]["atom_type"], "N_TYPE")  # Unchanged
    
    def test_update_ff_types_with_file(self):
        """Test updating force-field types using a mapping file."""
        # Create a temporary mapping file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump({
                "(-0.27, C)": "C_NEW_FILE",
                "(0.09, H)": "H_NEW_FILE"
            }, f)
            mapping_file = f.name
        
        try:
            # Update force-field types
            updates = self.system.update_ff_types(mapping_file)
            
            # Verify updates
            self.assertEqual(updates, 2)
            self.assertEqual(self.system.molecules[0].atoms[0].atom_type, "C_NEW_FILE")
            self.assertEqual(self.system.molecules[0].atoms[1].atom_type, "H_NEW_FILE")
            self.assertEqual(self.system.molecules[0].atoms[2].atom_type, "N_TYPE")  # Unchanged
        finally:
            # Clean up
            os.unlink(mapping_file)
    
    def test_update_charges_with_dict(self):
        """Test updating charges using a dictionary mapping."""
        # Create a test mapping
        charge_mapping = {
            "C_TYPE": -0.5,
            "H_TYPE": 0.2
        }
        
        # Update charges
        updates = self.system.update_charges(charge_mapping)
        
        # Verify updates
        self.assertEqual(updates, 2)
        self.assertEqual(self.system.molecules[0].atoms[0].charge, -0.5)
        self.assertEqual(self.system.molecules[0].atoms[1].charge, 0.2)
        self.assertEqual(self.system.molecules[0].atoms[2].charge, 0.0)  # Unchanged
        
        # Verify MDF data updates
        self.assertEqual(self.system.mdf_data[("RES", "C1")]["charge"], -0.5)
        self.assertEqual(self.system.mdf_data[("RES", "H1")]["charge"], 0.2)
        self.assertEqual(self.system.mdf_data[("RES", "N1")]["charge"], 0.0)  # Unchanged
    
    def test_update_charges_with_file(self):
        """Test updating charges using a mapping file."""
        # Create a temporary mapping file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump({
                "C_TYPE": -0.6,
                "H_TYPE": 0.3
            }, f)
            mapping_file = f.name
        
        try:
            # Update charges
            updates = self.system.update_charges(mapping_file)
            
            # Verify updates
            self.assertEqual(updates, 2)
            self.assertEqual(self.system.molecules[0].atoms[0].charge, -0.6)
            self.assertEqual(self.system.molecules[0].atoms[1].charge, 0.3)
            self.assertEqual(self.system.molecules[0].atoms[2].charge, 0.0)  # Unchanged
        finally:
            # Clean up
            os.unlink(mapping_file)
    
    def test_to_files(self):
        """Test writing system to files."""
        # Create temporary output files
        with tempfile.NamedTemporaryFile(delete=False) as car_file, \
             tempfile.NamedTemporaryFile(delete=False) as mdf_file:
            car_path = car_file.name
            mdf_path = mdf_file.name
        
        try:
            # Set PBC for the system
            self.system.pbc = (10.0, 10.0, 10.0, 90.0, 90.0, 90.0, "P1")
            
            # Write files
            self.system.to_files(car_path, mdf_path, base_name="TEST")
            
            # Check that files exist and have content
            self.assertTrue(os.path.exists(car_path))
            self.assertTrue(os.path.exists(mdf_path))
            
            with open(car_path, 'r') as f:
                car_content = f.read()
                self.assertIn("PBC=ON", car_content)
                self.assertIn("C1", car_content)
                self.assertIn("H1", car_content)
                self.assertIn("N1", car_content)
            
            with open(mdf_path, 'r') as f:
                mdf_content = f.read()
                self.assertIn("@molecule TEST", mdf_content)
                self.assertIn("C1", mdf_content)
                self.assertIn("H1", mdf_content)
                self.assertIn("N1", mdf_content)
                self.assertIn("#symmetry", mdf_content)
        finally:
            # Clean up
            if os.path.exists(car_path):
                os.unlink(car_path)
            if os.path.exists(mdf_path):
                os.unlink(mdf_path)
    
    @patch('molsaic.models.system.parse_car')
    @patch('molsaic.models.system.parse_mdf')
    def test_system_from_files(self, mock_parse_mdf, mock_parse_car):
        """Test creating a System from files using the factory method."""
        # Set up mocks
        mock_parse_mdf.return_value = (
            ["MDF Header"],
            {
                ("RES", "C1"): {
                    "element": "C",
                    "atom_type": "C_TYPE",
                    "charge": -0.27,
                    "charge_group": "?",
                    "isotope": "0",
                    "formal_charge": "0",
                    "switching_atom": "0",
                    "oop_flag": "0",
                    "chirality_flag": "0",
                    "occupancy": "1.0000",
                    "xray_temp_factor": "0.0000",
                    "connections": []
                }
            }
        )
        
        mock_parse_car.return_value = (
            ["CAR Header"],
            [
                [
                    {
                        'atom_name': 'C1',
                        'x': 1.0,
                        'y': 1.0,
                        'z': 1.0,
                        'residue_name': 'RES',
                        'residue_number': 1,
                        'atom_type': 'C_TYPE',
                        'element': 'C',
                        'charge': -0.27
                    }
                ]
            ],
            (10.0, 10.0, 10.0, 90.0, 90.0, 90.0, "P1")
        )
        
        # Create system from files
        system = System.system_from_files("test.car", "test.mdf")
        
        # Verify system
        self.assertEqual(len(system.molecules), 1)
        self.assertEqual(len(system.molecules[0].atoms), 1)
        self.assertEqual(system.molecules[0].atoms[0].atom_name, "C1")
        self.assertEqual(system.molecules[0].atoms[0].atom_type, "C_TYPE")
        self.assertEqual(system.molecules[0].atoms[0].charge, -0.27)
        self.assertEqual(system.pbc, (10.0, 10.0, 10.0, 90.0, 90.0, 90.0, "P1"))
        self.assertIn(("RES", "C1"), system.mdf_data)

if __name__ == '__main__':
    unittest.main()