# Creating Load Generators

This tutorial shows how to create load generator scripts to test cubestat visualizations and explore different system performance scenarios.

## Step 1: Create a new script

Create a new file in the `scripts` directory, for example, `load_generator.py`:

```python
#!/usr/bin/env python3
"""
Load generator for testing cubestat visualizations.

This script generates artificial system load to test cubestat's 
visualization capabilities.
"""

import argparse
import time
import os
import random
import multiprocessing
from typing import List, Callable

def cpu_load(duration: int, intensity: float = 1.0) -> None:
    """Generate CPU load.
    
    Args:
        duration: Duration in seconds
        intensity: Load intensity (0.0-1.0)
    """
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Adjust work/sleep ratio based on intensity
        work_time = intensity * 0.01  # 10ms at full intensity
        sleep_time = 0.01 - work_time
        
        # Generate CPU load
        start = time.time()
        while time.time() - start < work_time:
            # Busy loop to generate CPU load
            x = 0
            for i in range(1000):
                x += i * i
        
        # Sleep to achieve desired intensity
        if sleep_time > 0:
            time.sleep(sleep_time)

def memory_load(duration: int, size_mb: int) -> None:
    """Allocate memory to test memory metrics.
    
    Args:
        duration: Duration in seconds
        size_mb: Memory to allocate in MB
    """
    # Allocate memory (size_mb megabytes)
    data = bytearray(size_mb * 1024 * 1024)
    
    # Touch the memory to ensure it's actually allocated
    for i in range(0, len(data), 4096):
        data[i] = 1
    
    # Hold the allocation for the specified duration
    time.sleep(duration)
    
    # Return the memory (garbage collection will free it)

def disk_load(duration: int, size_mb: int, path: str = "/tmp") -> None:
    """Generate disk I/O load.
    
    Args:
        duration: Duration in seconds
        size_mb: File size in MB
        path: Directory to write to
    """
    filename = os.path.join(path, f"cubestat_test_{os.getpid()}.tmp")
    chunk_size = 1024 * 1024  # 1MB chunks
    
    try:
        # Write to disk
        with open(filename, "wb") as f:
            for _ in range(size_mb):
                f.write(os.urandom(chunk_size))
                f.flush()
                time.sleep(0.1)  # Control write speed
        
        # Read from disk
        with open(filename, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                time.sleep(0.1)  # Control read speed
    
    finally:
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)

def network_load(duration: int, size_mb: int) -> None:
    """Simulate network load (actual traffic not generated).
    
    Args:
        duration: Duration in seconds
        size_mb: Amount of "network" data to process
    """
    chunk_size = 1024 * 1024  # 1MB chunks
    
    for _ in range(size_mb):
        # Process a chunk of data (simulate network activity)
        data = os.urandom(chunk_size)
        # Do something with the data
        _ = len(data)
        time.sleep(0.5)  # Control "network" speed

def run_load_pattern(pattern: List[Callable], duration: int) -> None:
    """Run a load pattern with multiple load generators.
    
    Args:
        pattern: List of load generator functions to run
        duration: Total duration in seconds
    """
    processes = []
    
    # Start all load generators
    for load_func in pattern:
        p = multiprocessing.Process(target=load_func)
        p.start()
        processes.append(p)
    
    # Wait for the specified duration
    time.sleep(duration)
    
    # Terminate all processes
    for p in processes:
        p.terminate()
        p.join()

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate system load for testing cubestat")
    
    parser.add_argument("--duration", type=int, default=60,
                       help="Duration in seconds")
    parser.add_argument("--cpu", type=float, default=0.7,
                       help="CPU load intensity (0.0-1.0)")
    parser.add_argument("--memory", type=int, default=500,
                       help="Memory to allocate in MB")
    parser.add_argument("--disk", type=int, default=100,
                       help="Disk I/O in MB")
    parser.add_argument("--cores", type=int, default=multiprocessing.cpu_count(),
                       help="Number of CPU cores to use")
    
    args = parser.parse_args()
    
    print(f"Generating load for {args.duration} seconds...")
    
    # Create load pattern
    pattern = []
    
    # Add CPU load generators
    for _ in range(args.cores):
        pattern.append(lambda: cpu_load(args.duration, args.cpu))
    
    # Add memory load
    pattern.append(lambda: memory_load(args.duration, args.memory))
    
    # Add disk load
    pattern.append(lambda: disk_load(args.duration, args.disk))
    
    # Add network load simulation
    pattern.append(lambda: network_load(args.duration, args.disk))
    
    # Run the load pattern
    run_load_pattern(pattern, args.duration)
    
    print("Load generation complete.")

if __name__ == "__main__":
    main()
```

## Step 2: Make the script executable

```bash
chmod +x scripts/load_generator.py
```

## Step 3: Run cubestat with the load generator

Open two terminal windows. In the first, start cubestat:

```bash
cubestat
```

In the second, run the load generator:

```bash
python scripts/load_generator.py --duration 30 --cpu 0.8 --memory 1000 --disk 200
```

This will generate a 30-second load pattern that exercises CPU, memory, and disk metrics, allowing you to observe how cubestat visualizes the load.

## Step 4: Experiment with different load patterns

Create different load patterns to test specific aspects of your system:

```bash
# High CPU load
python scripts/load_generator.py --duration 20 --cpu 1.0 --memory 100 --disk 50

# High memory load
python scripts/load_generator.py --duration 20 --cpu 0.3 --memory 2000 --disk 50

# High disk I/O
python scripts/load_generator.py --duration 20 --cpu 0.3 --memory 100 --disk 500
```

## Creating a CUDA GPU Load Generator

For systems with NVIDIA GPUs, you can create a CUDA load generator:

```python
#!/usr/bin/env python3
"""
CUDA GPU load generator for testing cubestat.

This script generates artificial GPU load to test cubestat's 
GPU monitoring capabilities.

Requirements:
- CUDA toolkit
- pycuda package
"""

import argparse
import time
import numpy as np
import threading

try:
    import pycuda.driver as cuda
    import pycuda.autoinit
    from pycuda.compiler import SourceModule
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False

# CUDA kernel for matrix multiplication
CUDA_KERNEL = """
__global__ void matrix_mul(float *a, float *b, float *c, int width)
{
    int tx = threadIdx.x + blockIdx.x * blockDim.x;
    int ty = threadIdx.y + blockIdx.y * blockDim.y;
    
    if (tx < width && ty < width) {
        float value = 0;
        for (int k = 0; k < width; ++k) {
            value += a[ty * width + k] * b[k * width + tx];
        }
        c[ty * width + tx] = value;
    }
}
"""

def gpu_load(duration: int, intensity: float = 1.0, matrix_size: int = 1024) -> None:
    """Generate GPU load using CUDA.
    
    Args:
        duration: Duration in seconds
        intensity: Load intensity (0.0-1.0)
        matrix_size: Size of matrices for multiplication
    """
    if not CUDA_AVAILABLE:
        print("CUDA not available. Please install pycuda.")
        return
    
    # Compile the CUDA kernel
    mod = SourceModule(CUDA_KERNEL)
    matrix_mul = mod.get_function("matrix_mul")
    
    # Prepare data
    a = np.random.randn(matrix_size, matrix_size).astype(np.float32)
    b = np.random.randn(matrix_size, matrix_size).astype(np.float32)
    c = np.zeros((matrix_size, matrix_size), dtype=np.float32)
    
    # Copy data to GPU
    a_gpu = cuda.mem_alloc(a.nbytes)
    b_gpu = cuda.mem_alloc(b.nbytes)
    c_gpu = cuda.mem_alloc(c.nbytes)
    
    cuda.memcpy_htod(a_gpu, a)
    cuda.memcpy_htod(b_gpu, b)
    
    # Configure grid and block dimensions
    block_size = (16, 16, 1)
    grid_size = (
        (matrix_size + block_size[0] - 1) // block_size[0],
        (matrix_size + block_size[1] - 1) // block_size[1],
        1
    )
    
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Calculate work and sleep time based on intensity
        work_time = intensity * 0.5  # 500ms at full intensity
        sleep_time = 0.5 - work_time
        
        # Generate GPU load
        start = time.time()
        while time.time() - start < work_time:
            matrix_mul(
                a_gpu, b_gpu, c_gpu, np.int32(matrix_size),
                block=block_size, grid=grid_size
            )
            
        # Sleep to achieve desired intensity
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    # Clean up
    a_gpu.free()
    b_gpu.free()
    c_gpu.free()

def run_gpu_load(duration: int, intensity: float, gpu_count: int) -> None:
    """Run GPU load on multiple GPUs.
    
    Args:
        duration: Duration in seconds
        intensity: Load intensity (0.0-1.0)
        gpu_count: Number of GPUs to use
    """
    if not CUDA_AVAILABLE:
        print("CUDA not available. Please install pycuda.")
        return
    
    threads = []
    
    # Start a thread for each GPU
    for i in range(min(gpu_count, cuda.Device.count())):
        thread = threading.Thread(
            target=lambda: gpu_load(duration, intensity)
        )
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate GPU load for testing cubestat")
    
    parser.add_argument("--duration", type=int, default=60,
                       help="Duration in seconds")
    parser.add_argument("--intensity", type=float, default=0.8,
                       help="GPU load intensity (0.0-1.0)")
    parser.add_argument("--gpus", type=int, default=1,
                       help="Number of GPUs to use")
    
    args = parser.parse_args()
    
    if not CUDA_AVAILABLE:
        print("CUDA not available. Please install pycuda.")
        return
    
    available_gpus = cuda.Device.count()
    gpu_count = min(args.gpus, available_gpus)
    
    print(f"Found {available_gpus} CUDA-capable GPU(s)")
    print(f"Generating load on {gpu_count} GPU(s) for {args.duration} seconds...")
    
    run_gpu_load(args.duration, args.intensity, gpu_count)
    
    print("GPU load generation complete.")

if __name__ == "__main__":
    main()
```

## Creating a Variable Load Generator

For more realistic testing, you might want to create a load generator that varies the load over time:

```python
def variable_cpu_load(duration: int, min_intensity: float = 0.2, max_intensity: float = 1.0) -> None:
    """Generate variable CPU load with a sine wave pattern.
    
    Args:
        duration: Duration in seconds
        min_intensity: Minimum load intensity
        max_intensity: Maximum load intensity
    """
    start_time = time.time()
    end_time = start_time + duration
    
    while time.time() < end_time:
        # Calculate elapsed time
        elapsed = time.time() - start_time
        
        # Calculate current intensity using a sine wave pattern
        # This creates a wave that oscillates between min and max intensity
        intensity_range = max_intensity - min_intensity
        intensity = min_intensity + intensity_range * (
            0.5 + 0.5 * math.sin(elapsed * math.pi / 10)  # 20-second cycle
        )
        
        # Adjust work/sleep ratio based on intensity
        work_time = intensity * 0.01  # 10ms at full intensity
        sleep_time = 0.01 - work_time
        
        # Generate CPU load
        start = time.time()
        while time.time() - start < work_time:
            # Busy loop to generate CPU load
            x = 0
            for i in range(1000):
                x += i * i
        
        # Sleep to achieve desired intensity
        if sleep_time > 0:
            time.sleep(sleep_time)
```

## Load Pattern Presets

Add presets for common testing scenarios:

```python
# Define preset load patterns
PRESETS = {
    "idle": {
        "cpu": 0.1,
        "memory": 100,
        "disk": 10,
        "cores": 1
    },
    "light": {
        "cpu": 0.3,
        "memory": 500,
        "disk": 50,
        "cores": 2
    },
    "moderate": {
        "cpu": 0.5,
        "memory": 1000,
        "disk": 100,
        "cores": 4
    },
    "heavy": {
        "cpu": 0.8,
        "memory": 2000,
        "disk": 200,
        "cores": multiprocessing.cpu_count()
    },
    "stress": {
        "cpu": 1.0,
        "memory": 3000,
        "disk": 500,
        "cores": multiprocessing.cpu_count()
    }
}

# Update the argument parser to support presets
parser.add_argument("--preset", choices=list(PRESETS.keys()),
                   help="Use a predefined load pattern")

# Apply presets if specified
if args.preset:
    preset = PRESETS[args.preset]
    args.cpu = preset["cpu"]
    args.memory = preset["memory"]
    args.disk = preset["disk"]
    args.cores = preset["cores"]
    print(f"Using '{args.preset}' preset: CPU={args.cpu}, Memory={args.memory}MB, Disk={args.disk}MB, Cores={args.cores}")
```

## Best Practices for Load Testing

1. **Start small**: Begin with low-intensity loads to verify everything works correctly.

2. **Monitor system stability**: Watch for signs of system instability during testing, especially with high loads.

3. **Clean up resources**: Ensure your load generators clean up any allocated resources.

4. **Isolate tests**: Run load tests on a dedicated system to avoid interference with other applications.

5. **Test realistic scenarios**: Design load patterns that mimic real-world usage scenarios.

6. **Test edge cases**: Include tests for both minimum and maximum loads to verify system behavior at extremes.

7. **Script multiple test scenarios**: Create scripts that run multiple load patterns sequentially for automated testing.

## Next Steps

- [Optimizing Data Collection](./optimizing-data-collection.md)
- [Building Custom Visualizations](./building-custom-visualizations.md)
- [Cross-Platform Testing](./cross-platform-testing.md)