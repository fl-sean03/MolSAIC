#!/usr/bin/env python3
"""
Scans the codebase for potentially sensitive information.
This is a simple script to check for common patterns that might indicate
sensitive information before pushing to a public repository.
"""

import os
import re
import sys
from pathlib import Path

# Patterns that might indicate sensitive information
PATTERNS = [
    r'password\s*=\s*[\'"][^\'"]+[\'"]',
    r'api[-_]?key\s*=\s*[\'"][^\'"]+[\'"]',
    r'secret[-_]?key\s*=\s*[\'"][^\'"]+[\'"]',
    r'access[-_]?token\s*=\s*[\'"][^\'"]+[\'"]',
    r'auth[-_]?token\s*=\s*[\'"][^\'"]+[\'"]',
    r'credential\s*=\s*[\'"][^\'"]+[\'"]',
]

# Directories and files to skip
SKIP_DIRS = [
    ".git",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
]

SKIP_FILES = [
    "check_sensitive_info.py",  # This file
]

def check_file(file_path):
    """Check a file for sensitive information patterns."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        try:
            content = file.read()
            line_num = 1
            for line in content.split('\n'):
                for pattern in PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        print(f"Possible sensitive information in {file_path} line {line_num}:")
                        print(f"  {line.strip()}")
                line_num += 1
        except UnicodeDecodeError:
            # Skip binary files
            pass

def scan_directory(directory='.'):
    """Scan directory recursively for sensitive information."""
    for root, dirs, files in os.walk(directory):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if file in SKIP_FILES:
                continue
                
            # Skip non-text files
            if not file.endswith(('.py', '.md', '.txt', '.json', '.yml', '.yaml', '.sh', '.ini', '.cfg')):
                continue
                
            file_path = os.path.join(root, file)
            check_file(file_path)

if __name__ == "__main__":
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    print(f"Scanning {project_root} for sensitive information...")
    scan_directory(project_root)
    print("Scan complete!")