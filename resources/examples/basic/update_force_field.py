#!/usr/bin/env python3
"""
Example script demonstrating how to update force-field types in MDF and CAR files.
"""

import argparse
import sys
import json
from pathlib import Path

from molsaic.transformers.update_ff import update_ff_types

def main():
    """Force-field update example main function."""
    parser = argparse.ArgumentParser(
        description="Update force-field types in MDF and CAR files based on charge and element mapping"
    )
    parser.add_argument("--car", help="Input CAR file")
    parser.add_argument("--mdf", help="Input MDF file")
    parser.add_argument("--output-car", help="Output CAR file")
    parser.add_argument("--output-mdf", help="Output MDF file")
    parser.add_argument("--mapping", required=True, help="JSON mapping file")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not (args.car or args.mdf):
        print("Error: At least one of --car or --mdf must be provided")
        sys.exit(1)
    
    if args.car and not args.output_car:
        print("Error: --output-car is required when --car is provided")
        sys.exit(1)
        
    if args.mdf and not args.output_mdf:
        print("Error: --output-mdf is required when --mdf is provided")
        sys.exit(1)
    
    # Print mapping information
    try:
        with open(args.mapping, 'r') as f:
            mapping = json.load(f)
        print(f"Loaded mapping with {len(mapping)} entries:")
        for key, value in list(mapping.items())[:5]:
            print(f"  {key} -> {value}")
        if len(mapping) > 5:
            print(f"  (and {len(mapping) - 5} more...)")
    except Exception as e:
        print(f"Error loading mapping file: {str(e)}")
        sys.exit(1)
    
    # Update force-field types
    results = update_ff_types(
        car_file=args.car,
        mdf_file=args.mdf,
        output_car=args.output_car,
        output_mdf=args.output_mdf,
        mapping_file=args.mapping
    )
    
    # Print results
    if 'car_updates' in results:
        print(f"Updated {results['car_updates']} force-field types in CAR file: {args.output_car}")
    if 'mdf_updates' in results:
        print(f"Updated {results['mdf_updates']} force-field types in MDF file: {args.output_mdf}")
    
if __name__ == "__main__":
    main()