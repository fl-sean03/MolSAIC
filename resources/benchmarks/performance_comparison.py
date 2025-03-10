#!/usr/bin/env python3
"""
Performance benchmark comparing file-based vs object-based approaches.
"""

import os
import time
import logging
import tempfile
import statistics
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import both approaches
from molsaic.transformers.update_ff import update_ff_types
from molsaic.transformers.update_charges import update_charges
from molsaic.transformers.grid import generate_grid_files
from molsaic.pipeline import MolecularPipeline

class Benchmark:
    """Class for benchmarking MolSAIC performance."""
    
    def __init__(self):
        """Initialize benchmark with sample file paths."""
        # Base directory of the project
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Sample file paths
        self.sample_dir = os.path.join(self.base_dir, "samplefiles", "1NEC")
        self.mapping_dir = os.path.join(self.base_dir, "mappings")
        
        self.car_file = os.path.join(self.sample_dir, "NEC_0H.car")
        self.mdf_file = os.path.join(self.sample_dir, "NEC_0H.mdf")
        self.ff_mapping = os.path.join(self.mapping_dir, "charge_to_ff.json")
        self.charge_mapping = os.path.join(self.mapping_dir, "ff_to_charge.json")
        
        # Create temporary directory for outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Grid dimensions for testing
        self.grid_dims = (4, 4, 4)  # Default grid size for benchmarks
    
    def run_file_based(self) -> float:
        """
        Run file-based approach with intermediate files.
        
        Returns:
            float: Execution time in seconds.
        """
        start_time = time.time()
        
        # Step 1: Update force-field types
        ff_output_car = os.path.join(self.temp_dir, "step1.car")
        ff_output_mdf = os.path.join(self.temp_dir, "step1.mdf")
        
        update_ff_types(
            car_file=self.car_file,
            mdf_file=self.mdf_file,
            output_car=ff_output_car,
            output_mdf=ff_output_mdf,
            mapping_file=self.ff_mapping
        )
        
        # Step 2: Update charges
        charge_output_car = os.path.join(self.temp_dir, "step2.car")
        charge_output_mdf = os.path.join(self.temp_dir, "step2.mdf")
        
        update_charges(
            car_file=ff_output_car,
            mdf_file=ff_output_mdf,
            output_car=charge_output_car,
            output_mdf=charge_output_mdf,
            mapping_file=self.charge_mapping
        )
        
        # Step 3: Generate grid
        grid_output_car = os.path.join(self.temp_dir, "file_output.car")
        grid_output_mdf = os.path.join(self.temp_dir, "file_output.mdf")
        
        generate_grid_files(
            car_file=charge_output_car,
            mdf_file=charge_output_mdf,
            output_car=grid_output_car,
            output_mdf=grid_output_mdf,
            grid_dims=self.grid_dims,
            gap=2.0
        )
        
        elapsed = time.time() - start_time
        return elapsed
    
    def run_object_based(self) -> float:
        """
        Run object-based approach with no intermediate files.
        
        Returns:
            float: Execution time in seconds.
        """
        start_time = time.time()
        
        # Output files
        output_car = os.path.join(self.temp_dir, "object_output.car")
        output_mdf = os.path.join(self.temp_dir, "object_output.mdf")
        
        # Use fluent API with method chaining
        (MolecularPipeline()
            .load(self.car_file, self.mdf_file)
            .update_ff_types(self.ff_mapping)
            .update_charges(self.charge_mapping)
            .generate_grid(grid_dims=self.grid_dims, gap=2.0)
            .save(output_car, output_mdf))
        
        elapsed = time.time() - start_time
        return elapsed
    
    def run_benchmark(self, iterations: int = 5) -> Dict[str, Dict[str, float]]:
        """
        Run benchmark comparing both approaches.
        
        Args:
            iterations (int): Number of iterations for each approach.
            
        Returns:
            dict: Dictionary with benchmark results.
        """
        logger.info(f"Running benchmark with {iterations} iterations...")
        
        file_based_times = []
        object_based_times = []
        
        for i in range(iterations):
            logger.info(f"Iteration {i+1}/{iterations}")
            
            # Run file-based approach
            logger.info("Running file-based approach...")
            file_time = self.run_file_based()
            file_based_times.append(file_time)
            logger.info(f"File-based time: {file_time:.3f} seconds")
            
            # Run object-based approach
            logger.info("Running object-based approach...")
            object_time = self.run_object_based()
            object_based_times.append(object_time)
            logger.info(f"Object-based time: {object_time:.3f} seconds")
        
        # Calculate statistics
        file_stats = {
            "min": min(file_based_times),
            "max": max(file_based_times),
            "mean": statistics.mean(file_based_times),
            "median": statistics.median(file_based_times),
            "stdev": statistics.stdev(file_based_times) if len(file_based_times) > 1 else 0,
            "times": file_based_times
        }
        
        object_stats = {
            "min": min(object_based_times),
            "max": max(object_based_times),
            "mean": statistics.mean(object_based_times),
            "median": statistics.median(object_based_times),
            "stdev": statistics.stdev(object_based_times) if len(object_based_times) > 1 else 0,
            "times": object_based_times
        }
        
        return {
            "file_based": file_stats,
            "object_based": object_stats
        }
    
    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
        logger.info(f"Cleaned up temporary directory: {self.temp_dir}")

def print_results(results: Dict[str, Dict[str, float]]):
    """
    Print benchmark results in a formatted table.
    
    Args:
        results (dict): Dictionary with benchmark results.
    """
    file_stats = results["file_based"]
    object_stats = results["object_based"]
    
    # Calculate speedup factor
    speedup = file_stats["mean"] / object_stats["mean"]
    
    print("\n" + "=" * 80)
    print(f"PERFORMANCE COMPARISON (Grid dimensions: {benchmark.grid_dims})")
    print("=" * 80)
    print(f"{'Approach':<15} {'Min (s)':<10} {'Max (s)':<10} {'Mean (s)':<10} {'Median (s)':<10} {'StdDev':<10}")
    print("-" * 80)
    print(f"{'File-based':<15} {file_stats['min']:<10.3f} {file_stats['max']:<10.3f} "
          f"{file_stats['mean']:<10.3f} {file_stats['median']:<10.3f} {file_stats['stdev']:<10.3f}")
    print(f"{'Object-based':<15} {object_stats['min']:<10.3f} {object_stats['max']:<10.3f} "
          f"{object_stats['mean']:<10.3f} {object_stats['median']:<10.3f} {object_stats['stdev']:<10.3f}")
    print("-" * 80)
    print(f"Speedup factor: {speedup:.2f}x (file-based time / object-based time)")
    print("=" * 80)
    
    # Print individual iteration times
    print("\nIndividual run times (seconds):")
    print("-" * 40)
    print(f"{'Iteration':<10} {'File-based':<15} {'Object-based':<15}")
    for i, (file_time, object_time) in enumerate(zip(file_stats["times"], object_stats["times"])):
        print(f"{i+1:<10} {file_time:<15.3f} {object_time:<15.3f}")
    
    print("\nAnalysis:")
    if speedup > 1:
        print(f"- The object-based approach is {speedup:.2f}x faster on average")
        print("- This is because the object-based approach avoids intermediate file I/O")
        print("- For multiple transformations, the performance gap widens with more steps")
    elif speedup < 1:
        print(f"- The file-based approach is {1/speedup:.2f}x faster on average")
        print("- This could be due to overhead in the object model or implementation details")
    else:
        print("- Both approaches perform similarly on this benchmark")

if __name__ == "__main__":
    benchmark = Benchmark()
    
    try:
        # Run benchmark with 3 iterations
        results = benchmark.run_benchmark(iterations=3)
        
        # Print results
        print_results(results)
    
    finally:
        # Clean up temporary files
        benchmark.cleanup()