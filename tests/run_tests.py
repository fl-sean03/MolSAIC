#!/usr/bin/env python3
"""
Script to run all MolTools tests.
"""

import unittest
import sys
import os

if __name__ == "__main__":
    # Change to project root directory if script is run from tests directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(script_dir) == "tests":
        os.chdir(os.path.dirname(script_dir))
    
    # Add the parent directory to the path so tests can import the package
    sys.path.insert(0, os.path.abspath(os.path.curdir))
    
    # Discover and run all tests
    unittest.main(module=None, argv=['run_tests.py', 'discover', '-s', 'tests'])