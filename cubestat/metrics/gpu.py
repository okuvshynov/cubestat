import logging
import subprocess
from importlib.util import find_spec
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from cubestat.common import DisplayMode
from cubestat.metrics.base_metric import base_metric
from cubestat.metrics_registry import cubestat_metric


# Setup logging
logger = logging.getLogger(__name__)


class GPUMode(DisplayMode):
    collapsed = 'collapsed'
    load_only = 'load_only'
    load_and_vram = 'load_and_vram'


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
            return False, ''
        if self.mode == GPUMode.load_only and "vram" in title:
            return False, ''
        if self.n_gpus > 1 and "Total GPU" not in title:
            return True, '  '
        return True, ''

    def format(self, title: str, values: Sequence[float], idxs: Sequence[int]) -> Tuple[float, List[str]]:
        """Format GPU utilization values.
        
        Args:
            title: The metric title
            values: The metric values
            idxs: Indices to format
            
        Returns:
            Tuple of (max_value, formatted_values)
        """
        return 100.0, [f'{values[i]:3.0f}%' for i in idxs]

    def configure(self, conf: Any) -> 'gpu_metric':
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
        return 'gpu'

    def hotkey(self) -> str:
        """Return the hotkey used to toggle this metric's display mode."""
        return 'g'

    @classmethod
    def configure_argparse(cls, parser: Any) -> None:
        """Configure command line arguments for this metric.
        
        Args:
            parser: The argument parser to configure
        """
        parser.add_argument(
            '--gpu',
            type=GPUMode,
            default=GPUMode.load_only,
            choices=list(GPUMode),
            help='GPU mode - hidden, load, or load and vram usage. Hotkey: "g"'
        )


@cubestat_metric('linux')
class nvidia_gpu_metric(gpu_metric):
    has_nvidia: bool
    nvsmi: Optional[Any] = None
    
    def __init__(self) -> None:
        """Initialize the NVIDIA GPU metric."""
        self.has_nvidia = False
        self.n_gpus = 0
        try:
            subprocess.check_output(['nvidia-smi'], stderr=subprocess.PIPE)
            nvspec = find_spec('pynvml')
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
            logger.warning(f"nvidia-smi command failed: {e.stderr.decode() if e.stderr else 'unknown error'}")
        except FileNotFoundError:
            logger.warning("nvidia-smi not found, NVIDIA GPU monitoring disabled")
        except Exception as e:
            logger.exception(f"Unexpected error initializing NVIDIA GPU metrics: {str(e)}")

    def read(self, _context: Dict[str, Any]) -> Dict[str, float]:
        """Read NVIDIA GPU metrics.
        
        Args:
            _context: Context dictionary (unused)
            
        Returns:
            Dictionary of GPU metrics
        """
        res: Dict[str, float] = {}
        total = 0.0
        
        if not self.has_nvidia or self.nvsmi is None:
            return res
            
        try:
            self.n_gpus = 0
            query_result = self.nvsmi.DeviceQuery('utilization.gpu,memory.total,memory.used')
            
            if not query_result or 'gpu' not in query_result:
                logger.warning("Invalid DeviceQuery result from NVIDIA SMI")
                return res
                
            for i, v in enumerate(query_result['gpu']):
                try:
                    gpu_util = v['utilization']['gpu_util']
                    mem_used = v['fb_memory_usage']['used']
                    mem_total = v['fb_memory_usage']['total']
                    
                    res[f'GPU {i} util %'] = gpu_util
                    total += gpu_util
                    
                    # Protect against division by zero
                    if mem_total > 0:
                        res[f'GPU {i} vram used %'] = 100.0 * mem_used / mem_total
                    else:
                        res[f'GPU {i} vram used %'] = 0.0
                        logger.warning(f"GPU {i} reports zero total memory")
                        
                    self.n_gpus += 1
                except KeyError as e:
                    logger.warning(f"Missing key in GPU {i} data: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error processing GPU {i} data: {str(e)}")
                    
            if self.n_gpus > 1:
                combined: Dict[str, float] = {}
                # Protect against division by zero
                if self.n_gpus > 0:
                    combined[f'[{self.n_gpus}] Total GPU util %'] = total / self.n_gpus
                else:
                    combined[f'[0] Total GPU util %'] = 0.0
                    
                for k, v in res.items():
                    combined[k] = v
                return combined
        except Exception as e:
            logger.exception(f"Error reading NVIDIA GPU metrics: {str(e)}")
            self.n_gpus = 0
            
        return res


@cubestat_metric('darwin')
class macos_gpu_metric(gpu_metric):
    def __init__(self) -> None:
        """Initialize the macOS GPU metric."""
        self.n_gpus = 1
    
    def read(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Read macOS GPU metrics.
        
        Args:
            context: Context dictionary containing GPU data
            
        Returns:
            Dictionary of GPU metrics
        """
        res: Dict[str, float] = {}
        
        try:
            if 'gpu' not in context or 'idle_ratio' not in context['gpu']:
                logger.warning("Missing GPU data in context")
                return res
                
            idle_ratio = context['gpu']['idle_ratio']
            res['GPU util %'] = 100.0 - 100.0 * idle_ratio
        except KeyError as e:
            logger.warning(f"Missing key in GPU data: {str(e)}")
        except Exception as e:
            logger.exception(f"Error reading macOS GPU metrics: {str(e)}")
            
        return res
