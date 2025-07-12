#!/usr/bin/env python3
"""
Performance benchmark script for NC Parser multithreading
"""
import time
import subprocess
import sys
import os

def run_benchmark(file_path, threads, resolution=1.0):
    """Run a benchmark with specified parameters."""
    print(f"\n=== Benchmark: {threads} threads, resolution {resolution} ===")
    
    start_time = time.time()
    
    try:
        cmd = [
            sys.executable, "main.py", file_path,
            "--threads", str(threads),
            "--fast",
            "--no-viz",
            "--resolution", str(resolution)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            # Extract performance info from output
            lines = result.stdout.split('\n')
            path_time = None
            material_time = None
            total_commands = None
            total_points = None
            
            for line in lines:
                if "Path calculation completed in" in line:
                    path_time = float(line.split("in ")[1].split("s")[0])
                elif "Material removal completed in" in line:
                    material_time = float(line.split("in ")[1].split("s")[0])
                elif "Found " in line and "total commands" in line:
                    total_commands = int(line.split("Found ")[1].split(" total")[0])
                elif "Generated " in line and "tool path points" in line:
                    total_points = int(line.split("Generated ")[1].split(" tool")[0])
            
            print(f"Total time: {elapsed:.2f}s")
            if path_time:
                print(f"Path calculation: {path_time:.2f}s")
            if material_time:
                print(f"Material removal: {material_time:.2f}s")
            if total_commands:
                print(f"Commands processed: {total_commands:,}")
            if total_points:
                print(f"Points generated: {total_points:,}")
                if total_commands:
                    print(f"Commands/second: {total_commands/elapsed:.0f}")
                    print(f"Points/second: {total_points/elapsed:.0f}")
            
            return elapsed, path_time, material_time
        else:
            print(f"Error: {result.stderr}")
            return None, None, None
            
    except subprocess.TimeoutExpired:
        print("Benchmark timed out (5 minutes)")
        return None, None, None
    except Exception as e:
        print(f"Benchmark failed: {e}")
        return None, None, None

def main():
    """Run performance benchmarks."""
    print("NC Parser Multithreading Performance Benchmark")
    print("=" * 50)
    
    # Check if sample file exists
    test_file = "sample_nc_file.H"
    if not os.path.exists(test_file):
        print(f"Error: Test file '{test_file}' not found")
        return 1
    
    # Test different thread counts
    thread_counts = [1, 2, 4, 8]
    results = []
    
    for threads in thread_counts:
        total_time, path_time, material_time = run_benchmark(test_file, threads)
        if total_time:
            results.append((threads, total_time, path_time, material_time))
    
    # Summary
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)
    print(f"{'Threads':<8} {'Total':<10} {'Path':<10} {'Material':<10} {'Speedup':<8}")
    print("-" * 50)
    
    baseline_time = None
    for threads, total_time, path_time, material_time in results:
        if baseline_time is None:
            baseline_time = total_time
            speedup = "1.0x"
        else:
            speedup = f"{baseline_time/total_time:.1f}x"
        
        path_str = f"{path_time:.1f}s" if path_time else "N/A"
        material_str = f"{material_time:.1f}s" if material_time else "N/A"
        
        print(f"{threads:<8} {total_time:.1f}s{'':<4} {path_str:<10} {material_str:<10} {speedup:<8}")
    
    print("\nRecommendations:")
    if len(results) >= 2:
        best_threads = min(results, key=lambda x: x[1])[0]
        print(f"- Best performance: {best_threads} threads")
        print(f"- For large files use: --threads {best_threads} --fast")
        print(f"- For quick preview use: --threads {best_threads} --fast --resolution 2.0 --no-viz")

if __name__ == "__main__":
    sys.exit(main())
