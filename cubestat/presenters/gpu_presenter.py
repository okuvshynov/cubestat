from argparse import ArgumentParser
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cubestat.common import DisplayMode
from cubestat.metrics_registry import presenter_registry
from cubestat.presenters.base_presenter import BasePresenter


class GPUMode(DisplayMode):
    collapsed = "collapsed"
    load_only = "load_only"
    load_and_vram = "load_and_vram"


@presenter_registry.register
class GPUPresenter(BasePresenter):
    """GPU presenter handling complex display modes and multi-vendor formatting."""

    def __init__(self):
        self.mode = GPUMode.load_only
        self.n_gpus = 0

    @classmethod
    def key(cls) -> str:
        return "gpu"


    def configure(self, config) -> "GPUPresenter":
        """Configure GPU display mode."""
        self.mode = getattr(config, "gpu", GPUMode.load_only)
        return self

    def pre(self, title: str) -> Tuple[bool, str]:
        """Filter GPU metrics based on display mode."""
        if self.n_gpus > 0 and self.mode == GPUMode.collapsed and "Total GPU" not in title:
            return False, ""
        if self.mode == GPUMode.load_only and "vram" in title:
            return False, ""
        if self.n_gpus > 1 and "Total GPU" not in title:
            return True, "  "
        return True, ""

    def format(
        self, title: str, values: Sequence[float], idxs: Sequence[int]
    ) -> Tuple[float, List[str]]:
        """Format GPU utilization values as percentages."""
        return 100.0, [f"{values[i]:3.0f}%" for i in idxs]

    def hotkey(self) -> Optional[str]:
        """Return hotkey for GPU metric."""
        return "g"

    @classmethod
    def configure_argparse(cls, parser: ArgumentParser) -> None:
        """Configure command-line arguments."""
        parser.add_argument(
            "--gpu",
            type=GPUMode,
            default=GPUMode.load_only,
            choices=list(GPUMode),
            help='GPU mode - hidden, load, or load and vram usage. Hotkey: "g"',
        )

    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Process GPU data from collector."""
        result = {}
        
        # Check if we have standardized metrics (from collector)
        has_standardized = any(k.startswith("gpu.") for k in raw_data.keys())
        
        if has_standardized:
            # Handle standardized metric names directly
            gpu_devices = {}
            gpu_total_count = raw_data.get("gpu.total.count", 0)
            gpu_total_util = raw_data.get("gpu.total.utilization.percent", 0.0)

            # First pass: collect all GPU metrics by vendor and device
            for key, value in raw_data.items():
                if key.startswith("gpu.") and key not in [
                    "gpu.total.count",
                    "gpu.total.utilization.percent",
                ]:
                    parts = key.split(".")
                    if len(parts) >= 5:
                        # gpu.vendor.device_id.metric.unit
                        vendor = parts[1]
                        device_id = parts[2]
                        metric_type = parts[3]

                        device_key = f"{vendor}.{device_id}"
                        if device_key not in gpu_devices:
                            gpu_devices[device_key] = {}

                        if metric_type == "utilization":
                            gpu_devices[device_key]["util"] = value
                            gpu_devices[device_key]["vendor"] = vendor.upper()
                            gpu_devices[device_key]["id"] = device_id
                        elif metric_type == "memory":
                            gpu_devices[device_key]["vram_used_percent"] = value

            # Store GPU count for display filtering
            self.n_gpus = gpu_total_count

            # Add multi-GPU total if needed
            if gpu_total_count > 1:
                result[f"[{gpu_total_count}] Total GPU util %"] = gpu_total_util

            # Second pass: output GPUs in order by vendor then device ID
            for device_key in sorted(gpu_devices.keys()):
                device = gpu_devices[device_key]
                vendor = device.get("vendor", "")
                device_id = device.get("id", "")

                # Handle special case for macOS single GPU
                if vendor == "APPLE":
                    if "util" in device:
                        result["GPU util %"] = device["util"]
                else:
                    # Multi-vendor format
                    if "util" in device:
                        result[f"{vendor} GPU {device_id} util %"] = device["util"]
                    if "vram_used_percent" in device:
                        result[f"{vendor} GPU {device_id} vram used %"] = device[
                            "vram_used_percent"
                        ]
        else:
            # Legacy support for pre-transformed data (backward compatibility)
            # Extract GPU count for display filtering
            self.n_gpus = raw_data.get("_n_gpus", 0)
            
            # Filter out metadata keys and pass through transformed data
            result = {k: v for k, v in raw_data.items() if not k.startswith("_")}

        return result
