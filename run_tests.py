#!/usr/bin/env python3
"""
Script to run all MolTools tests.
"""

import unittest
import sys
import os

if __name__ == "__main__":
    # Add the parent directory to the path so tests can import the package
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Discover and run all tests
    unittest.main(module=None, argv=['run_tests.py', 'discover', '-s', 'tests'])