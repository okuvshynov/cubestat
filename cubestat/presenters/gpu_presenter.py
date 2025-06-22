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

    @classmethod
    def collector_id(cls) -> str:
        return "gpu"

    def configure(self, config) -> "GPUPresenter":
        """Configure GPU display mode."""
        # Handle both Dict and Namespace objects
        if hasattr(config, "get"):
            mode_value = config.get("gpu", GPUMode.load_only)
        else:
            mode_value = getattr(config, "gpu", GPUMode.load_only)

        # Ensure we have a proper GPUMode enum, not a string
        if isinstance(mode_value, str):
            self.mode = GPUMode(mode_value)
        else:
            self.mode = mode_value
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
        """Convert collector data to display format with proper titles."""
        result = {}
        
        # Extract metadata
        self.n_gpus = raw_data.get("_n_gpus", 0)
        total_util = raw_data.get("_total_util", 0.0)
        
        # Handle multi-GPU total first
        if self.n_gpus > 1:
            result[f"[{self.n_gpus}] Total GPU util %"] = total_util
        
        # Process individual GPU metrics
        for key, value in raw_data.items():
            if key.startswith("_"):  # Skip metadata
                continue
                
            # Parse GPU metrics and convert to display format
            if "_gpu_" in key:
                # Format: VENDOR_gpu_INDEX_METRIC
                parts = key.split("_")
                if len(parts) >= 4:
                    vendor = parts[0]
                    gpu_index = parts[2]
                    metric_type = "_".join(parts[3:])
                    
                    if metric_type == "util":
                        result[f"{vendor} GPU {gpu_index} util %"] = value
                    elif metric_type == "vram_used_percent":
                        result[f"{vendor} GPU {gpu_index} vram used %"] = value
            elif key == "gpu_util":  # macOS format
                result["GPU util %"] = value
        
        return result