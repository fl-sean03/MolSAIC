"""
Unit tests for the MolecularPipeline class.
"""

import os
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock

from moltools.pipeline import MolecularPipeline
from moltools.models.system import System
from moltools.models.molecule import Molecule
from moltools.models.atom import Atom

class TestMolecularPipeline(unittest.TestCase):
    """Test cases for the MolecularPipeline class."""
    
    @patch('moltools.models.system.System.system_from_files')
    def test_load(self, mock_system_from_files):
        """Test loading files into the pipeline."""
        # Set up mock
        mock_system = MagicMock()
        mock_system.molecules = [MagicMock()]
        mock_system_from_files.return_value = mock_system
        
        # Create pipeline and load
        pipeline = MolecularPipeline()
        result = pipeline.load("test.car", "test.mdf")
        
        # Verify
        mock_system_from_files.assert_called_once_with("test.car", "test.mdf")
        self.assertEqual(pipeline.system, mock_system)
        self.assertEqual(pipeline.transform_count, 0)
        self.assertEqual(result, pipeline)  # Verify method chaining
    
    def test_save(self):
        """Test saving system to files."""
        # Create a system with mock
        mock_system = MagicMock()
        
        # Create pipeline and set system
        pipeline = MolecularPipeline()
        pipeline.system = mock_system
        
        # Call save
        result = pipeline.save("output.car", "output.mdf", "TEST")
        
        # Verify
        mock_system.to_files.assert_called_once_with(
            "output.car", "output.mdf", "TEST", None
        )
        self.assertEqual(result, pipeline)  # Verify method chaining
    
    def test_save_without_system(self):
        """Test saving without loading a system first."""
        pipeline = MolecularPipeline()
        
        with self.assertRaises(ValueError):
            pipeline.save("output.car", "output.mdf")
    
    def test_update_ff_types(self):
        """Test updating force-field types through the pipeline."""
        # Create a system with mock
        mock_system = MagicMock()
        mock_system.update_ff_types.return_value = 10  # 10 updates
        
        # Create pipeline and set system
        pipeline = MolecularPipeline()
        pipeline.system = mock_system
        
        # Call update_ff_types
        result = pipeline.update_ff_types("mapping.json")
        
        # Verify
        mock_system.update_ff_types.assert_called_once_with("mapping.json")
        self.assertEqual(pipeline.transform_count, 1)
        self.assertEqual(result, pipeline)  # Verify method chaining
    
    def test_update_ff_types_without_system(self):
        """Test updating force-field types without loading a system first."""
        pipeline = MolecularPipeline()
        
        with self.assertRaises(ValueError):
            pipeline.update_ff_types("mapping.json")
    
    def test_update_charges(self):
        """Test updating charges through the pipeline."""
        # Create a system with mock
        mock_system = MagicMock()
        mock_system.update_charges.return_value = 10  # 10 updates
        
        # Create pipeline and set system
        pipeline = MolecularPipeline()
        pipeline.system = mock_system
        
        # Call update_charges
        result = pipeline.update_charges("mapping.json")
        
        # Verify
        mock_system.update_charges.assert_called_once_with("mapping.json")
        self.assertEqual(pipeline.transform_count, 1)
        self.assertEqual(result, pipeline)  # Verify method chaining
    
    def test_update_charges_without_system(self):
        """Test updating charges without loading a system first."""
        pipeline = MolecularPipeline()
        
        with self.assertRaises(ValueError):
            pipeline.update_charges("mapping.json")
    
    def test_generate_grid(self):
        """Test generating a grid through the pipeline."""
        # Create a system with mock
        mock_molecule = MagicMock()
        mock_system = MagicMock()
        mock_system.molecules = [mock_molecule]
        
        # Create pipeline and set system
        pipeline = MolecularPipeline()
        pipeline.system = mock_system
        
        # Call generate_grid
        result = pipeline.generate_grid((2, 2, 2), 1.0)
        
        # Verify
        mock_system.generate_grid.assert_called_once_with(mock_molecule, (2, 2, 2), 1.0)
        self.assertEqual(pipeline.transform_count, 1)
        self.assertEqual(result, pipeline)  # Verify method chaining
    
    def test_generate_grid_without_system(self):
        """Test generating a grid without loading a system first."""
        pipeline = MolecularPipeline()
        
        with self.assertRaises(ValueError):
            pipeline.generate_grid()
    
    def test_generate_grid_without_molecules(self):
        """Test generating a grid with a system that has no molecules."""
        mock_system = MagicMock()
        mock_system.molecules = []
        
        pipeline = MolecularPipeline()
        pipeline.system = mock_system
        
        with self.assertRaises(ValueError):
            pipeline.generate_grid()
    
    def test_debug_mode(self):
        """Test debug mode with intermediate file output."""
        # Create a system with mock
        mock_system = MagicMock()
        mock_system.molecules = [MagicMock()]
        
        # Create pipeline in debug mode and set system
        with tempfile.TemporaryDirectory() as tmpdir:
            debug_prefix = os.path.join(tmpdir, "debug_")
            pipeline = MolecularPipeline(debug=True, debug_prefix=debug_prefix)
            pipeline.system = mock_system
            
            # Perform multiple transformations
            pipeline.update_ff_types("mapping.json")
            pipeline.update_charges("mapping.json")
            
            # Verify debug files were requested
            self.assertEqual(mock_system.to_files.call_count, 2)
            mock_system.to_files.assert_any_call(
                f"{debug_prefix}1_output.car",
                f"{debug_prefix}1_output.mdf",
                "DEBUG_1"
            )
            mock_system.to_files.assert_any_call(
                f"{debug_prefix}2_output.car",
                f"{debug_prefix}2_output.mdf",
                "DEBUG_2"
            )
    
    def test_get_system(self):
        """Test getting the system object from the pipeline."""
        # Create a system
        mock_system = MagicMock()
        
        # Create pipeline and set system
        pipeline = MolecularPipeline()
        pipeline.system = mock_system
        
        # Get system
        system = pipeline.get_system()
        
        # Verify
        self.assertEqual(system, mock_system)
    
    def test_get_system_without_loading(self):
        """Test getting the system without loading first."""
        pipeline = MolecularPipeline()
        
        with self.assertRaises(ValueError):
            pipeline.get_system()
    
    def test_method_chaining(self):
        """Test method chaining with the fluent API."""
        # Set up mocks
        mock_system = MagicMock()
        mock_system.molecules = [MagicMock()]
        
        with patch('moltools.models.system.System.system_from_files') as mock_system_from_files:
            mock_system_from_files.return_value = mock_system
            
            # Create pipeline with fluent API
            pipeline = MolecularPipeline()
            result = (pipeline
                      .load("input.car", "input.mdf")
                      .update_ff_types("ff_mapping.json")
                      .update_charges("charge_mapping.json")
                      .generate_grid((3, 3, 3), 1.5)
                      .save("output.car", "output.mdf"))
            
            # Verify method calls
            mock_system_from_files.assert_called_once()
            mock_system.update_ff_types.assert_called_once()
            mock_system.update_charges.assert_called_once()
            mock_system.generate_grid.assert_called_once()
            mock_system.to_files.assert_called_once()
            
            # Verify transform count
            self.assertEqual(pipeline.transform_count, 3)
            
            # Verify method chaining works
            self.assertEqual(result, pipeline)

if __name__ == '__main__':
    unittest.main()