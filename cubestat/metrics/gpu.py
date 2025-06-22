import logging
import subprocess
from abc import ABC, abstractmethod
from importlib.util import find_spec
from typing import Any, Dict, List, Sequence, Tuple

from cubestat.common import DisplayMode
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric

# Setup logging
logger = logging.getLogger(__name__)


class GPUMode(DisplayMode):
    collapsed = "collapsed"
    load_only = "load_only"
    load_and_vram = "load_and_vram"


class gpu_metric(base_metric):
    n_gpus: int
    mode: GPUMode

    def pre(self, title: str) -> Tuple[bool, str]:
        """Prepare GPU metric for display.

        Args:
            title: The metric title

        Returns:
            Tuple of (should_display, prefix)
        """
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
        """Format GPU utilization values.

        Args:
            title: The metric title
            values: The metric values
            idxs: Indices to format

        Returns:
            Tuple of (max_value, formatted_values)
        """
        return 100.0, [f"{values[i]:3.0f}%" for i in idxs]

    def configure(self, conf: Any) -> "gpu_metric":
        """Configure the GPU metric.

        Args:
            conf: Configuration object

        Returns:
            The configured metric instance
        """
        self.mode = conf.gpu
        return self

    @classmethod
    def key(cls) -> str:
        """Return the key that identifies this metric."""
        return "gpu"

    def hotkey(self) -> str:
        """Return the hotkey used to toggle this metric's display mode."""
        return "g"

    @classmethod
    def configure_argparse(cls, parser: Any) -> None:
        """Configure command line arguments for this metric.

        Args:
            parser: The argument parser to configure
        """
        parser.add_argument(
            "--gpu",
            type=GPUMode,
            default=GPUMode.load_only,
            choices=list(GPUMode),
            help='GPU mode - hidden, load, or load and vram usage. Hotkey: "g"',
        )


class GPUHandler(ABC):
    """Abstract base class for GPU-specific handlers."""
    
    @abstractmethod
    def __init__(self) -> None:
        """Initialize the GPU handler."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this GPU type is available on the system."""
        pass
    
    @abstractmethod
    def get_gpu_count(self) -> int:
        """Get the number of GPUs of this type."""
        pass
    
    @abstractmethod
    def read_metrics(self) -> Dict[str, float]:
        """Read metrics for all GPUs of this type."""
        pass
    
    @abstractmethod
    def get_vendor_prefix(self) -> str:
        """Get the vendor prefix for GPU naming (e.g., 'NVIDIA', 'AMD')."""
        pass


class NVIDIAGPUHandler(GPUHandler):
    """Handler for NVIDIA GPUs."""
    
    def __init__(self) -> None:
        """Initialize the NVIDIA GPU handler."""
        self.has_nvidia = False
        self.nvsmi = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize NVIDIA GPU support."""
        try:
            subprocess.check_output(["nvidia-smi"], stderr=subprocess.PIPE)
            nvspec = find_spec("pynvml")
            if nvspec is not None:
                try:
                    from pynvml_utils import nvidia_smi
                    self.nvsmi = nvidia_smi.getInstance()
                    self.has_nvidia = True
                    logger.info("NVIDIA GPU monitoring initialized successfully")
                except ImportError as e:
                    logger.warning(f"Failed to import pynvml_utils: {str(e)}")
            else:
                logger.warning("pynvml module not found, NVIDIA GPU monitoring disabled")
        except subprocess.CalledProcessError as e:
            logger.warning(
                f"nvidia-smi command failed: {e.stderr.decode() if e.stderr else 'unknown error'}"
            )
        except FileNotFoundError:
            logger.debug("nvidia-smi not found, NVIDIA GPU monitoring disabled")
        except Exception as e:
            logger.exception(f"Unexpected error initializing NVIDIA GPU metrics: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if NVIDIA GPUs are available."""
        return self.has_nvidia and self.nvsmi is not None
    
    def get_gpu_count(self) -> int:
        """Get the number of NVIDIA GPUs."""
        if not self.is_available():
            return 0
        
        try:
            query_result = self.nvsmi.DeviceQuery("utilization.gpu")
            if query_result and "gpu" in query_result:
                return len(query_result["gpu"])
        except Exception:
            pass
        return 0
    
    def read_metrics(self) -> Dict[str, float]:
        """Read NVIDIA GPU metrics."""
        res: Dict[str, float] = {}
        
        if not self.is_available():
            return res
        
        try:
            query_result = self.nvsmi.DeviceQuery("utilization.gpu,memory.total,memory.used")
            
            if not query_result or "gpu" not in query_result:
                logger.warning("Invalid DeviceQuery result from NVIDIA SMI")
                return res
            
            for i, v in enumerate(query_result["gpu"]):
                try:
                    gpu_util = v["utilization"]["gpu_util"]
                    mem_used = v["fb_memory_usage"]["used"]
                    mem_total = v["fb_memory_usage"]["total"]
                    
                    prefix = self.get_vendor_prefix()
                    res[f"{prefix} GPU {i} util %"] = gpu_util
                    
                    # Protect against division by zero
                    if mem_total > 0:
                        res[f"{prefix} GPU {i} vram used %"] = 100.0 * mem_used / mem_total
                    else:
                        res[f"{prefix} GPU {i} vram used %"] = 0.0
                        logger.warning(f"{prefix} GPU {i} reports zero total memory")
                except KeyError as e:
                    logger.warning(
                        f"Missing key in {self.get_vendor_prefix()} GPU {i} data: {str(e)}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Error processing {self.get_vendor_prefix()} GPU {i} data: {str(e)}"
                    )
        except Exception as e:
            logger.exception(f"Error reading NVIDIA GPU metrics: {str(e)}")
        
        return res
    
    def get_vendor_prefix(self) -> str:
        """Get the vendor prefix for NVIDIA GPUs."""
        return "NVIDIA"


class AMDGPUHandler(GPUHandler):
    """Handler for AMD GPUs."""
    
    def __init__(self) -> None:
        """Initialize the AMD GPU handler."""
        self.has_amd = False
        self.rocml = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize AMD GPU support."""
        try:
            # First check: rocm-smi command available
            subprocess.check_output(["rocm-smi"], stderr=subprocess.PIPE)
            
            # Second check: pyrsmi module available
            rsmi_spec = find_spec("pyrsmi")
            if rsmi_spec is not None:
                try:
                    # Third check: import and initialize pyrsmi
                    import pyrsmi.rocml as rocml
                    
                    rocml.smi_initialize()
                    self.rocml = rocml
                    self.has_amd = True
                    logger.info("AMD ROCm GPU monitoring initialized successfully")
                except ImportError as e:
                    logger.warning(f"Failed to import pyrsmi: {str(e)}")
                except Exception as e:
                    logger.warning(f"Failed to initialize ROCm SMI: {str(e)}")
            else:
                logger.warning("pyrsmi module not found, AMD GPU monitoring disabled")
        except subprocess.CalledProcessError as e:
            logger.warning(
                f"rocm-smi command failed: {e.stderr.decode() if e.stderr else 'unknown error'}"
            )
        except FileNotFoundError:
            logger.debug("rocm-smi not found, AMD GPU monitoring disabled")
        except Exception as e:
            logger.exception(f"Unexpected error initializing AMD GPU metrics: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if AMD GPUs are available."""
        return self.has_amd and self.rocml is not None
    
    def get_gpu_count(self) -> int:
        """Get the number of AMD GPUs."""
        if not self.is_available():
            return 0
        
        try:
            return self.rocml.smi_get_device_count()
        except Exception:
            return 0
    
    def read_metrics(self) -> Dict[str, float]:
        """Read AMD GPU metrics."""
        res: Dict[str, float] = {}
        
        if not self.is_available():
            return res
        
        try:
            device_count = self.rocml.smi_get_device_count()
            
            for i in range(device_count):
                try:
                    # Get GPU utilization percentage
                    gpu_util = self.rocml.smi_get_device_utilization(i)
                    
                    # Get memory usage information
                    mem_used = self.rocml.smi_get_device_memory_used(i)
                    mem_total = self.rocml.smi_get_device_memory_total(i)
                    
                    prefix = self.get_vendor_prefix()
                    res[f"{prefix} GPU {i} util %"] = float(gpu_util)
                    
                    # Protect against division by zero
                    if mem_total > 0:
                        res[f"{prefix} GPU {i} vram used %"] = 100.0 * mem_used / mem_total
                    else:
                        res[f"{prefix} GPU {i} vram used %"] = 0.0
                        logger.warning(f"{prefix} GPU {i} reports zero total memory")
                except Exception as e:
                    logger.warning(
                        f"Error processing {self.get_vendor_prefix()} GPU {i} data: {str(e)}"
                    )
        except Exception as e:
            logger.exception(f"Error reading AMD GPU metrics: {str(e)}")
        
        return res
    
    def get_vendor_prefix(self) -> str:
        """Get the vendor prefix for AMD GPUs."""
        return "AMD"
    
    def __del__(self) -> None:
        """Cleanup ROCm SMI resources."""
        if self.has_amd and self.rocml is not None:
            try:
                self.rocml.smi_shutdown()
            except Exception:
                pass  # Ignore cleanup errors


class MacOSGPUHandler(GPUHandler):
    """Handler for macOS GPUs."""
    
    def __init__(self) -> None:
        """Initialize the macOS GPU handler."""
        self.available = True  # Always available on macOS
    
    def is_available(self) -> bool:
        """Check if macOS GPU is available."""
        return self.available
    
    def get_gpu_count(self) -> int:
        """Get the number of GPUs (always 1 for macOS)."""
        return 1 if self.available else 0
    
    def read_metrics(self) -> Dict[str, float]:
        """Read macOS GPU metrics from context."""
        # Note: This is handled differently in the unified metric
        return {}
    
    def get_vendor_prefix(self) -> str:
        """Get the vendor prefix for macOS GPUs."""
        return "GPU"


@cubestat_metric("linux")
class unified_gpu_metric_linux(gpu_metric):
    """Unified GPU metric for Linux supporting multiple GPU types."""
    
    def __init__(self) -> None:
        """Initialize the unified GPU metric."""
        self.gpu_handlers: List[GPUHandler] = []
        self.n_gpus = 0
        self.gpu_counts: Dict[str, int] = {}
        
        # Try to initialize each GPU type
        for handler_class in [NVIDIAGPUHandler, AMDGPUHandler]:
            try:
                handler = handler_class()
                if handler.is_available():
                    count = handler.get_gpu_count()
                    if count > 0:
                        self.gpu_handlers.append(handler)
                        self.gpu_counts[handler.get_vendor_prefix()] = count
                        self.n_gpus += count
                        logger.info(f"Detected {count} {handler.get_vendor_prefix()} GPU(s)")
            except Exception as e:
                logger.warning(f"Failed to initialize {handler_class.__name__}: {str(e)}")
    
    def read(self, _context: Dict[str, Any]) -> Dict[str, float]:
        """Read metrics from all available GPU types.
        
        Args:
            _context: Context dictionary (unused)
        
        Returns:
            Dictionary of GPU metrics
        """
        res: Dict[str, float] = {}
        total_util = 0.0
        gpu_count = 0
        
        # Collect metrics from all handlers
        for handler in self.gpu_handlers:
            handler_metrics = handler.read_metrics()
            res.update(handler_metrics)
            
            # Sum up utilization for total calculation
            for key, value in handler_metrics.items():
                if "util %" in key and "Total" not in key:
                    total_util += value
                    gpu_count += 1
        
        # Add total GPU utilization if we have multiple GPUs
        if self.n_gpus > 1:
            combined: Dict[str, float] = {}
            if gpu_count > 0:
                combined[f"[{self.n_gpus}] Total GPU util %"] = total_util / gpu_count
            else:
                combined[f"[{self.n_gpus}] Total GPU util %"] = 0.0
            
            # Reorder to put total first
            for k, v in res.items():
                combined[k] = v
            return combined
        
        return res


@cubestat_metric("darwin")
class unified_gpu_metric_macos(gpu_metric):
    """Unified GPU metric for macOS."""
    
    def __init__(self) -> None:
        """Initialize the macOS GPU metric."""
        self.handler = MacOSGPUHandler()
        self.n_gpus = self.handler.get_gpu_count()
    
    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read macOS GPU metrics.
        
        Args:
            context: Context dictionary containing GPU data
        
        Returns:
            Dictionary of GPU metrics
        """
        res: Dict[str, float] = {}
        
        try:
            if "gpu" not in context or "idle_ratio" not in context["gpu"]:
                logger.warning("Missing GPU data in context")
                return res
            
            idle_ratio = context["gpu"]["idle_ratio"]
            res["GPU util %"] = 100.0 - 100.0 * idle_ratio
        except KeyError as e:
            logger.warning(f"Missing key in GPU data: {str(e)}")
        except Exception as e:
            logger.exception(f"Error reading macOS GPU metrics: {str(e)}")
        
        return res