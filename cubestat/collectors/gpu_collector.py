import logging
import subprocess
from abc import ABC, abstractmethod
from importlib.util import find_spec
from typing import Any, Dict, List

from cubestat.collectors.base_collector import BaseCollector
from cubestat.metrics_registry import collector_registry

# Setup logging
logger = logging.getLogger(__name__)


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
                    res[f"{prefix}_gpu_{i}_util"] = gpu_util
                    
                    # Protect against division by zero
                    if mem_total > 0:
                        res[f"{prefix}_gpu_{i}_vram_used_percent"] = 100.0 * mem_used / mem_total
                    else:
                        res[f"{prefix}_gpu_{i}_vram_used_percent"] = 0.0
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
                    res[f"{prefix}_gpu_{i}_util"] = float(gpu_util)
                    
                    # Protect against division by zero
                    if mem_total > 0:
                        res[f"{prefix}_gpu_{i}_vram_used_percent"] = 100.0 * mem_used / mem_total
                    else:
                        res[f"{prefix}_gpu_{i}_vram_used_percent"] = 0.0
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


class GPUCollector(BaseCollector):
    """Base GPU collector."""

    @classmethod
    def collector_id(cls) -> str:
        return "gpu"


@collector_registry.register("linux")
class LinuxGPUCollector(GPUCollector):
    """Linux GPU collector supporting multiple vendors (NVIDIA, AMD)."""

    def __init__(self):
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

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect GPU metrics from all available vendors."""
        result = {}
        total_util = 0.0
        gpu_count = 0
        
        # Collect metrics from all handlers
        for handler in self.gpu_handlers:
            handler_metrics = handler.read_metrics()
            result.update(handler_metrics)
            
            # Sum up utilization for total calculation
            for key, value in handler_metrics.items():
                if "_util" in key and "total" not in key.lower():
                    total_util += value
                    gpu_count += 1
        
        # Add metadata for presenter
        result["_n_gpus"] = self.n_gpus
        result["_total_util"] = total_util / gpu_count if gpu_count > 0 else 0.0
        
        return result


@collector_registry.register("darwin")
class MacOSGPUCollector(GPUCollector):
    """macOS GPU collector using system context data."""

    def __init__(self):
        self.n_gpus = 1  # macOS always reports 1 GPU

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect macOS GPU metrics from context."""
        result = {}
        
        try:
            if "gpu" not in context or "idle_ratio" not in context["gpu"]:
                logger.warning("Missing GPU data in context")
                return {"_n_gpus": 0}
            
            idle_ratio = context["gpu"]["idle_ratio"]
            result["gpu_util"] = 100.0 - 100.0 * idle_ratio
            result["_n_gpus"] = self.n_gpus
        except KeyError as e:
            logger.warning(f"Missing key in GPU data: {str(e)}")
            result["_n_gpus"] = 0
        except Exception as e:
            logger.exception(f"Error reading macOS GPU metrics: {str(e)}")
            result["_n_gpus"] = 0
        
        return result