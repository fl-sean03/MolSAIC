"""
Integration tests for the external tools framework.

These tests verify the integration between the external tools framework 
and the MolecularPipeline, focusing on actual functionality with real
data files.
"""

import os
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest import mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from moltools.pipeline import MolecularPipeline
from moltools.external_tools.msi2namd import MSI2NAMDTool

class TestMSI2NAMDIntegration(unittest.TestCase):
    """Integration tests for MSI2NAMD tool."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for outputs
        self.test_dir = tempfile.mkdtemp()
        
        # Set paths to sample files
        sample_dir = Path(__file__).parent.parent.parent / "samplefiles" / "1NEC"
        self.car_file = str(sample_dir / "NEC_0H.car")
        self.mdf_file = str(sample_dir / "NEC_0H.mdf")
        
        # Create output directory
        self.output_dir = os.path.join(self.test_dir, "namd_output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Mock the MSI2NAMD execution since we don't have the actual executable
        self.mock_execute = mock.patch.object(
            MSI2NAMDTool, 
            'execute',
            return_value={
                'return_code': 0,
                'stdout': 'Conversion successful',
                'stderr': '',
                'pdb_file': os.path.join(self.test_dir, 'mock.pdb'),
                'psf_file': os.path.join(self.test_dir, 'mock.psf'),
                'namd_file': os.path.join(self.test_dir, 'mock.namd'),
                'param_file': os.path.join(self.test_dir, 'mock.params'),
                'output_files': [
                    os.path.join(self.test_dir, 'mock.pdb'),
                    os.path.join(self.test_dir, 'mock.psf'),
                    os.path.join(self.test_dir, 'mock.namd'),
                    os.path.join(self.test_dir, 'mock.params')
                ]
            }
        )
        
        # Create mock output files
        for ext in ['pdb', 'psf', 'namd', 'params']:
            with open(os.path.join(self.test_dir, f'mock.{ext}'), 'w') as f:
                f.write(f'Mock {ext} file')
        
        # Start mocks
        self.mock_execute_func = self.mock_execute.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop mocks
        self.mock_execute.stop()
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_pipeline_convert_to_namd(self):
        """Test the convert_to_namd method in MolecularPipeline."""
        # Create pipeline
        pipeline = MolecularPipeline()
        
        # Load data
        pipeline.load(self.car_file, self.mdf_file)
        
        # Convert to NAMD
        pipeline.convert_to_namd(
            output_dir=self.output_dir,
            residue_name="NEC",
            cleanup_workspace=True
        )
        
        # Check that the mock was called with expected arguments
        self.mock_execute_func.assert_called_once()
        args, kwargs = self.mock_execute_func.call_args
        self.assertIn('system', kwargs)
        self.assertIn('output_dir', kwargs)
        self.assertEqual(self.output_dir, kwargs['output_dir'])
        self.assertEqual("NEC", kwargs['residue_name'])
        
        # Check that namd_files attribute was set
        self.assertIn('pdb_file', pipeline.namd_files)
        self.assertIn('psf_file', pipeline.namd_files)
        self.assertIn('namd_file', pipeline.namd_files)
        self.assertIn('param_file', pipeline.namd_files)
    
    def test_pipeline_chain(self):
        """Test chaining the convert_to_namd method with other methods."""
        # Create pipeline
        pipeline = MolecularPipeline()
        
        # Chain methods
        result = (pipeline
                 .load(self.car_file, self.mdf_file)
                 .convert_to_namd(output_dir=self.output_dir)
                 .validate())  # Should still be chainable
        
        # Check result
        self.assertIsNotNone(result)
        self.assertTrue(result['valid'])
        
        # Check that namd_files attribute was set
        self.assertIn('pdb_file', pipeline.namd_files)

if __name__ == "__main__":
    unittest.main()