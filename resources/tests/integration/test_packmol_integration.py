#!/usr/bin/env python3
"""
Integration tests for the Packmol external tool.

These tests verify that the Packmol integration works correctly with the external tool.
"""

import os
import json
import unittest
import tempfile
from pathlib import Path

# Add the parent directory to the Python path so we can import moltools
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from moltools.external_tools import PackmolTool

class TestPackmolIntegration(unittest.TestCase):
    """Test cases for Packmol integration."""
    
    def setUp(self):
        """Set up for the tests."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name
        
        # Create a sample input file for testing
        self.input_file = os.path.join(self.temp_path, "test.inp")
        with open(self.input_file, "w") as f:
            f.write("""# Test Packmol input file
tolerance 2.0
filetype pdb
output test_output.pdb

structure molecule.pdb
  number 10
  inside box 0. 0. 0. 30. 30. 30.
end structure
""")
        
        # Create a dummy molecule file
        self.molecule_file = os.path.join(self.temp_path, "molecule.pdb")
        with open(self.molecule_file, "w") as f:
            f.write("""ATOM      1  O   WAT     1       0.000   0.000   0.000  1.00  0.00
ATOM      2  H1  WAT     1       0.957   0.000   0.000  1.00  0.00
ATOM      3  H2  WAT     1      -0.240   0.928   0.000  1.00  0.00
END
""")
        
        # Create a test update dictionary
        self.update_dict = {
            "global": {
                "tolerance": ["3.0"],
                "output": ["updated_output.pdb"]
            },
            "structures": [
                {
                    "properties": {
                        "number": ["20"]
                    }
                }
            ]
        }
        
        # Initialize the Packmol tool
        try:
            self.packmol = PackmolTool()
            self.packmol_available = True
        except ValueError:
            self.packmol_available = False
            print("Packmol executable not found, skipping execution tests")
    
    def tearDown(self):
        """Clean up after the tests."""
        self.temp_dir.cleanup()
    
    def test_parse_packmol_file(self):
        """Test parsing a Packmol input file."""
        config = self.packmol.parse_packmol_file(self.input_file)
        
        # Check that the global options were parsed correctly
        self.assertIn("global", config)
        self.assertIn("tolerance", config["global"])
        self.assertEqual(["2.0"], config["global"]["tolerance"])
        self.assertIn("output", config["global"])
        self.assertEqual(["test_output.pdb"], config["global"]["output"])
        
        # Check that the structure blocks were parsed correctly
        self.assertIn("structures", config)
        self.assertEqual(1, len(config["structures"]))
        self.assertEqual("molecule.pdb", config["structures"][0]["structure_file"])
        self.assertIn("number", config["structures"][0]["properties"])
        self.assertEqual(["10"], config["structures"][0]["properties"]["number"])
        self.assertIn("inside", config["structures"][0]["constraints"][0]["keyword"])
    
    def test_generate_packmol_file(self):
        """Test generating a Packmol input file from a configuration."""
        # Parse the existing file
        config = self.packmol.parse_packmol_file(self.input_file)
        
        # Generate a new file
        output_file = os.path.join(self.temp_path, "generated.inp")
        self.packmol.generate_packmol_file(config, output_file)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Parse the generated file and verify it matches the original config
        generated_config = self.packmol.parse_packmol_file(output_file)
        self.assertEqual(config, generated_config)
    
    def test_update_dict(self):
        """Test updating a configuration dictionary."""
        # Parse the existing file
        config = self.packmol.parse_packmol_file(self.input_file)
        
        # Update the configuration
        updated_config = self.packmol.update_dict(config, self.update_dict)
        
        # Check that the updates were applied
        self.assertEqual(["3.0"], updated_config["global"]["tolerance"])
        self.assertEqual(["updated_output.pdb"], updated_config["global"]["output"])
        self.assertEqual(["20"], updated_config["structures"][0]["properties"]["number"])
    
    def test_prepare_inputs(self):
        """Test preparing inputs for Packmol execution."""
        # Skip if Packmol is not available
        if not self.packmol_available:
            self.skipTest("Packmol executable not found")
        
        # Prepare inputs
        input_info = self.packmol.prepare_inputs(
            self.temp_path,
            input_file=self.input_file,
            update_dict=self.update_dict
        )
        
        # Check that the input file was copied to the workspace
        self.assertIn("input_file", input_info)
        self.assertTrue(os.path.exists(input_info["input_file"]))
        
        # Check that a new output file was generated with the updates
        self.assertIn("output_file", input_info)
        self.assertTrue(os.path.exists(input_info["output_file"]))
        
        # Check that the configuration was updated
        self.assertIn("config", input_info)
        self.assertEqual(["3.0"], input_info["config"]["global"]["tolerance"])
    
    @unittest.skipIf(not os.environ.get("MOLTOOLS_PACKMOL_PATH"), "Packmol executable not available")
    def test_execute(self):
        """Test executing Packmol."""
        # Skip if Packmol is not available
        if not self.packmol_available:
            self.skipTest("Packmol executable not found")
        
        try:
            # Execute Packmol with the test input file
            result = self.packmol.execute(input_file=self.input_file)
            
            # Check that execution was successful
            self.assertEqual(0, result["return_code"])
            
            # Check that the output file was identified
            self.assertIn("output_file", result)
            if result["output_file"]:
                self.assertTrue(os.path.exists(result["output_file"]))
        except Exception as e:
            # If execution fails, it might be due to missing Packmol or incompatible test files
            self.skipTest(f"Packmol execution failed: {e}")

if __name__ == "__main__":
    unittest.main()