"""
Unit tests for the external tools integration framework.

These tests verify the functionality of the core components of 
the external tools framework, including workspace management,
base tool functionality, and specific tool implementations.
"""

import os
import tempfile
import unittest
from unittest import mock
import shutil
from pathlib import Path

from moltools.workspace import WorkspaceManager
from moltools.external_tools.base import BaseExternalTool
from moltools.external_tools import config

class TestWorkspaceManager(unittest.TestCase):
    """Tests for the WorkspaceManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_create_workspace(self):
        """Test creating a workspace directory."""
        # Create workspace manager
        manager = WorkspaceManager(base_path=self.test_dir)
        
        # Create workspace
        workspace_path = manager.create_workspace("test_workspace")
        
        # Check that workspace was created
        self.assertTrue(os.path.exists(workspace_path))
        self.assertTrue(workspace_path.startswith(self.test_dir))
        self.assertTrue(os.path.isdir(workspace_path))
        
        # Check that workspace is set as current
        self.assertEqual(workspace_path, manager.current_workspace)
    
    def test_track_files(self):
        """Test tracking files in a workspace."""
        # Create workspace manager
        manager = WorkspaceManager(base_path=self.test_dir)
        workspace_path = manager.create_workspace("test_workspace")
        
        # Create test files
        file1 = os.path.join(workspace_path, "file1.txt")
        file2 = os.path.join(workspace_path, "file2.log")
        with open(file1, "w") as f:
            f.write("Test file 1")
        with open(file2, "w") as f:
            f.write("Test file 2")
        
        # Track files
        manager.track_file(file1)
        manager.track_files([file2])
        
        # Check tracked files
        tracked_files = manager.get_tracked_files()
        self.assertEqual(2, len(tracked_files))
        self.assertIn(os.path.abspath(file1), tracked_files)
        self.assertIn(os.path.abspath(file2), tracked_files)
        
        # Test filtering
        log_files = manager.get_tracked_files("*.log")
        self.assertEqual(1, len(log_files))
        self.assertIn(os.path.abspath(file2), log_files)
    
    def test_cleanup_current(self):
        """Test cleaning up the current workspace."""
        # Create workspace manager
        manager = WorkspaceManager(base_path=self.test_dir)
        workspace_path = manager.create_workspace("test_workspace")
        
        # Create test files
        file1 = os.path.join(workspace_path, "file1.txt")
        file2 = os.path.join(workspace_path, "file2.log")
        file3 = os.path.join(workspace_path, "file3.pdb")  # Should be preserved
        with open(file1, "w") as f:
            f.write("Test file 1")
        with open(file2, "w") as f:
            f.write("Test file 2")
        with open(file3, "w") as f:
            f.write("Test file 3")
        
        # Clean up with default patterns
        manager.cleanup_current()
        
        # Check that only preserved files remain
        self.assertFalse(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))
        self.assertTrue(os.path.exists(file3))  # PDB file should be preserved
    
    def test_get_workspace_path(self):
        """Test getting workspace paths."""
        # Create workspace manager
        manager = WorkspaceManager(base_path=self.test_dir)
        workspace_path = manager.create_workspace("test_workspace")
        
        # Get workspace paths
        self.assertEqual(workspace_path, manager.get_workspace_path())
        self.assertEqual(os.path.join(workspace_path, "test.txt"), 
                       manager.get_workspace_path("test.txt"))
    
    def test_context_manager(self):
        """Test using workspace manager as a context manager."""
        # Use context manager
        with WorkspaceManager(base_path=self.test_dir) as manager:
            # Create a file in the workspace
            workspace_path = manager.current_workspace
            file_path = os.path.join(workspace_path, "test.txt")
            with open(file_path, "w") as f:
                f.write("Test file")
            
            # Track the file
            manager.track_file(file_path)
            
            # Check that file exists
            self.assertTrue(os.path.exists(file_path))
        
        # After context exit, workspace should be cleaned up
        self.assertFalse(os.path.exists(file_path))

# Mock implementation of BaseExternalTool for testing
class MockExternalTool(BaseExternalTool):
    """Mock implementation of BaseExternalTool for testing."""
    
    def _get_tool_name(self):
        return "mock_tool"
    
    def validate_inputs(self, **kwargs):
        # Always valid for testing
        pass
    
    def prepare_inputs(self, workspace_path, **kwargs):
        # Create a test input file
        input_file = os.path.join(workspace_path, "input.txt")
        with open(input_file, "w") as f:
            f.write("Test input")
        return {"input_file": input_file}
    
    def build_command(self, input_info, **kwargs):
        # Build a simple echo command
        return ["echo", "Hello from mock tool"]
    
    def process_output(self, return_code, stdout, stderr, input_info, **kwargs):
        # Create a mock output file
        workspace_path = os.path.dirname(input_info["input_file"])
        output_file = os.path.join(workspace_path, "output.txt")
        with open(output_file, "w") as f:
            f.write(stdout)
        
        return {
            "return_code": return_code,
            "stdout": stdout,
            "stderr": stderr,
            "output_files": [output_file]
        }

class TestBaseExternalTool(unittest.TestCase):
    """Tests for the BaseExternalTool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Patch find_executable to return a mock path
        self.find_executable_patcher = mock.patch(
            "moltools.external_tools.utils.find_executable", 
            return_value="/usr/bin/mock_tool"
        )
        self.mock_find_executable = self.find_executable_patcher.start()
        
        # Patch run_process to return a successful result
        self.run_process_patcher = mock.patch(
            "moltools.external_tools.utils.run_process",
            return_value=(0, "Mock output", "")
        )
        self.mock_run_process = self.run_process_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
        # Stop patches
        self.find_executable_patcher.stop()
        self.run_process_patcher.stop()
    
    def test_tool_execution(self):
        """Test the execute method of BaseExternalTool."""
        # Create workspace manager
        workspace_manager = WorkspaceManager(base_path=self.test_dir)
        
        # Create and execute the mock tool
        tool = MockExternalTool(workspace_manager=workspace_manager)
        result = tool.execute(param1="value1", param2="value2")
        
        # Check that the tool was executed correctly
        self.assertEqual(0, result["return_code"])
        self.assertEqual("Mock output", result["stdout"])
        self.assertEqual("", result["stderr"])
        self.assertEqual(1, len(result["output_files"]))
        
        # Check that workspace management was used
        self.assertIsNotNone(workspace_manager.current_workspace)
        
        # Check that run_process was called
        self.mock_run_process.assert_called_once()
    
    def test_context_manager(self):
        """Test using BaseExternalTool as a context manager."""
        # Create workspace manager
        workspace_manager = WorkspaceManager(base_path=self.test_dir)
        
        # Use tool as context manager
        with MockExternalTool(workspace_manager=workspace_manager) as tool:
            # Execute the tool
            result = tool.execute()
            
            # Check result
            self.assertEqual(0, result["return_code"])
            
            # Check that workspace exists
            self.assertTrue(os.path.exists(workspace_manager.current_workspace))
        
        # After context exit, workspace should be cleaned up
        self.assertFalse(os.path.exists(workspace_manager.current_workspace))

if __name__ == "__main__":
    unittest.main()