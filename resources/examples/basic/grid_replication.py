#!/usr/bin/env python3
"""
Example script demonstrating grid replication of molecules.
"""

import argparse
import sys
from pathlib import Path

from molsaic.transformers.grid import generate_grid_files

def main():
    """Grid replication example main function."""
    parser = argparse.ArgumentParser(
        description="Generate a grid of replicated molecules from CAR and MDF files"
    )
    parser.add_argument("--car", required=True, help="Input CAR file")
    parser.add_argument("--mdf", required=True, help="Input MDF file")
    parser.add_argument("--output-car", required=True, help="Output CAR file")
    parser.add_argument("--output-mdf", required=True, help="Output MDF file")
    parser.add_argument("--grid", type=int, default=8, help="Grid dimension (default: 8)")
    parser.add_argument("--gap", type=float, default=2.0, help="Gap between molecules in Å (default: 2.0)")
    parser.add_argument("--base-name", default="MOL", help="Base molecule name")
    
    args = parser.parse_args()
    
    # Generate the grid
    generate_grid_files(
        args.car,
        args.mdf,
        args.output_car,
        args.output_mdf,
        grid_dims=(args.grid, args.grid, args.grid),
        gap=args.gap,
        base_name=args.base_name
    )
    
    print(f"Grid replication complete: {args.grid}x{args.grid}x{args.grid} = {args.grid**3} molecules.")
    print(f"Output CAR file: {args.output_car}")
    print(f"Output MDF file: {args.output_mdf}")
    
if __name__ == "__main__":
    main()