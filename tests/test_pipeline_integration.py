#!/usr/bin/env python3
"""
Integration test for the MolecularPipeline.
Tests chaining multiple transformations in a single pipeline.
"""

import os
import unittest
import tempfile
import shutil
import logging
import glob

from moltools.pipeline import MolecularPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for the MolecularPipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Define paths to test files
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sample_dir = os.path.join(self.base_dir, "samplefiles", "1NEC")
        self.mapping_dir = os.path.join(self.base_dir, "mappings")
        
        self.car_file = os.path.join(self.sample_dir, "NEC_0H.car")
        self.mdf_file = os.path.join(self.sample_dir, "NEC_0H.mdf")
        self.ff_mapping = os.path.join(self.mapping_dir, "charge_to_ff.json")
        self.charge_mapping = os.path.join(self.mapping_dir, "ff_to_charge.json")
        
        # Output files
        self.output_car = os.path.join(self.temp_dir, "output.car")
        self.output_mdf = os.path.join(self.temp_dir, "output.mdf")
        self.debug_prefix = os.path.join(self.temp_dir, "debug_")
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary directory and all files
        shutil.rmtree(self.temp_dir)
    
    def test_chained_pipeline(self):
        """Test chaining multiple transformations in a single pipeline."""
        # Create a pipeline with method chaining
        pipeline = MolecularPipeline()
        
        # Chain operations
        pipeline.load(self.car_file, self.mdf_file) \
                .update_ff_types(self.ff_mapping) \
                .update_charges(self.charge_mapping) \
                .generate_grid(grid_dims=(2, 2, 2), gap=2.0) \
                .save(self.output_car, self.output_mdf, "TEST")
        
        # Verify output files exist
        self.assertTrue(os.path.exists(self.output_car), "CAR output file was not created")
        self.assertTrue(os.path.exists(self.output_mdf), "MDF output file was not created")
        
        # Read file content
        with open(self.output_car, 'r') as f:
            car_content = f.read()
        
        with open(self.output_mdf, 'r') as f:
            mdf_content = f.read()
            
        # Basic content checks
        self.assertIn("PBC=ON", car_content, "PBC header missing in CAR file")
        self.assertIn("@molecule TEST", mdf_content, "Molecule header missing in MDF file")
        self.assertIn("@periodicity 3 xyz", mdf_content, "Periodicity missing in MDF file")
        
        # Verify system has expected molecules after grid generation
        system = pipeline.get_system()
        self.assertEqual(len(system.molecules), 8, "Grid should have 8 molecules (2x2x2)")
        
        # Verify some transformations happened - atoms should have force-field types updated
        mol = system.molecules[0]
        self.assertGreater(len(mol.atoms), 0, "Molecule has no atoms")
        
        # Check for at least one atom with NEW_ prefix (from force-field mapping)
        found_transformed_atom = False
        for atom in mol.atoms:
            if atom.atom_type.startswith("NEW_"):
                found_transformed_atom = True
                break
        
        self.assertTrue(found_transformed_atom, "No atoms with transformed force-field types found")