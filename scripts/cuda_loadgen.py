#!/usr/bin/env python3
"""GPU load generator for testing cubestat GPU monitoring.

This script generates artificial load on GPUs to test monitoring functionality.
Works with single or multiple GPUs.
"""

import argparse
import sys
import time

import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn.parallel import DataParallel


class SimpleModel(nn.Module):
    """Simple neural network model for generating GPU load."""
    
    def __init__(self, size=1000):
        super(SimpleModel, self).__init__()
        self.fc1 = nn.Linear(size, size)
        self.fc2 = nn.Linear(size, size)
        self.fc3 = nn.Linear(size, size)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        return self.fc3(x)


def get_gpu_info():
    """Get information about available GPUs."""
    if not torch.cuda.is_available():
        return []
    
    gpu_info = []
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        gpu_info.append({
            'index': i,
            'name': props.name,
            'memory': props.total_memory // (1024**3),  # Convert to GB
        })
    return gpu_info


def generate_load(gpu_ids=None, duration=60, batch_size=64, model_size=1000, 
                  memory_fraction=0.5, iterations_per_second=10):
    """Generate load on specified GPUs.
    
    Args:
        gpu_ids: List of GPU IDs to use (None for all GPUs)
        duration: How long to run in seconds
        batch_size: Batch size for the model
        model_size: Size of the model layers
        memory_fraction: Fraction of GPU memory to use (0-1)
        iterations_per_second: Target iterations per second
    """
    gpu_info = get_gpu_info()
    if not gpu_info:
        print("No CUDA GPUs available!")
        return
    
    # Determine which GPUs to use
    if gpu_ids is None:
        gpu_ids = list(range(len(gpu_info)))
    else:
        # Validate GPU IDs
        invalid_ids = [gid for gid in gpu_ids if gid >= len(gpu_info)]
        if invalid_ids:
            print(f"Invalid GPU IDs: {invalid_ids}. Available GPUs: 0-{len(gpu_info)-1}")
            return
    
    print(f"Using GPU(s): {gpu_ids}")
    for gid in gpu_ids:
        info = gpu_info[gid]
        print(f"  GPU {gid}: {info['name']} ({info['memory']} GB)")
    
    # Set the primary device
    torch.cuda.set_device(gpu_ids[0])
    
    # Create model
    model = SimpleModel(model_size).cuda(gpu_ids[0])
    
    # Use DataParallel if multiple GPUs
    if len(gpu_ids) > 1:
        model = DataParallel(model, device_ids=gpu_ids)
        print(f"Using DataParallel across {len(gpu_ids)} GPUs")
    
    # Allocate memory to reach target memory usage
    dummy_tensors = []  # Keep references to prevent garbage collection
    if memory_fraction > 0:
        for gid in gpu_ids:
            with torch.cuda.device(gid):
                # Get available memory
                free_mem = torch.cuda.mem_get_info(gid)[0]
                # Allocate tensor to use specified fraction
                alloc_size = int(free_mem * memory_fraction / 4)  # 4 bytes per float32
                dummy_tensor = torch.randn(alloc_size, device=f'cuda:{gid}')
                dummy_tensors.append(dummy_tensor)
                print(f"  GPU {gid}: Allocated {alloc_size * 4 / (1024**3):.1f} GB")
    
    # Create data and optimizer
    input_data = torch.randn(batch_size, model_size).cuda(gpu_ids[0])
    target_data = torch.randn(batch_size, model_size).cuda(gpu_ids[0])
    criterion = nn.MSELoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001)
    
    # Run load generation
    print(f"\nGenerating load for {duration} seconds...")
    print("Press Ctrl+C to stop early\n")
    
    start_time = time.time()
    iteration = 0
    target_sleep = 1.0 / iterations_per_second if iterations_per_second > 0 else 0
    
    try:
        while True:
            iter_start = time.time()
            
            # Forward and backward pass
            optimizer.zero_grad()
            outputs = model(input_data)
            loss = criterion(outputs, target_data)
            loss.backward()
            optimizer.step()
            
            # Print progress
            iteration += 1
            elapsed = time.time() - start_time
            if iteration % iterations_per_second == 0:
                print(f"Time: {elapsed:.1f}s, Iteration: {iteration}, Loss: {loss.item():.4f}")
            
            # Check if we should stop
            if elapsed >= duration:
                break
            
            # Control iteration rate
            if target_sleep > 0:
                iter_time = time.time() - iter_start
                sleep_time = max(0, target_sleep - iter_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    print(f"\nCompleted {iteration} iterations in {time.time() - start_time:.1f} seconds")


def main():
    parser = argparse.ArgumentParser(
        description='Generate load on GPUs for testing monitoring tools',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--gpus', type=int, nargs='+', default=None,
                        help='GPU IDs to use (e.g., --gpus 0 1). Default: all GPUs')
    parser.add_argument('--duration', type=int, default=60,
                        help='Duration in seconds')
    parser.add_argument('--batch-size', type=int, default=64,
                        help='Batch size for the model')
    parser.add_argument('--model-size', type=int, default=1000,
                        help='Size of model layers')
    parser.add_argument('--memory-fraction', type=float, default=0.5,
                        help='Fraction of GPU memory to use (0-1)')
    parser.add_argument('--iterations-per-second', type=int, default=10,
                        help='Target iterations per second (0 for max speed)')
    parser.add_argument('--list-gpus', action='store_true',
                        help='List available GPUs and exit')
    
    args = parser.parse_args()
    
    # Check for CUDA availability
    if not torch.cuda.is_available():
        print("CUDA is not available. Please check your PyTorch installation.")
        sys.exit(1)
    
    # List GPUs if requested
    if args.list_gpus:
        gpu_info = get_gpu_info()
        if not gpu_info:
            print("No CUDA GPUs found")
        else:
            print("Available GPUs:")
            for info in gpu_info:
                print(f"  GPU {info['index']}: {info['name']} ({info['memory']} GB)")
        return
    
    # Validate memory fraction
    if not 0 <= args.memory_fraction <= 1:
        print("Error: memory-fraction must be between 0 and 1")
        sys.exit(1)
    
    # Generate load
    generate_load(
        gpu_ids=args.gpus,
        duration=args.duration,
        batch_size=args.batch_size,
        model_size=args.model_size,
        memory_fraction=args.memory_fraction,
        iterations_per_second=args.iterations_per_second
    )


if __name__ == '__main__':
    main()