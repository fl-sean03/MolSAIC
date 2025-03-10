#!/bin/bash
# Run all integration tests for MolSAIC
# This script runs all the integration tests and benchmarks for the MolSAIC package

# Exit on error
set -e

# Change to project root directory if script is run from tests directory
if [[ $(basename $(pwd)) == "tests" ]]; then
    cd ..
fi

echo "===================="
echo "Running integration tests"
echo "===================="

# Create test output directory if it doesn't exist
mkdir -p test_outputs

# Run integration tests
echo "Running pipeline integration tests..."
python -m unittest tests/test_pipeline_integration.py

echo ""
echo "===================="
echo "Running benchmarks"
echo "===================="

# Create benchmark directory if it doesn't exist
mkdir -p benchmarks

echo "Running performance comparison benchmark..."
python benchmarks/performance_comparison.py

echo ""
echo "===================="
echo "Running file vs object examples"
echo "===================="

# Create example output directory if it doesn't exist
mkdir -p examples/outputs

echo "Running file vs object approach example..."
python examples/legacy/file_vs_object_approach.py

echo "Running pipeline example..."
python examples/advanced/pipeline_example.py

echo ""
echo "All tests completed successfully!"